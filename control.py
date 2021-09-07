import json
import websocket
import datetime
import numpy as np

class TemperatureController:
    '''
    Class to control a Bluefors temperature controller system. Currently written
    for compatibility with an LD-400 system, although it may be compatible with
    other models of Bluefors fridges.
    '''
    def __init__(self, ip_address):
        '''
        Constructor. Queries all heaters and thermometer channels at startup
        to obtain names and diagnostic information.

        Parameters
        ----------
        ip_address : str
            IP address of temperature controller device
        '''
        self.ip_address = ip_address #'192.168.1.204'
        self.heaters_info = {}
        self.thermometers_info = {}

        # get info on heaters
        ws = websocket.create_connection('ws://{}:5002/heater'.format(self.ip_address),
                                         timeout=10)
        for heater_chan in [1,2,3,4]:
            ws.send(json.dumps({'heater_nr': heater_chan}))
            resp = ws.recv()
            data = json.loads(resp)
            self.heaters_info[data['name']] = data
        ws.close()

        # get info on thermometers
        ws = websocket.create_connection('ws://{}:5002/channel'.format(self.ip_address),
                                         timeout=10)
        for heater_chan in [1,2,3,4,5,6,7,8]:
            ws.send(json.dumps({'channel_nr': heater_chan}))
            resp = ws.recv()
            data = json.loads(resp)
            self.thermometers_info[data['name']] = data
        ws.close()

    def get_data(self, channel):
        '''
        Get most recent data from the temperature controller.

        Parameters
        ----------
        channel : int or str
            Channel number or name for which to get data
        '''
        # parse arguments
        if type(channel) is int:
            channel_num = channel
        elif type(channel) is str:
            channel_num = self.thermometers_info[channel]['channel_nr']
        else:
            raise ValueError('Invalid argument type.')

        ws = websocket.create_connection('ws://{}:5002/channel/historical-data'.format(self.ip_address),
                                              timeout=10)
        ws.send(json.dumps({'channel_nr': channel_num,
                            'start_time': (datetime.datetime.now() - datetime.timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S'),
                            'stop_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'fields': ['timestamp', 'resistance', 'temperature']}))
        resp = ws.recv()
        data = json.loads(resp)

        # throw out data from all but the most recent measurement
        for field in ['timestamp', 'resistance', 'temperature']:
            data['measurements'][field] = data['measurements'][field][-1]

        ws.close()
        return data

    def set_heater(self, channel, active=None, pid_mode=None, power=None,
                   max_power=None, setpoint=None,
                   control_algorithm_settings=None):
        '''
        Change the heater settings.

        Parameters
        ----------
        channel : int or str
            Channel number or name for which to get data
        active : bool
            Set whether heater is active
        pid_mode : int
            0 : manual mode
            1 : PID mode
        power : float
            Manual power to apply, in Watts
        max_power : float
            Max power to apply, useful during PID regulation, in Watts
        setpoint : float
            PID setpoint in units of Kelvin (?)
        control_algorithm_settings : dict
            Proportional, integral, and derivative terms for the PID
            controller. Be sure to read the Bluefors docs when setting this!
            The argument must be of the form:

            {'proportional': 0.04
             'integral': 150
             'derivative': 0}
             
            where the values above should be reasonable for regulating between
            20 and 100mK.
        '''
        # parse arguments
        args_dict = locals()

        if type(channel) is int:
            channel_num = channel
        elif type(channel) is str:
            channel_num = self.heaters_info[channel]['heater_nr']
        else:
            raise ValueError('Invalid argument type.')

        settings_dict = {'heater_nr': channel_num}
        args_dict.pop('self')
        args_dict.pop('channel')
        for arg in args_dict:
            if arg != "channel" and args_dict[arg] is not None:
                settings_dict[arg] = args_dict[arg]
        
        ws = websocket.create_connection('ws://{}:5002/heater/update'.format(self.ip_address),
                                         timeout=10)
        ws.send(json.dumps(settings_dict))
        ws.close()