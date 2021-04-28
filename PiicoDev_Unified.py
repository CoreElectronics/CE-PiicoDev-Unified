"""
PiicoDev.py: Unifies I2C drivers for different builds of micropython
"""

import os
_SYSNAME = os.uname().sysname

# Run correct imports for different micropython ports
if _SYSNAME == 'microbit':
    from microbit import i2c
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
    
    def __init__(self):
        self.i2c = i2c
        
        if _SYSNAME == 'microbit':
            self.sysPort = 'microbit'
            self.UnifiedWrite = i2c.write
            self.UnifiedRead = i2c.read
            self.writeto_mem = self.writeto_mem
            self.readfrom_mem = self.readfrom_mem
            
        else:
            self.sysPort = 'machine'
            self.UnifiedWrite = i2c.writeto
            self.UnifiedRead = i2c.readfrom
            self.writeto_mem = i2c.writeto_mem # use machine's built-ins
            self.readfrom_mem = i2c.readfrom_mem
