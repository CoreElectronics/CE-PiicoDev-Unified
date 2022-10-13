'\nPiicoDev.py: Unifies I2C drivers for different builds of MicroPython\n'
_F='address must be 8 or 16 bits long only'
_E='microbit'
_D=False
_C='big'
_B=True
_A=None
import os
_SYSNAME=os.uname().sysname
compat_ind=1
i2c_err_str='PiicoDev could not communicate with module at address 0x{:02X}, check wiring'
setupi2c_str=', run "sudo curl -L https://piico.dev/i2csetup | bash". Suppress this warning by setting suppress_warnings=True'
if _SYSNAME==_E:from microbit import i2c;from utime import sleep_ms
elif _SYSNAME=='Linux':
	from smbus2 import SMBus,i2c_msg;from time import sleep;from math import ceil
	def sleep_ms(t):sleep(t/1000)
else:from machine import I2C;from utime import sleep_ms
class I2CBase:
	def writeto_mem(A,addr,memaddr,buf,*,addrsize=8):raise NotImplementedError('writeto_mem')
	def readfrom_mem(A,addr,memaddr,nbytes,*,addrsize=8):raise NotImplementedError('readfrom_mem')
	def write8(A,addr,buf,stop=_B):raise NotImplementedError('write')
	def read16(A,addr,nbytes,stop=_B):raise NotImplementedError('read')
	def __init__(A,bus=_A,freq=_A,sda=_A,scl=_A):raise NotImplementedError('__init__')
class I2CUnifiedMachine(I2CBase):
	def __init__(A,bus=_A,freq=_A,sda=_A,scl=_A):
		B=bus
		if B is _A:B=0
		if freq is not _A and sda is not _A and scl is not _A:print('Using supplied freq, sda and scl to create machine I2C');A.i2c=I2C(B,freq=freq,sda=sda,scl=scl)
		else:A.i2c=I2C(B)
		A.writeto_mem=A.i2c.writeto_mem;A.readfrom_mem=A.i2c.readfrom_mem
	def write8(A,addr,reg,data):
		if reg is _A:A.i2c.writeto(addr,data)
		else:A.i2c.writeto(addr,reg+data)
	def read16(A,addr,reg):A.i2c.writeto(addr,reg,_D);return A.i2c.readfrom(addr,2)
class I2CUnifiedMicroBit(I2CBase):
	def __init__(B,freq=_A):
		A=freq
		if A is not _A:print('Initialising I2C freq to {}'.format(A));microbit.i2c.init(freq=A)
	def writeto_mem(B,addr,memaddr,buf,*,addrsize=8):A=memaddr.to_bytes(addrsize//8,_C);i2c.write(addr,A+buf)
	def readfrom_mem(B,addr,memaddr,nbytes,*,addrsize=8):A=memaddr.to_bytes(addrsize//8,_C);i2c.write(addr,A,repeat=_B);return i2c.read(addr,nbytes)
	def write8(A,addr,reg,data):
		if reg is _A:i2c.write(addr,data)
		else:i2c.write(addr,reg+data)
	def read16(A,addr,reg):i2c.write(addr,reg,repeat=_B);return i2c.read(addr,2)
class I2CUnifiedLinux(I2CBase):
	def __init__(D,bus=_A,suppress_warnings=_B):
		C='/boot/config.txt';B=bus
		if suppress_warnings==_D:
			with open(C)as A:
				if'dtparam=i2c_arm=on'in A.read():0
				else:print('I2C is not enabled. To enable'+setupi2c_str)
				A.close()
			with open(C)as A:
				if'dtparam=i2c_arm_baudrate=400000'in A.read():0
				else:print('Slow baudrate detected. If glitching occurs'+setupi2c_str)
				A.close()
		if B is _A:B=1
		D.i2c=SMBus(B)
	def readfrom_mem(C,addr,memaddr,nbytes,*,addrsize=8):A=nbytes;B=[_A]*A;C.smbus_i2c_read(addr,memaddr,B,A,addrsize=addrsize);return B
	def writeto_mem(A,addr,memaddr,buf,*,addrsize=8):A.smbus_i2c_write(addr,memaddr,buf,len(buf),addrsize=addrsize)
	def smbus_i2c_write(F,address,reg,data_p,length,addrsize=8):
		D=addrsize;C=address;A=reg;G=0;B=[]
		for H in range(length):B.append(data_p[H])
		if D==8:E=i2c_msg.write(C,[A]+B)
		elif D==16:E=i2c_msg.write(C,[A>>8,A&255]+B)
		else:raise Exception(_F)
		F.i2c.i2c_rdwr(E);return G
	def smbus_i2c_read(I,address,reg,data_p,length,addrsize=8):
		D=addrsize;C=length;B=reg;A=address;E=0
		if D==8:F=i2c_msg.write(A,[B])
		elif D==16:F=i2c_msg.write(A,[B>>8,B&255])
		else:raise Exception(_F)
		G=i2c_msg.read(A,C);I.i2c.i2c_rdwr(F,G)
		if E==0:
			for H in range(C):data_p[H]=ord(G.buf[H])
		return E
	def write8(B,addr,reg,data):
		if reg is _A:A=int.from_bytes(data,_C);B.i2c.write_byte(addr,A)
		else:C=int.from_bytes(reg,_C);A=int.from_bytes(data,_C);B.i2c.write_byte_data(addr,C,A)
	def read16(A,addr,reg):B=int.from_bytes(reg,_C);return A.i2c.read_word_data(addr,B).to_bytes(2,byteorder='little',signed=_D)
def create_unified_i2c(bus=_A,freq=_A,sda=_A,scl=_A,suppress_warnings=_B):
	if _SYSNAME==_E:A=I2CUnifiedMicroBit(freq=freq)
	elif _SYSNAME=='Linux':A=I2CUnifiedLinux(bus=bus,suppress_warnings=suppress_warnings)
	else:A=I2CUnifiedMachine(bus=bus,freq=freq,sda=sda,scl=scl)
	return A