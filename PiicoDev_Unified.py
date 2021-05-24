"""
PiicoDev.py: Unifies I2C drivers for different builds of micropython
"""

import os
_SYSNAME = os.uname().sysname

# Run correct imports for different micropython ports
if _SYSNAME == 'microbit':
    from microbit import i2c
    from utime import sleep_ms
    
elif _SYSNAME == 'Linux': # For Raspberry Pi SBC
    from smbus2 import SMBus, i2c_msg
    from time import sleep
    from math import ceil
    i2c = SMBus(1)
    
    def sleep_ms(t):
        sleep(t/1000)
    
else: # Vanilla machine implementation
    from machine import I2C
    from utime import sleep_ms
    i2c = I2C(0)
   

class PiicoDev_Unified_I2C(object):
    def smbus_i2c_write(self, address, reg, data_p, length, addrsize=8):
            ret_val = 0
            data = []
            for index in range(length):
                data.append(data_p[index])
            if addrsize == 8:
                msg_w = i2c_msg.write(address, [reg] + data)
            elif addrsize == 16:
                msg_w = i2c_msg.write(address, [reg >> 8, reg & 0xff] + data)
            else:
                raise Exception("address must be 8 or 16 bits long only")
            self.i2c.i2c_rdwr(msg_w)
            return ret_val
    
    def smbus_i2c_read(self, address, reg, data_p, length, addrsize=8):
            ret_val = 0
            if addrsize == 8:
                msg_w = i2c_msg.write(address, [reg]) # warning this is set up for 16-bit addresses
            elif addrsize == 16:
                msg_w = i2c_msg.write(address, [reg >> 8, reg & 0xff]) # warning this is set up for 16-bit addresses
            else:
                raise Exception("address must be 8 or 16 bits long only")
            msg_r = i2c_msg.read(address, length)
            self.i2c.i2c_rdwr(msg_w, msg_r)
            if ret_val == 0:
                for index in range(length):
                    data_p[index] = ord(msg_r.buf[index])
            return ret_val
        
    # Implement machine library's Memory operations as standard bus operations (microbit-friendly)
    def writeto_mem(self, addr, memaddr, buf, *, addrsize=8):
        if _SYSNAME == 'Linux':
            self.smbus_i2c_write(addr, memaddr, buf, len(buf), addrsize=addrsize)
        else:
            ad = memaddr.to_bytes(addrsize//8,'big') # pad address for eg. 16 bit
            self.UnifiedWrite(addr, ad+buf)
        
    def readfrom_mem(self, addr, memaddr, nbytes, *, addrsize=8):
        if _SYSNAME == 'Linux':
            data = [None] * nbytes # initialise empty list
            self.smbus_i2c_read(addr, memaddr, data, nbytes, addrsize=addrsize)
            return data
        else:
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
        if reg is None:
            if _SYSNAME == 'Linux':
                d = int.from_bytes(data, 'big')
                self.i2c.write_byte(addr, d)
            else:
                self.UnifiedWrite(addr, data)
        else:
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
        
        elif _SYSNAME == 'Linux':
            raise Exception('Unified write not compatible with Linux systems')
            
        else:
            return self.i2c.readfrom(addr, nbytes, stop)
    
    def __init__(self):
        self.i2c = i2c
        if _SYSNAME == 'microbit':
            self.sysPort = 'microbit'
            self.writeto_mem = self.writeto_mem
            self.readfrom_mem = self.readfrom_mem
       
        elif _SYSNAME == 'Linux':
            self.sysPort = 'linux'
        
        else:
            self.sysPort = 'machine'
            self.writeto_mem = i2c.writeto_mem # use machine's built-ins
            self.readfrom_mem = i2c.readfrom_mem
