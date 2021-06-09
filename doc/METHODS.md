# PiicoDev Unified Methods

The following methods can be used for I2C communication:

Method | Usage | Description
--- | --- | ---
`writeto_mem(addr, memaddr, buf, *, addrsize=8)` | Preferred | Write *buf* to the target specified by *addr* starting from the memory address specified by *memaddr*. The argument *addrsize* specifies the address size in bits.  The method returns `None`.
`readfrom_mem(addr, memaddr, nbytes, *, addrsize=8)` | Preferred | Read *nbytes* from the target specified by *addr* starting from the memory address specified by *memaddr*. The argument *addrsize* specifies the address size in bits. Returns a `bytes` object with the data read.
`write8(addr, reg, data)` | Not preferred | Write *reg* immediately followed by *data* to the target specified by *addr*.  If *reg* is `None`, only *data* will be sent to the target.
`read16(addr, reg)` | Not preferred | Read two bytes from the target specified by *addr* after writing *reg* to the target.  Returns a `bytes` object with the data read.

Where:

Value | Type
--- | ---
addr | bytes
memaddr | bytes
reg | bytes
data | bytes
nbytes | int
addrsize | int
