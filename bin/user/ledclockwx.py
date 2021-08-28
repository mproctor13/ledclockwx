#!/usr/bin/env python
"""
ledclockwx
"""
import os
import time
import syslog
import weewx
import weeutil
import configobj
import json
import ast
try:
    from weeutil.config import merge_config
except ImportError:
    from weecfg import merge_config # pre WeeWX 3.9

from weewx.engine import StdEngine, StdService
try:
    from urllib.parse import urlparse, urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError


DRIVER_VERSION = "0.01"

def logmsg(level, msg):
    syslog.syslog(level, 'ledclock: %s' % msg)

def logdbg(msg):
    logmsg(syslog.LOG_DEBUG, msg)

def loginf(msg):
    logmsg(syslog.LOG_INFO, msg)

def logerr(msg):
    logmsg(syslog.LOG_ERR, msg)

def surely_a_list(innie):
    if isinstance(innie, list):
        return innie
    if innie is None or innie is "":
        return []
    return [innie] # cross fingers

class LedClockwx(StdService):

    def __init__(self, engine, config_dict):
      # Initialize my superclass first:
      super(LedClockwx, self).__init__(engine, config_dict)
      self.ledclock_dict = config_dict.get('LedClockwx', {})
      loginf('ledclockwx configuration %s' % self.ledclock_dict)

      self.url = self.ledclock_dict.get('url', 'http://localhost/state')

      self.default_units = self.ledclock_dict.get('usUnits', 'US').upper()
      self.default_units = weewx.units.unit_constants[self.default_units]

      self.temperatureKeys = surely_a_list(self.ledclock_dict.get('temperatureKeys', 'inTemp'))
      self.temperature_must_have = surely_a_list(self.ledclock_dict.get('temperature_must_have', []))

      # The conversion from station pressure to MSL barometric pressure depends on the
      # temperature. So, the default is to only provide the pressure value when there
      # is already an outdoor temperature value
      self.pressureKeys = surely_a_list(self.ledclock_dict.get('pressureKeys', 'pressure'))
      self.pressure_must_have = surely_a_list(self.ledclock_dict.get('pressure_must_have', ['inTemp']))

      self.humidityKeys = surely_a_list(self.ledclock_dict.get('humidityKeys', 'inHumidity'))
      self.humidity_must_have = surely_a_list(self.ledclock_dict.get('humidity_must_have', []))

      self.luxKeys = surely_a_list(self.ledclock_dict.get('luxKeys', 'inLux'))
      self.openKeys = surely_a_list(self.ledclock_dict.get('openKeys', 'open'))

      loginf('fallback default units: %s' % weewx.units.unit_nicknames[self.default_units])

      # This is last to make sure all the other stuff is ready to go
      # (avoid race condition)
      self.bind(weewx.NEW_LOOP_PACKET, self.new_loop_packet)

    def new_loop_packet(self, event):

        packet = event.packet

        f = urlopen(self.url)
        ledclockdata = f.read().decode('utf-8')

        loginf('ledclock data %s' % ledclockdata)

        if ledclockdata is None:
            return

        try:
            json_data = json.loads(ledclockdata)
        except ValueError:
            json_data = ast.literal_eval(ledclockdata)
        # If there is a declared set of units already, we'll convert to that.
        # If there isn't, we'll accept the configured wisdom.
        if 'usUnits' in packet:
            converter = weewx.units.StdUnitConverters[packet['usUnits']]
        else:
            converter = weewx.units.StdUnitConverters[self.default_units]

        for key in self.luxKeys:
            packet[key] = float(json_data['lux'])

        for key in self.openKeys:
            packet[key] = weeutil.weeutil.to_bool(json_data['closed'])

        if all(must_have in packet for must_have in self.temperature_must_have):
            temperatureC = (int(json_data['temperature']), 'degree_F', 'group_temperature')
            converted = converter.convert(temperatureC)
            for key in self.temperatureKeys:
                packet[key] = converted[0]

        if all(must_have in packet for must_have in self.pressure_must_have):
            pressurePA = (float(json_data['pressure']), 'inHg', 'group_pressure')
            converted = converter.convert(pressurePA)
            for key in self.pressureKeys:
                packet[key] = converted[0]

        if all(must_have in packet for must_have in self.humidity_must_have):
            raw_humidity = float(json_data['humidity'])
            if raw_humidity <= 1:
                raw_humidity = raw_humidity * 1000
            humidityPCT = (raw_humidity, 'percent', 'group_percent')
            converted = converter.convert(humidityPCT)
            for key in self.humidityKeys:
                packet[key] = converted[0]

        logdbg(packet)
