import io
import base64
from bisect import bisect
from struct import pack, unpack

def encode_ir(signal: list[int], compression_level=2) -> str:
	'''
	Encodes an IR signal (see `decode_tuya_ir`)
	into an IR code string for a Tuya blaster.
	'''
	payload = b''.join(pack('<H', t) for t in signal)
	compress(out := io.BytesIO(), payload, compression_level)
	payload = out.getvalue()
	return base64.encodebytes(payload).decode('ascii').replace('\n', '')
	
# COMPRESSION

def emit_literal_blocks(out: io.FileIO, data: bytes):
    for i in range(0, len(data), 32):
	    emit_literal_block(out, data[i:i+32])

def emit_literal_block(out: io.FileIO, data: bytes):
    length = len(data) - 1
    assert 0 <= length < (1 << 5)
    out.write(bytes([length]))
    out.write(data)

def emit_distance_block(out: io.FileIO, length: int, distance: int):
	distance -= 1
	assert 0 <= distance < (1 << 13)
	length -= 2
	assert length > 0
	block = bytearray()
	if length >= 7:
		assert length - 7 < (1 << 8)
		block.append(length - 7)
		length = 7
	block.insert(0, length << 5 | distance >> 8)
	block.append(distance & 0xFF)
	out.write(block)

def compress(out: io.FileIO, data: bytes, level=2):
	'''
	Takes a byte string and outputs a compressed "Tuya stream".
	Implemented compression levels:
	0 - copy over (no compression, 3.1% overhead)
	1 - eagerly use first length-distance pair found (linear)
	2 - eagerly use best length-distance pair found
	3 - optimal compression (n^3)
	'''
	if level == 0:
		return emit_literal_blocks(out, data)

	W = 2**13 # window size
	L = 255+9 # maximum length
	distance_candidates = lambda: range(1, min(pos, W) + 1)

	def find_length_for_distance(start: int) -> int:
		length = 0
		limit = min(L, len(data) - pos)
		while length < limit and data[pos + length] == data[start + length]:
			length += 1
		return length
		
	find_length_candidates = lambda: \
		( (find_length_for_distance(pos - d), d) for d in distance_candidates() )
	find_length_cheap = lambda: \
		next((c for c in find_length_candidates() if c[0] >= 3), None)
	find_length_max = lambda: \
		max(find_length_candidates(), key=lambda c: (c[0], -c[1]), default=None)

	if level >= 2:
		suffixes = []; next_pos = 0
		key = lambda n: data[n:]
		find_idx = lambda n: bisect(suffixes, key(n), key=key)
		def distance_candidates():
			nonlocal next_pos
			while next_pos <= pos:
				if len(suffixes) == W:
					suffixes.pop(find_idx(next_pos - W))
				suffixes.insert(idx := find_idx(next_pos), next_pos)
				next_pos += 1
			idxs = (idx+i for i in (+1,-1)) # try +1 first
			return (pos - suffixes[i] for i in idxs if 0 <= i < len(suffixes))

	if level <= 2:
		find_length = { 1: find_length_cheap, 2: find_length_max }[level]
		block_start = pos = 0
		while pos < len(data):
			if (c := find_length()) and c[0] >= 3:
				emit_literal_blocks(out, data[block_start:pos])
				emit_distance_block(out, c[0], c[1])
				pos += c[0]
				block_start = pos
			else:
				pos += 1
		emit_literal_blocks(out, data[block_start:pos])
		return

	# use topological sort to find shortest path
	predecessors = [(0, None, None)] + [None] * len(data)
	def put_edge(cost, length, distance):
		npos = pos + length
		cost += predecessors[pos][0]
		current = predecessors[npos]
		if not current or cost < current[0]:
			predecessors[npos] = cost, length, distance
	for pos in range(len(data)):
		if c := find_length_max():
			for l in range(3, c[0] + 1):
				put_edge(2 if l < 9 else 3, l, c[1])
		for l in range(1, min(32, len(data) - pos) + 1):
			put_edge(1 + l, l, 0)

	# reconstruct path, emit blocks
	blocks = []; pos = len(data)
	while pos > 0:
		_, length, distance = predecessors[pos]
		pos -= length
		blocks.append((pos, length, distance))
	for pos, length, distance in reversed(blocks):
		if not distance:
			emit_literal_block(out, data[pos:pos + length])
		else:
			emit_distance_block(out, length, distance)
