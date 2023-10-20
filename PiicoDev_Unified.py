'''
PiicoDev.py: Unifies I2C drivers for different builds of MicroPython
Changelog:
    - 2021       M.Ruppe - Initial Unified Driver
    - 2022-10-13 P.Johnston - Add helptext to run i2csetup script on Raspberry Pi 
    - 2022-10-14 M.Ruppe - Explicitly set default I2C initialisation parameters for machine-class (Raspberry Pi Pico + W)
    - 2023-01-31 L.Howell - Add minimal support for ESP32
    - 2023-05-17 M.Ruppe - Make I2CUnifiedMachine() more flexible on initialisation. Frequency is optional.
'''
import os
_SYSNAME = os.uname().sysname
compat_ind = 1
i2c_err_str = 'PiicoDev could not communicate with module at address 0x{:02X}, check wiring'
setupi2c_str = ', run "sudo curl -L https://piico.dev/i2csetup | bash". Suppress this warning by setting suppress_warnings=True'

if _SYSNAME == 'microbit':
    from microbit import i2c
    from utime import sleep_ms
    
elif _SYSNAME == 'Linux':
    from smbus2 import SMBus, i2c_msg
    from time import sleep
    from math import ceil
    
    def sleep_ms(t):
        sleep(t/1000)

else:
    from machine import I2C, Pin
    from utime import sleep_ms

class I2CBase:
    def writeto_mem(self, addr, memaddr, buf, *, addrsize=8):
        raise NotImplementedError('writeto_mem')

    def readfrom_mem(self, addr, memaddr, nbytes, *, addrsize=8):
        raise NotImplementedError('readfrom_mem')

    def write8(self, addr, buf, stop=True):
        raise NotImplementedError('write')

    def read16(self, addr, nbytes, stop=True):
        raise NotImplementedError('read')

    def __init__(self, bus=None, freq=None, sda=None, scl=None):
        raise NotImplementedError('__init__')

class I2CUnifiedMachine(I2CBase):
    def __init__(self, bus=None, freq=None, sda=None, scl=None):
        if _SYSNAME == 'esp32' and (bus is None or sda is None or scl is None):
            raise Exception('Please input bus, machine.pin SDA, and SCL objects to use ESP32')
        
        if freq is None: freq = 400_000
        if not isinstance(freq, (int)):
            raise ValueError("freq must be an Int")
        if freq < 400_000: print("\033[91mWarning: minimum freq 400kHz is recommended if using OLED module.\033[0m")
        if bus is not None and sda is not None and scl is not None:
            print('Using supplied bus, sda, and scl to create machine.I2C() with freq: {} Hz'.format(freq))
            self.i2c = I2C(bus, freq=freq, sda=sda, scl=scl)
        elif bus is None and sda is None and scl is None:
            self.i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=freq) # RPi Pico in Expansion Board
        else:
            raise Exception("Please provide at least bus, sda, and scl")

        self.writeto_mem = self.i2c.writeto_mem
        self.readfrom_mem = self.i2c.readfrom_mem

    def write8(self, addr, reg, data):
        if reg is None:
            self.i2c.writeto(addr, data)
        else:
            self.i2c.writeto(addr, reg + data)
            
    def read16(self, addr, reg):
        self.i2c.writeto(addr, reg, False)
        return self.i2c.readfrom(addr, 2)

