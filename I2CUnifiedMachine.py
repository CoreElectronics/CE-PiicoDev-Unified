from machine import I2C
from I2CBase import I2CBase

class I2CUnifiedMachine(I2CBase):
    """An implementation of I2CBase for boards such as 
       Raspberry Pi Pico and others
       All calls are handed off to the machine.ic2
    """
    def __init__(self, bus=0, freq=None, sda=None, scl=None):
        """
        Parameters
        ----------
        bus : int
            Some boards have more than one bus
            example: 0
        freq : int
            frequency of data bit transfer in bits per second
            example: 400000    
        sda : enum
            Some boards allow the data (sda) pin to be changed
            value is dependent on the board
            example: Pin(8)
        scl : enum
            Some boards allow the clock (scl) pin to be changed
            value is dependent on the board
            example: Pin(9)
        """
        if freq is not None and sda is not None and scl is not None:
            print("Using supplied freq, sda and scl to create machine I2C")
            self.i2c = I2C(bus, freq=freq, sda=sda, scl=scl)
        else: 
            print("Using default machine I2C")
            self.i2c = I2C(bus)

        self.writeto_mem = self.i2c.writeto_mem 
        self.readfrom_mem = self.i2c.readfrom_mem   
        self.write = self.i2c.writeto
        self.read = self.i2c.readfrom
