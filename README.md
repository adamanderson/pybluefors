# pybluefors

## Usage
Instantiate a client:
```
from pybluefors.control import TemperatureController
tc = TemperatureController('192.168.1.204')
```
Get data for a specific channel:
```
data = tc.get_data("MXC-flange")
```
Update a heater:
```
tc.set_heater(channel='MXC-heater', active=True, power=20e-6)
```
Turn on the PID controller:
```
tc.set_heater(channel='MXC-heater',
              active=True,
              pid_mode=1,
              setpoint=0.03,
              control_algorithm_settings = {'proportional': 0.04
                                            'integral': 150
                                            'derivative': 0})
```