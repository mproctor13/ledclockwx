# [ledclockwx](https://github.com/mproctor13/ledclockwx)
_Copyright (c) 2021, Michael Proctor-Smith based on bme280wx(https://gitlab.com/wjcarpenter/bme280wx/blob/master/LICENSE) by WJCarpenter_
_[This project is licensed under the BSD 2-clause "Simplified" License.](https://github.com/mproctor13/ledclockwx/blob/master/LICENSE)_

ledclockwx is an extension to [weewx weather station software](https://weewx.com).
It gives the ability to suplement existing station readings with temperature,
pressure, and humidity readings from json provided by
[ledclock](https://github.com/mproctor13/ledclockwx).

## Installation
### Pre-requisites
* [weewx](https://weewx.com). Should work with any recent version. Tested with weewx 3.9.1 and 4.1.0.
* python 2.7 or python 3.x. You will already have a suitable python version if you are running weewx.

Download the compressed archive https://github.com/mproctor13/ledclockwx/archive/refs/heads/master.zip of this project to any convenient temporary directory.

Run the extensions installer:
```
wee_extension --install master.zip
```
Restart weewx using these steps or your favorite local variant:
```
sudo /etc/init.d/weewx stop
sudo /etc/init.d/weewx start
```
It's OK to delete the downloaded file after installation.
You will not need it for uninstalling the extension, but, of course, you will need it to re-install.

## Uninstall

To uninstall this extension, use the extensions installer:
```
wee_extension --uninstall ledclockwx
```
Restart weewx using these steps or your favorite local variant:
```
sudo /etc/init.d/weewx stop
sudo /etc/init.d/weewx start
```
## Upgrade
If you want to upgrade to a newer version of this extension,
simply uninstall the old version and install the new version, as noted above.
However, during the uninstall, the extension manager will remove the configuration settings (described in the next section).
If you have modified any of them, make a note of them before the uninstall.
(One easy way to do that is to simply rename the `[LedClockwx]` section to something else.
That will prevent the extension manager from removing the whole section.)

## Configuration
Installation will add a default configuration to `/etc/weewx/weewx.conf`:
```
# Options for extension 'ledclockwx'
[LedClockwx]
    url = file://example.json
    usUnits = US
    temperatureKeys = clockTemp
    temperature_must_have = ""
    pressureKeys = pressure
    pressure_must_have = clockTemp
    humidityKeys = clockHumidity
    humidity_must_have = ""
    pressure_must_have = "clockTemp"
    luxKeys = clockLux
    openKeys = clockOpen
```
The configuration items have the following meanings:

* `url`: The url to download json from.
* `usUnits`: Ordinarily, a weewx loop data packet will contain a `usUnits` key identifying the units system for the values in the packet.
  The ledclock data will be converted to that units system before being added to the packet.
  It is possible that the loop data packet will not have the `usUnits` key.
  In that case, the ledclock data will be converted to the units system from this configuration item.
  Allowed values are `US` (the default), `METRIC`, or `METRICWX`,
  which are the units systems understood by weewx.
  A `usUnits` key with this value will _not_ be added to the weewx loop data packet.
* `temperatureKeys`: When the ledclock temperature data is added to weewx loop data packets, it will use this key or keys.
  If you don't want to use this ledclock value, set this to empty string (`""`).
  The value can be an empty string (meaning, do not add at all), a single item, or a comma-separated list of items.
  If multiple keys are configured, the same value is used with each key.
  The default is `clockTemp` under the assumption that your Raspberry Pi is running indoors.
* `temperature_must_have`: The ledclock temperature will only be added to the weewx loop data packet if these items are already present in the packet.
  The value can be an empty string (meaning, no requirements), a single item, or a comma-separated list of items.
  The default is empty string.
* `pressureKeys`: When the ledclock pressure data is added to weewx loop data packets, it will use this key or keys.
  If you don't want to use this ledclock value, set this to empty string (`""`).
  The value can be an empty string (meaning, do not add at all), a single item, or a comma-separated list of items.
  If multiple keys are configured, the same value is used with each key.
  The default is `pressure`. Do _not_ use `barometer`.
  _This is "station pressure". The weewx software will calculate the MSL "barometric pressure" from this.
  That calculation depends upon the ambient temperature and the altitude._
  **Check to make sure that your weewx configuration reflects the altitude of your ledclock sensor, not that of other sensors you may have.**
* `pressure_must_have`: The ledclock pressure will only be added to the weewx loop data packet if these items are already present in the packet.
  The value can be an empty string (meaning, no requirements), a single item, or a comma-separated list of items.
  The default is `outTemp` because the calculation of MSL barometric pressure depends upon the ambient temperature.
  Although the pressure inside will be the same as the pressure outside, the temperature probably will not be.
* `humidityKeys`: When the ledclock humidity data is added to weewx loop data packets, it will use this key or keys.
  If you don't want to use this ledclock value, set this to empty string (`""`).
  The value can be an empty string (meaning, do not add at all), a single item, or a comma-separated list of items.
  If multiple keys are configured, the same value is used with each key.
  The default is `inHumidity`.
* `humidity_must_have`: The ledclock humidity will only be added to the weewx loop data packet if these items are already present in the packet.
  The value can be an empty string (meaning, no requirements), a single item, or a comma-separated list of items.
  The default is empty string.

After making any configuration changes, you must restart weewx.
Be sure to also have a look at the system log to see that weewx started properly.
Mistakes in configuration can lead to unrecoverable errors that prompt weewx to shut down.
