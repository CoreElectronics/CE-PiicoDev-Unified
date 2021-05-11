import microbit
from microbit import i2c
from I2CBase import I2CBase


class I2CUnifiedMicroBit(I2CBase):
    """An implementation of I2CBase for the BBC micro:bit
       The micro:bit does not have implementations of writeto_mem or readfrom_mem
       and so implements these as calls to write and read"""

    def writeto_mem(self, addr, memaddr, buf, *, addrsize=8):
        # micro:bit does not contain a writeto_mem function
        # implementing in terms of the provided microbit.i2c.write
        ad = memaddr.to_bytes(addrsize // 8, 'big')  # pad address for eg. 16 bit
        self.write(addr, ad + buf)

    def readfrom_mem(self, addr, memaddr, nbytes, *, addrsize=8):
        # micro:bit does not contain a readfrom_mem function
        # implementing in terms of the provided microbit.i2c.read
        ad = memaddr.to_bytes(addrsize // 8, 'big')  # pad address for eg. 16 bit
        self.write(addr, ad)
        return self.read(addr, nbytes)

    def write(self, addr, buf, stop=True):
        repeat = not stop
        i2c.write(addr, buf, repeat)

    def read(self, addr, nbytes, stop=True):
        repeat = not stop
        return i2c.read(addr, nbytes, repeat)

    def __init__(self, bus=0, freq=None, sda=None, scl=None):
        """
        Parameters
        ----------
        bus : int
            The micro:bit has a single I2C bus 
            and this value is ignored
        freq : int, optional
            frequency of data bit transfer in bits per second    
            example 400000    
        sda : enum
            While the micro:bit documentation suggests that the sda 
            pin can be changed, in practice it does not like it
            so this value is ignored
            sda is pin20 on the micro:bit
        scl : enum
            While the micro:bit documentation suggests that the scl 
            pin can be changed, in practice it does not like it
            so this value is ignored
            scl is pin19 on the micro:bit
        """
        if freq is not None:
            print("Initialising I2C freq to {}".format(freq))
            microbit.i2c.init(freq=freq)