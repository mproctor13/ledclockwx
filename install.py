# installer for ledclockwx extension

from setup import ExtensionInstaller

def loader():
    return LedClockwxInstaller()

class LedClockwxInstaller(ExtensionInstaller):
    def __init__(self):
        super(LedClockwxInstaller, self).__init__(
            version=0.1,
            name='ledclockwx',
            description='Add ledclock sensor readings to loop packet data',
            author="Michael Proctor-Smith",
            author_email="mproctor13@gmail.com",
            data_services='user.ledclockwx.LedClockwx',
            config={
                'LedClockwx': {
                    'url': 'http://localhost/state',
                    'usUnits': 'US',
                    'temperatureKeys': 'clockTemp',
                    'temperature_must_have': '',
                    'pressureKeys': 'pressure',
                    'pressure_must_have': 'clockTemp',
                    'humidityKeys': 'clockHumidity',
                    'humidity_must_have': ''
                }
            },
            files=[('bin/user', ['bin/user/ledclockwx.py'])]
            )
