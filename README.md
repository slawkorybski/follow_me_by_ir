# FollowMe by IR
Home Assistant custom component to send temperature IR code using Zosung IR Blaster ZS06 (zigbee IR blaster) to Midea (and other compatible brands) air conditioners.
It uses FollowMe functionality which is widly use by many Midea's family AC devices like Rotenso etc.

IR code encoding functionality is heavly inspired on the project:
* @mildsunrise (https://gist.github.com/mildsunrise/1d576669b63a260d2cff35fda63ec0b5)


## Install Manually
1. Locate the `custom_components` directory in your Home Assistant configuration directory. It may need to be created.
2. Copy the `custom_components/follow_me_by_ir` directory into the `custom_components` directory.
3. Restart Home Assistant.

## Manual Configuration
Following an example of configuration which should be placed in sensors folder of Home Assistant configuration directory:

### Example configuration

```yaml
sensor:
  - platform: follow_me_by_ir
    name: FollowMe by IR
    scan_interval: 60
    ieee: "34:25:b4:ff:fe:32:69:15"
    temperature_entity_id: sensor.temperature_sensor_2_temperature
```

| Parameter | Description |
| --- | --- | 
| temperature_entity_id | is a entity_id of the temperature sensor |
| ieee | is a zigbee ieee of Zosung IR Blaster ZS06 (zigbee IR blaster) |
