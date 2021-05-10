"""
PiicoDev.py: Unifies I2C drivers for different builds of micropython
"""

import os
_SYSNAME = os.uname().sysname

def sleep_ms2s(t): # RPi SBC only has sleep[sec]
    sleep(t/1000)

# Run correct imports for different micropython ports
if _SYSNAME == 'microbit':
    from microbit import i2c
    
elif _SYSNAME == 'Linux': # For Raspberry Pi SBC
    from smbus2 import SMBus
    from time import sleep
    i2c = SMBus(1)
    sleep_ms = sleep_ms2s
    
else: # Vanilla machine implementation
    from machine import I2C
    i2c = I2C(0)
    

class PiicoDev_Unified_I2C(object):
    
    # Implement machine library's Memory operations as standard bus operations (microbit-friendly)
    def writeto_mem(self, addr, memaddr, buf, *, addrsize=8):
        ad = memaddr.to_bytes(addrsize//8,'big') # pad address for eg. 16 bit
        self.UnifiedWrite(addr, ad+buf)
        
    def readfrom_mem(self, addr, memaddr, nbytes, *, addrsize=8):
        ad = memaddr.to_bytes(addrsize//8,'big') # pad address for eg. 16 bit
        self.UnifiedWrite(addr, ad) # address pointer
        return self.UnifiedRead(addr, nbytes)
    
    def UnifiedWrite(self, addr, buf, stop=True):
        if _SYSNAME == 'microbit':
            repeat = not(stop)
            self.i2c.write(addr, buf, repeat)
        else:
            self.i2c.writeto(addr, buf, stop)
    
    def write8(self, addr, reg, data):
        if _SYSNAME == 'Linux':
            r = int.from_bytes(reg, 'big')
            d = int.from_bytes(data, 'big')
            self.i2c.write_byte_data(addr, r, d)
        else:
            self.UnifiedWrite(addr, reg + data)
            
            
    def read16(self, addr, reg):
        if _SYSNAME == 'Linux':
            regInt = int.from_bytes(reg, 'big')
            return self.i2c.read_word_data(addr, regInt).to_bytes(2, byteorder='little', signed=False)
        else:
            self.UnifiedWrite(addr, reg, stop=False)
            return self.UnifiedRead(addr, 2)
    
    def UnifiedRead(self, addr, nbytes, stop=True):
        if _SYSNAME == 'microbit':
            repeat = not(stop)
            return self.i2c.read(addr, nbytes, repeat)
            
        else:
            return self.i2c.readfrom(addr, nbytes, stop)
    
    def __init__(self):
        self.i2c = i2c
        
        if _SYSNAME == 'microbit':
            self.sysPort = 'microbit'
        
        elif _SYSNAME == 'Linux':
            self.sysPort = 'linux'
        
        else:
            self.sysPort = 'machine'
            self.writeto_mem = i2c.writeto_mem # use machine's built-ins
            self.readfrom_mem = i2c.readfrom_mem
