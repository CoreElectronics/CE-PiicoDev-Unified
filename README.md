# Core Electronics Unified PiicoDev Library
*Unifies the I2C drivers for different implementations of MicroPython*

## Adding the Unified I2C api to your sensor library api
To add the unified I2C to your sensor library api add a named i2c paramter to the __init__ method.
    
For example:
```
# don't create a global i2c here, creates issues trying to pass in a user created i2c
class PiicoDev_VL53L1X:

    def __init__(self, address=0x29, i2c=None):
        if i2c is not None:
            print("Using supplied i2c")
            self.i2c = i2c
        else:
            self.i2c = create_unified_i2c()
```
This means that the user in most cases does not need to 
worry about the I2C settings if the wish to connect the 
sensor to the default scl or sda pins of the microcontroller.

# Documentation to add to PiicoDev_VL53L1X
## User Examples

### User example of defaults for Raspberry Pi Pico and the BBC micro:bit - same user code for both
Raspberry Pi Pico defaults
* sda pin 8
* scl pin 9

BBC micro:bit
* sda pin 20
* scl pin 19

```
from PiicoDev_VL53L1X import PiicoDev_VL53L1X
from utime import sleep_ms

laser = PiicoDev_VL53L1X()

while True:
    dist = laser.read() # read the distance in millimetres
    print("{:4d} | ".format(dist))
    sleep_ms(1000)
```
    
### Custom frequency for BBC micro:bit
```
from PiicoDev_VL53L1X import PiicoDev_VL53L1X
from utime import sleep_ms
from PiicoDev_Unified import create_unified_i2c

laser = PiicoDev_VL53L1X(i2c=create_unified_i2c(freq=400000))

while True:
    dist = laser.read() # read the distance in millimetres
    print("{:4d} | ".format(dist))
    sleep_ms(1000)
```

### Custom frequency, scl and sda pins for the Raspberry Pi Pico:
```
from PiicoDev_VL53L1X import PiicoDev_VL53L1X
from utime import sleep_ms
from machine import Pin
from PiicoDev_Unified import create_unified_i2c

i2cmod=create_unified_i2c(freq=400000, sda=Pin(0), scl=Pin(1))
laser = PiicoDev_VL53L1X(i2c=i2cmod)

while True:
    dist = laser.read() # read the distance in millimetres
    print("{:4d} | ".format(dist))
    sleep_ms(1000)    
    
``` 