class I2CUnifiedMicroBit(I2CBase):
    def __init__(self, freq=None):
        if freq is not None:
            print('Initialising I2C freq to {}'.format(freq))
            microbit.i2c.init(freq=freq)
            
    def writeto_mem(self, addr, memaddr, buf, *, addrsize=8):
        ad = memaddr.to_bytes(addrsize // 8, 'big')  # pad address for eg. 16 bit
        i2c.write(addr, ad + buf)
        
    def readfrom_mem(self, addr, memaddr, nbytes, *, addrsize=8):
        ad = memaddr.to_bytes(addrsize // 8, 'big')  # pad address for eg. 16 bit
        i2c.write(addr, ad, repeat=True)
        return i2c.read(addr, nbytes)    
    
    def write8(self, addr, reg, data):
        if reg is None:
            i2c.write(addr, data)
        else:
            i2c.write(addr, reg + data)

    def read16(self, addr, reg):
        i2c.write(addr, reg, repeat=True)
        return i2c.read(addr, 2)
            
class I2CUnifiedLinux(I2CBase):
    def __init__(self, bus=None, suppress_warnings=True):
        if suppress_warnings == False:
            with open('/boot/config.txt') as config_file:
                if 'dtparam=i2c_arm=on' in config_file.read():
                    pass
                else:
                    print('I2C is not enabled. To enable' + setupi2c_str)
                config_file.close()
            with open('/boot/config.txt') as config_file:
                if 'dtparam=i2c_arm_baudrate=400000' in config_file.read():
                    pass
                else:
                    print('Slow baudrate detected. If glitching occurs' + setupi2c_str)
                config_file.close()
        if bus is None:
            bus = 1
        self.i2c = SMBus(bus)

    def readfrom_mem(self, addr, memaddr, nbytes, *, addrsize=8):
        data = [None] * nbytes # initialise empty list
        self.smbus_i2c_read(addr, memaddr, data, nbytes, addrsize=addrsize)
        return data
    
    def writeto_mem(self, addr, memaddr, buf, *, addrsize=8):
        self.smbus_i2c_write(addr, memaddr, buf, len(buf), addrsize=addrsize)
    
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
            raise Exception('address must be 8 or 16 bits long only')
        self.i2c.i2c_rdwr(msg_w)
        return ret_val
        
    def smbus_i2c_read(self, address, reg, data_p, length, addrsize=8):
        ret_val = 0
        if addrsize == 8:
            msg_w = i2c_msg.write(address, [reg]) # warning this is set up for 16-bit addresses
        elif addrsize == 16:
            msg_w = i2c_msg.write(address, [reg >> 8, reg & 0xff]) # warning this is set up for 16-bit addresses
        else:
            raise Exception('address must be 8 or 16 bits long only')
        msg_r = i2c_msg.read(address, length)
        self.i2c.i2c_rdwr(msg_w, msg_r)
        if ret_val == 0:
            for index in range(length):
                data_p[index] = ord(msg_r.buf[index])
        return ret_val
    
    def write8(self, addr, reg, data):
        if reg is None:
            d = int.from_bytes(data, 'big')
            self.i2c.write_byte(addr, d)
        else:
            r = int.from_bytes(reg, 'big')
            d = int.from_bytes(data, 'big')
            self.i2c.write_byte_data(addr, r, d)
    
    def read16(self, addr, reg):
        regInt = int.from_bytes(reg, 'big')
        return self.i2c.read_word_data(addr, regInt).to_bytes(2, byteorder='little', signed=False)

def create_unified_i2c(bus=None, freq=None, sda=None, scl=None, suppress_warnings=True):
    if _SYSNAME == 'microbit':
        i2c = I2CUnifiedMicroBit(freq=freq)
    elif _SYSNAME == 'Linux':
        i2c = I2CUnifiedLinux(bus=bus, suppress_warnings=suppress_warnings)
    else:
        i2c = I2CUnifiedMachine(bus=bus, freq=freq, sda=sda, scl=scl)
    return i2c


#
# PiicoDev devices presence tests
#
# Mjt 20231016
#

_Debug = 0	# can be chucked out, used to print short WIP messages, and to execute the function tests.


class PiicoDev_test():
    """
    # PiicoDev devices presence tests
    #
    # Mjt 20231016

    the simple tests without this module
    ------------------------------------
    i2c = I2C(id=0)         # PiicoDev chain on i2c channel 0
    connected = i2c.scan()  # whats connected
    print(connected)
    for i in connected:
        print(i, hex(i))

    What this module provides
    =========================
    Instantiation
    -------------
        # the default for standard PiicoDev setup
        tests = PiicoDev_test()
    OR
        # for an alternate i2c bus on GPIO6 and GPOI7
        test_altbus = PiicoDev_test(id=1, scl=Pin(7), sda=Pin(6))
       
    
    Immediately after this you can display what has been detected on the default i2c bus by either
    
        print(tests.connected)
    or
        tests.show()

    these print a list of detected i2c ID's
        [16, 60, 82, 83, 119]
        
    Available functions
    -------------------
        clear()                 - clears the list of connected i2c devices
        rescan()                - clears and rescans the default i2c bus and repopulates the list
        show_int()              - prints the list of connected ID's in DECIMAL detected by the original/most recent scan
        show_hex()              - prints the list of connected ID's in HEXADECIMAL detected by the original/most recent scan
        is_ID_connected(id)     - returns 1 if the ID is in the list, otherwise 0
        how_many_connected()    - returns count of detected ID's
        
        details()               - prints 'human name' of the connected ID's e.g. 'OLED Module'
            details('what')     - prints 'human name' of the connected ID's e.g. 'OLED Module'       
            details('short')    - prints 'short_name' of the connected ID's e.g. 'SSD1306'
            details('long')     - prints 'long_name' of the connected ID's e.g. 'PiicoDev OLED Module SSD1306'
        *****
        The details() function can also access a user defined dictionary of devices from other manufacturers.
        The user dictionary MUST be in the same format as the internal dictionaries
        
            extern_list: dict = {
                0x53: {		# 16.  0x10
                    'what': 'Ambient Light-UV Sensor',
                    'long_name': 'Adafruit LTR390 Ambient Light-UV Sensor',
                    'short_name': 'LTR390'},
                <nextID>: {    # possible comment
                    'what': 'simple description',
                    'long_name': 'lengthy description',
                    'short_name': 'MFR code'},
            }

        then calliing the details() function as below _AFTER_ the user dictionary is defined, will
        display this if the LTR390 is in the connected devices list
        
            details('what', extern_list ) - prints 'human name' of the connected ID's e.g. 'Ambient Light-UV Sensor'       
            details('short', extern_list) - prints 'short_name' of the connected ID's e.g. 'LTR390'
            details('long', extern_list)  - prints 'long_name' of the connected ID's e.g. 'Adafruit LTR390 Ambient Light-UV Sensor'

        what_is(id)             - prints 'human name' of the given ID e.g. 'RGB LED Module'
            what_is(id, 'what') - prints 'human name' of the given ID e.g. 'RGB LED Module'
            what_is(id, 'short')- prints 'short_name' of the given ID e.g. 'LED'
            what_is(id, 'long') - prints 'long_name' of the given ID e.g. 'PiicoDev 3x RGB LED Module'
            
        show_all()              - prints all 'human names' from the main internal dictonary
            show_all('what')    - prints all 'human names' from the main internal dictonary
            show_all('short')   - prints all 'short names' from the main internal dictonary
            show_all('long')    - prints all 'long names' from the main internal dictonary
          ** with extra option 'show' also displays similar entries from the conflicts dictionary
            show_all('what', 'show')    - prints all 'human names' from the conflict internal dictonary
            show_all('short', show')    - prints all 'shout names' from the conflict internal dictonary
            show_all('long', 'show')    - prints all 'long names' from the conflict internal dictonary
            
    Address conflicts
    -----------------
    Where possible this module will highlight potential conflicts, since some PiicoDev devices
    do have addresses that could collide. This can be dealt with by setting the module address switch (ASW)
    to a non default setting (if available), OR by programatically changing the device address if possible.
    
    This module only 'knows' about PiicoDev devices.
    
    'Constant' values
    -----------------
    Internally there is a set of constant names for the PiicoDev addresses, both the default address, and
    if available the alternate address that can be selected by changing the address switch (ASW)
    (at this time only one alternate is provided)
    
    These constants can be used after instantiation in user code
    
        tests.__BME280_ID       # ==  0x77 or 119. this is a fixed address
        tests.__VEML6030_0_ID   # ==  0x10 or 16.  this is the value when the ASW is OFF  
        tests.__VEML6030_1_ID   # ==  0x48 or 72.  this is the value is the ASW is ON  
    
    NOTE: =============================================================================
    NOTE:
    NOTE: The "Constants" and the __TWO__ dictionary lists MUST be checked / updated
    NOTE:    when new PiicoDev devices are created by Core Electronics
    NOTE:     sorry team ;-)
    NOTE:
    NOTE: =============================================================================
    """
    
    #
    # declare "CONSTANTS"
    # these are used to uniquely identify the various (conflicting) PiicoDev addresses
    #  note the 'conflict' markers   ----vv   and    ----^^
    #
    #  can use outside the class if prefixed with instantiated classname
    #  i.e.
    #
    # tests = PiicoDev_test()
    # if tests.is_ID_connected(tests.__BME280_ID):
    #    print('have BME280')
    #

    __LED_ID = 0x8                      # 8.      RGB LEDS
                                # ----vv
    __VEML6030_0_ID = 0x10		# 16. xx  Light sensor (ASW off)
    __VEML6040_ID = 0x10		# 16. xx  Colour sensor
                                # ----^^
    __LIS3DH_1_ID = 0x18		# 24.     Accelerometer - ASW ON
    __LIS3DH_0_ID = 0x19		# 25.     Accelerometer - ASW OFF
    __TRANSCEIVER_ID = 0x1a		# 26.     Transceiver
    __QMC6310_ID = 0x1c			# 28.     Magnetometer
    __TOUCH_ID = 0x28			# 40.     Capacitive sensor
    __VL53L1X_ID = 0x29			# 41.     Laser distance sensor
    __RFID_ID = 0x2c			# 44.     RFID module
                                # ----vv
    __ULTRASONIC_ID = 0x35		# 53. xx  Ultrasonic rangefinder
    __POTENTIOMETER_ID = 0x35           # 53. xx  Potentiometer
                                # ----^^
    __SSD1306_ID = 0x3c			# 60.     OLED display
    __BUTTON_ID = 0x42			# 66.     Pushbutton
    __SERVO_ID = 0x44			# 68.     Servo controller
                                # ----vv
    __TMP117_ID = 0x48			# 72. xx  Temperature sensor
    __VEML6030_1_ID = 0x48		# 72. xx  Light sensor (ASW on)
                                # ----^^
                                # ----vv
    __RV3028_ID = 0x52			# 82. xx  RTC
    __ENS160_1_ID = 0x52		# 82. xx  Air quality sensor (ASW on)
                                # ----^^
    __ENS160_0_ID = 0x53		# 83.     Air quality sensor (ASW off)
    __BUZZER_ID = 0x5c			# 92.     Buzzer
    __MS5637_ID = 0x76			# 118.    Pressuure sensor
    __BME280_ID = 0x77			# 119.    Atmospheric sensor

    ################
    ## the MAIN list
    ################
    # the dictionary of the fixed, and where possible the default (ASW off) ID's
    #  also has some non-conflicting (ASW on) ID's
    PiicoDev_list: dict = {
        __LED_ID: {			# 8.   0x8
            'what': 'RGB LED Module',
            'long_name': 'PiicoDev 3x RGB LED Module',
            'short_name': 'LED'},
        __VEML6040_ID: {		# 16.  0x10
            'what': 'Colour Sensor',
            'long_name': 'PiicoDev VEML6040 Colour Sensor',
            'short_name': 'VEML6040'},
        __LIS3DH_1_ID: {		# 24.  0x18
            'what': 'Accelerometer (ASW on)',
            'long_name': 'PiicoDev 3-Axis Accelerometer LIS3DH (ASW on)',
            'short_name': 'LIS3DH (ASW on)'},
        __LIS3DH_0_ID: {		# 25.  0x19
            'what': 'Accelerometer (ASW off)',
            'long_name': 'PiicoDev 3-Axis Accelerometer LIS3DH (ASW off)',
            'short_name': 'LIS3DH (ASW off)'},
        __TRANSCEIVER_ID: {		# 26.  0x1A
            'what': 'Transceiver',
            'long_name': 'PiicoDev Transceiver 915MHz',
            'short_name': 'TRANSCEIVER'},
        __QMC6310_ID: {		# 28.  0x1c
            'what': 'Magnetometer',
            'long_name': 'PiicoDev Magnetometer QMC6310',
            'short_name': 'QMC6310'},
        __TOUCH_ID: {		# 40.  0x28
            'what': 'Capacitive Touch Sensor',
            'long_name': 'PiicoDev Capacitive Touch Sensor',
            'short_name': 'TOUCH'},
        __VL53L1X_ID: {		# 41.  0x29
            'what': 'Laser Distance Sensor',
            'long_name': 'PiicoDev Laser Distance Sensor VL53L1X',
            'short_name': 'VL53L1X'},
        __RFID_ID: {		# 45.  0x2c
            'what': 'RFID Module',
            'long_name': 'PiicoDev RFID Module (NFC 13.56MHz)',
            'short_name': 'RFID'},
        __ULTRASONIC_ID: {	# 53.  0x35
           'what': 'Ultrasonic Rangefinder',
            'long_name': 'PiicoDev Ultrasonic Rangefinder Module',
            'short_name': 'ULTRASONIC'},
        __SSD1306_ID: {		# 60.  0x3c
            'what': 'OLED Module',
            'long_name': 'PiicoDev OLED Module SSD1306',
            'short_name': 'SSD1306',
            'initme': 'create_PiicoDev_SSD1306()'},
        __BUTTON_ID: {		# 66.  0x42
            'what': 'Button',
            'long_name': 'PiicoDev Button',
            'short_name': 'BUTTON'},
        __SERVO_ID: {		# 68.  0x44
            'what': 'Servo Driver',
            'long_name': 'PiicoDev Servo Driver (4 Channel)',
            'short_name': 'SERVO'},
        __TMP117_ID: {		# 72.  0x48
            'what': 'Precision Temperature Sensor',
            'long_name': 'PiicoDev TMP117 Precision Temperature Sensor',
            'short_name': 'TMP117'},
        __RV3028_ID: {		# 82.  0x52
            'what': 'Real Time Clock',
            'long_name': 'PiicoDev Real Time Clock (RTC) RV3028',
            'short_name': 'RV3028'},
        __ENS160_0_ID: {		# 83.  0x53
            'what': 'Air Quality Sensor (ASW off)',
            'long_name': 'PiicoDev Air Quality Sensor ENS160 (ASW off)',
            'short_name': 'ENS160 (ASW off)'},
        __BUZZER_ID: {		# 92.  0x5c
            'what': 'Buzzer Module',
            'long_name': 'PiicoDev Buzzer Module',
            'short_name': 'BUZZER'},
        __MS5637_ID: {		# 118.  0x76
            'what': 'Pressure Sensor',
            'long_name': 'PiicoDev Pressure Sensor MS5637',
            'short_name': 'MS5637'},
        __BME280_ID: {		# 119.  0x77
            'what': 'Atmospheric Sensor',
            'long_name': 'PiicoDev BME280 Atmospheric Sensor',
            'short_name': 'BME280'},
    }

    #####################
    ## the conflicts list
    #####################
    # the dictionary of the conflicting fixed, and conflicting (ASW on) ID's
    #  also has some conflicting (ASW off) ID's
    PiicoDev_conf_list: dict = {
        __VEML6030_0_ID: {		# 16.  0x10
            'what': 'Ambient Light Sensor (ASW off)',
            'long_name': 'PiicoDev VEML6030 Ambient Light Sensor (ASW off)',
            'short_name': 'VEML6030 (ASW off)'},
        __POTENTIOMETER_ID: {	# 53.  0x35
           'what': 'Potentiometer',
            'long_name': 'PiicoDev Potentiometer (Rotary)',
            'short_name': 'Potentiometer'},
        __VEML6030_1_ID: {	# 72.  0x48
            'what': 'Ambient Light Sensor (ASW on)',
            'long_name': 'PiicoDev VEML6030 Ambient Light Sensor (ASW on)',
            'short_name': 'VEML6030 (ASW on)'},
        __ENS160_1_ID: {		# 82.  0x52
            'what': 'Air Quality Sensor (ASW on)',
            'long_name': 'PiicoDev Air Quality Sensor ENS160 (ASW on)',
            'short_name': 'ENS160 (ASW on)'},
    }


    #
    # PiicoDev defaults pre-defined
    # can be overloaded with other values if needed to establish a second/alternate i2c bus
    #
    def __init__(self, id=0, scl=Pin(9), sda=Pin(8), freq=400_000):
        self.i2c = I2C(id=id, scl=scl, sda=sda, freq=freq)
        self.connected = self.i2c.scan()
        
    def clear(self):
        self.connected = []
        
    def rescan(self):
        self.connected = []
        self.connected = self.i2c.scan()
    
    def show_int(self):
        print(self.connected)
    
    def show_hex(self):
        print( [hex(i) for i in self.connected] )

    def is_ID_connected(self, id):
        if _Debug == 1:
            print('is_ID_connected(',id,')')
        if self.connected.count(id) == 1:
            return(1)
        else:
            return(0)
    
    def how_many_connected(self):
        if _Debug == 1:
            print('how_many__connected()')
        return(len(self.connected))

    def details(self, mode='what', extlist=None):
        if _Debug == 1:
            print('details(',mode,')')
        if len(self.connected) == 0:
            print('nothing connected')
        else:
            for i in self.connected:
                hit = 0
                if i in self.PiicoDev_list:
                    self.print_main(i, mode)
#                    if mode == 'long':
#                        s = self.PiicoDev_list[i]['long_name']
#                    elif mode == 'short':
#                        s = self.PiicoDev_list[i]['short_name']
#                    else:   # assume 'what'
#                        s = self.PiicoDev_list[i]['what']
#                    print(i, hex(i), s)
                    hit = 1
                if i in self.PiicoDev_conf_list:
                    print('   vvv Possible conflict vvv')
                    self.print_conf(i, mode)
#                    if mode == 'long':
#                        s = self.PiicoDev_conf_list[i]['long_name']
#                    elif mode == 'short':
#                        s = self.PiicoDev_conf_list[i]['short_name']
#                    else:   # assume 'what'
#                        s = self.PiicoDev_conf_list[i]['what']
#                    print(i, hex(i), s, '<<<<< Possible conflict')
                    hit = 1
                if extlist != None:
                    if i in extlist:
                        print('   vvv EXTERNAL LIST --- Possible conflict vvv')
                        if mode == 'long':
                            s = extlist[i]['long_name']
                        elif mode == 'short':
                            s = extlist[i]['short_name']
                        else:   # assume 'what'
                            s = extlist[i]['what']
                        print(i, hex(i), s)
                        hit = 1
                if hit == 0:
                    print('Unknown device at ID ', i)

    def what_is(self, id, mode='what'):
        hit = 0
        if id in self.PiicoDev_list:
            self.print_main(id, mode)
#            if mode == 'long':
#                s = self.PiicoDev_list[id]['long_name']
#            elif mode == 'short':
#                s = self.PiicoDev_list[id]['short_name']
#            else:   # assume 'what'
#                s = self.PiicoDev_list[id]['what']
#            print('Found:', id, hex(id), s)
            hit = 1
        if id in self.PiicoDev_conf_list:
            print('   vvv Possible conflict vvv')
            self.print_conf(id, mode)
#            if mode == 'long':
#                s = self.PiicoDev_conf_list[id]['long_name']
#            elif mode == 'short':
#                s = self.PiicoDev_conf_list[id]['short_name']
#            else:   # assume 'what'
#                s = self.PiicoDev_conf_list[id]['what']
#            print('Found but possible conflict:', id, hex(id), s)
            hit = 1
        if hit == 0:
            print('Unknown ID ', id)

    def show_all(self, mode='what', conf='noshow' ):
        for i in sorted(self.PiicoDev_list):
            self.print_main(i, mode)
#            if mode == 'long':
#                print(i, hex(i), self.PiicoDev_list[i]['long_name'])
#            elif mode == 'short':
#                print(i, hex(i), self.PiicoDev_list[i]['short_name'])
#            else:	# assume 'what'
#                print(i, hex(i), self.PiicoDev_list[i]['what'])
        if conf != 'noshow':
            print('-- conflicting --')
            for i in sorted(self.PiicoDev_conf_list):
                self.print_conf(i, mode)
#                if mode == 'long':
#                    print(i, hex(i), self.PiicoDev_conf_list[i]['long_name'])
#                elif mode == 'short':
#                    print(i, hex(i), self.PiicoDev_conf_list[i]['short_name'])
#                else:	# assume 'what'
#                    print(i, hex(i), self.PiicoDev_conf_list[i]['what'])
                
#
# Print common functions
#
    def print_main(self, id, mode):
        if mode == 'long':
            s = self.PiicoDev_list[id]['long_name']
        elif mode == 'short':
            s = self.PiicoDev_list[id]['short_name']
        else:   # assume 'what'
            s = self.PiicoDev_list[id]['what']
        print(id, hex(id), s)

    def print_conf(self, id, mode):
        if mode == 'long':
            s = self.PiicoDev_conf_list[id]['long_name']
        elif mode == 'short':
            s = self.PiicoDev_conf_list[id]['short_name']
        else:   # assume 'what'
            s = self.PiicoDev_conf_list[id]['what']
        print(id, hex(id), s)

# end of  class

if _Debug:
    tests = PiicoDev_test()

    # for an alternate i2c bus on GPIO6 and GPOI7
    test_altbus = PiicoDev_test(id=1, scl=Pin(7), sda=Pin(6))

    print('tests.connected')
    print(tests.connected)
    print('clear()')
    tests.clear()
    print(tests.connected)
    print('rescan()')
    tests.rescan()
    print(tests.connected)
    print('show()')
    tests.show_int()
    tests.show_hex()
    print('how many')
    aa = tests.how_many_connected()
    print(aa)
    print('details()')
    tests.details()
    tests.details('short')
    tests.details('long')
    print('************')
    tests.details('what', extern_list)
    print('************')
    aa = tests.is_ID_connected(119)
    print(aa)

    aa = tests.is_ID_connected(0x77)
    print(aa)

    if tests.is_ID_connected(tests.__BME280_ID):
        print('have BME280')

    if tests.is_ID_connected(tests.__POTENTIOMETER_ID):
        print('have Ultrasonic rangfinder - cant distinguish conflicting IDs')
    else:
        print('oops')
        
    tests.what_is(0xff)	# no such ID, will complain
    
    tests.what_is(53, 'long')

    tests.show_all()

    tests.show_all('long','show')

    print('***************************************************')