#----------------------------------------------------------------------------

def calc_crc(byte_array: bytes):
    bit_reversal = []

    for i in byte_array:
      bit_reversal.append(int('{:08b}'.format(i)[::-1], 2))
      # Calculate checksum
      checksum = 2**8 - sum(bit_reversal) % 2**8
      # Return bits to original order
      res = int('{:08b}'.format(checksum)[::-1], 2)
      
    return res
    
def build_raw(header, one, zero, gap, bin):
    """
    Generates Raw from Lirc command, returns command as a list of integers.
    """
    def clean_string_seps(string, sep):
        """Cleans possible values separators and spaces in string to replace them with unique sep."""
        string = re.sub(r'[\s;\+\-]', ',', string)   # Replace spaces, ; + or - with ','
        string = re.sub(r'(,){2,}', ',', string)       # Replace multiple ',,,' with single ','
        string = string.replace(',', sep)             # Replace ',' with sep
        return string
        
    import re

    def parse_to_int_list(string):
        """Parses a cleaned string to a list of integers."""
        return list(map(int, string.split(','))) if string else []

    str_list = [parse_to_int_list(clean_string_seps(zero, ',')), parse_to_int_list(clean_string_seps(one, ','))]
    header = parse_to_int_list(clean_string_seps(header, ','))

    raw = []
    if header:
        raw.extend(header)

    for i in range(len(bin)):
        raw.extend(str_list[int(bin[i])])  # Pushes zero or one sequence

    if gap:
        raw.extend(parse_to_int_list(gap))  # Completes by pushing gap

    # print(f"{header}, [{bin}], {gap}")  # Equivalent to the info() function in JS

    return raw    

def hex_to_bin(byte_array: bytes):
    """
    Converts an array of bytes to a binary string with 16-bit zero-padding.
    Examples:
    - [0xA5] -> "0000000010100101"
    - [0xA5, 0x5A, 0xD9, 0x26, 0xF5, 0x0A] -> "101001010101101011011001001001101111010100001010"
    """
    bin_str = ""

    for byte in byte_array:
        bin_str += bin(byte)[2:].zfill(8)  # Convert each byte to binary, pad with zeros

    return bin_str
    
def negate_bytes(byte_array: bytes) -> bytes:
    """
    Returns a new array of bytes where each byte is the bitwise negation of the input byte.
    Examples:
    - [0xFF, 0x00] -> [0x00, 0xFF]
    - [0xA5, 0x5A] -> [0x5A, 0xA5]
    """
    return [~byte & 0xFF for byte in byte_array]
    
def get_temp_command(temperature: float) -> bytes:
    assert -30 <= temperature < 70
    # conversion to int 
    value = round(temperature)
	# data frame of FollowMe IR command
    byte_array = [0xA4,0x82,0x48,0x7F]
    byte_array.append(value + 1)
    crc = calc_crc(byte_array)
    # print(f"{crc:02X}")
    byte_array.append(crc)
    
    return byte_array
    
def encode_temperature(temperature: float) -> str:
    '''
    following declaration of timing variable to be used in next version of build_raw function
    TICK_US = 560
    HEADER_MARK_US = 8 * TICK_US
    HEADER_SPACE_US = 8 * TICK_US
    BIT_MARK_US = 1 * TICK_US
    BIT_ONE_SPACE_US = 3 * TICK_US
    BIT_ZERO_SPACE_US = 1 * TICK_US
    FOOTER_MARK_US = 1 * TICK_US
    FOOTER_SPACE_US = 10 * TICK_US
    '''
    command = get_temp_command(temperature)
    # command = [0xA4,0x82,0x48,0x7F,0x16] - 21 deg. of Celcius
    # Print as hex values separated by spaces
    # print(" ".join(f"{byte:02X}" for byte in command)) 
    binary = hex_to_bin(command)
    neg_command = negate_bytes(command)
    # print(" ".join(f"{byte:02X}" for byte in neg_command))
    neg_binary = hex_to_bin(neg_command)
    # print(neg_binary)
    
    # Example usage:
    command_raw = build_raw("4497, 4497", "588, 1657", "588, 588", "588,5601", binary)
    neg_command_raw = build_raw("4497, 4497", "588, 1657", "588, 588", "588,5601", neg_binary)
    # print(command_raw + neg_command_raw)
    
    return encode_ir(command_raw + neg_command_raw)

    
# test = encode_temperature(23.8)
# print(test)
