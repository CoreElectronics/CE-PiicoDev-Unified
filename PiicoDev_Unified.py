"""
PiicoDev.py: Unifies I2C drivers for different builds of micropython
"""

import os

def create_unified_i2c(bus=0, freq=None, sda=None, scl=None):
    """The parameters passed are to override the defaults
    only supply parameters if you wish to override the defaults 
    for your board.
    See the implementations such as I2CUnifiedMachine or 
    I2CUnifiedMicroBit for more details on what can be changed.

    To add a unified I2C to your sensor library, add a named 
    i2c paramter to the __init__ method.
    For example:
        def __init__(self, address=0x29, i2c=None):
            if i2c is not None:
                print("Using supplied i2c")
                self.i2c = i2c
            else:
                self.i2c = create_unified_i2c()

    This means that the user in most cases does not need to 
    worry about the I2C settings if the wish to connect the 
    sensor to the default scl or sda pins of the microcontroller.
    For example for the Raspberry Pi Pico and the BBC micro:bit:

    from PiicoDev_VL53L1X import PiicoDev_VL53L1X

    laser = PiicoDev_VL53L1X()

    Those users that want to change the pins can instead make a 
    call to create_unified_i2c themselves and pass that in
    to the sensor api constructor.
    For example for the Raspberry Pi Pico:

    from PiicoDev_VL53L1X import PiicoDev_VL53L1X

    laser = PiicoDev_VL53L1X(i2c=create_unified_i2c(freq=400000, sda=Pin(0), scl=Pin(1)))
    """
    _SYSNAME = os.uname().sysname
    if _SYSNAME == 'microbit':
        from I2CUnifiedMicroBit import I2CUnifiedMicroBit
        i2c = I2CUnifiedMicroBit(bus, freq, sda, scl)
    else:
        from I2CUnifiedMachine import I2CUnifiedMachine
        i2c = I2CUnifiedMachine(bus, freq, sda, scl)
    return i2c