if __name__ == '__main__':
    usage = """%prog [options] [--debug] [--help]"""

    def main():
        import optparse
        config_file = '/etc/weewx/weewx.conf'
        debug = False

        parser = optparse.OptionParser(usage=usage)
        parser.add_option('--config', dest='config_file', type=str, metavar="FILE",
                          help="Use configuration file FILE. Default is /etc/weewx/weewx.conf or /home/weewx/weewx.conf")
        parser.add_option('--version', dest='version', action='store_true',
                          help='display driver version')
        parser.add_option('--debug', dest='debug', action='store_true',
                          help='display diagnostic information while running')
        parser.add_option("--url", dest="url", type=str, metavar="url",
                          help="specify the interface, e.g., http://localhost:8080/state")
        (options, args) = parser.parse_args()

        if options.config_file:
            config_file = options.config_file

        if options.debug:
            debug = options.debug

        if options.version:
            print("ledclockwx version %s" % DRIVER_VERSION)
            exit(1)

        min_config_dict = {
            'debug': debug,
            'Station': {
                'altitude': [0, 'foot'],
                'latitude': 0,
                'station_type': 'Simulator',
                'longitude': 0
            },
            'Simulator': {
                'driver': 'weewx.drivers.simulator',
            },
            'Engine': {
                'Services': {}
            }
        }
        # print(min_config_dict)

        engine = StdEngine(min_config_dict)
        config_path = os.path.abspath(config_file)

        config_dict = configobj.ConfigObj(config_path, file_error=True)
        # print(config_dict['LedClockwx'])
        if options.url:
            config_dict['LedClockwx']['url'] = options.url
            print(options.url)
        weewx.accum.initialize(config_dict)

        service = LedClockwx(engine, config_dict)
        # units = weewx.units.unit_constants['usUnits']
        data = {}
        data['dateTime'] = time.time()
        data['usUnits'] = weewx.units.unit_constants['US']

        new_loop_packet_event = weewx.Event(weewx.NEW_LOOP_PACKET,
                                                    packet=data)
        engine.dispatchEvent(new_loop_packet_event)
        print("Loop packet is: %s %s"
                      % (weeutil.weeutil.timestamp_to_string(new_loop_packet_event.packet['dateTime']),
                         weeutil.weeutil.to_sorted_string(new_loop_packet_event.packet)))

        service.shutDown()

    def init_weewx():
        """ Perform the necessary WeeWX initialization. """
        min_config_dict = {
            'Station': {
                'altitude': [0, 'foot'],
                'latitude': 0,
                'station_type': 'Simulator',
                'longitude': 0
            },
            'Simulator': {
                'driver': 'weewx.drivers.simulator',
            },
            'Engine': {
                'Services': {}
            }
        }

        engine = StdEngine(min_config_dict)
        config_file = '/etc/weewx/weewx_service.conf'
        config_path = os.path.abspath(config_file)

        config_dict = configobj.ConfigObj(config_path, file_error=True)
        weewx.accum.initialize(config_dict)

        service = LedClockwx(engine, config_dict)
        # units = weewx.units.unit_constants['usUnits']
        data = {}
        data['dateTime'] = time.time()
        data['usUnits'] = weewx.units.unit_constants['US']

        new_loop_packet_event = weewx.Event(weewx.NEW_LOOP_PACKET,
                                                    packet=data)
        engine.dispatchEvent(new_loop_packet_event)
        print("Loop packet is: %s %s"
                      % (weeutil.weeutil.timestamp_to_string(new_loop_packet_event.packet['dateTime']),
                         weeutil.weeutil.to_sorted_string(new_loop_packet_event.packet)))

        service.shutDown()
if __name__ == '__main__':
    main()
