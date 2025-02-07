# FollowMe by IR
Home Assistant custom component to send temperature IR code using Zosung IR Blaster ZS06 (zigbee IR blaster) to Midea (and other compatible brands) air conditioners.
It uses FollowMe functionality which is widly use by many Midea's family AC devices like Rotenso etc.

IR code encoding functionality is heavly inspired on the project:
* @mildsunrise (https://gist.github.com/mildsunrise/1d576669b63a260d2cff35fda63ec0b5)


## Install Manually
1. Locate the `custom_components` directory in your Home Assistant configuration directory. It may need to be created.
2. Copy the `custom_components/follow_me_by_ir` directory into the `custom_components` directory.
3. Restart Home Assistant.

## Configuration
FollowMe by IR is configured via the GUI. See the HA docs for more details.
Click the Add Integration button and search for "FollowMe by IR" integration.

### Example configuration

| Parameter | Description |
| --- | --- | 
| scan_interval | parameter defining the time interval with which the IR code is sent | 
| temperature_entity_id | is a entity_id of the temperature sensor |
| ir_blaster_ieee | is a zigbee ieee of Zosung IR Blaster ZS06 (zigbee IR blaster) device |
