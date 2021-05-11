class I2CBase:
    """The interface for the unified I2C library.
       Allows sensor libraries to abstract away 
       the differing I2C library apis for each microcontroller
       Ideally only add methods that can be supported on all platforms directly
       or by translating to other method calls that do exist
    """
    
    def writeto_mem(self, addr, memaddr, buf, *, addrsize=8):
        raise NotImplementedError("writeto_mem")

    def readfrom_mem(self, addr, memaddr, nbytes, *, addrsize=8):
        raise NotImplementedError("readfrom_mem")

    def write(self, addr, buf, stop=True):
        raise NotImplementedError("write")

    def read(self, addr, nbytes, stop=True):
        raise NotImplementedError("read")

    def __init__(self, bus=0, freq=None, sda=None, scl=None):
        raise NotImplementedError("__init__")
