#!/usr/bin/env python

import struct
import time
import sys
try:
	from hid import *
except Exception, e:
	print e
	print "Please install libhid: http://libhid.alioth.debian.org/"
	sys.exit(1)


class RawHID:
	"""
	HID communications class.
	"""

	READ_ENDPOINT = 0x81
	WRITE_ENDPOINT = 0x02
	INTERFACE = 0

	BLOCK_SIZE = 64
	TIMEOUT = 1000 # milliseconds
	CONNECT_RETRIES = 3

	def __init__(self, verbose=False):
		self.verbose = verbose
		self.hid = None
		self.rep = self.READ_ENDPOINT
		self.wep = self.WRITE_ENDPOINT

	# TODO: Need to flush USB data for the device once it's opened so old data doesn't screw us up
	def open(self, vid, pid, rep=None, wep=None):
		"""
		Initialize libhid and connect to USB device.

		@vid   - Vendor ID of the USB device.
		@pid   - Product ID of the USB device.
		@rep   - USB input endpoint
		@wep   - USB output endpoint

		Returns True on success.
		Returns False on failure.
		"""

		retval = False

		if rep is not None:
			self.rep = rep
		if wep is not None:
			self.wep = wep

		hid_ret = hid_init()
		if hid_ret == HID_RET_SUCCESS:
			self.hid = hid_new_HIDInterface()
			match = HIDInterfaceMatcher()
			match.vendor_id = vid
			match.product_id = pid
		
			hid_ret = hid_force_open(self.hid, self.INTERFACE, match, self.CONNECT_RETRIES)
			if hid_ret == HID_RET_SUCCESS:
				retval = True
				if self.verbose:
					hid_write_identification(sys.stderr, self.hid)
			else:
				raise Exception("hid_force_open() failed with error code: %d\n" % hid_ret)
		else:
			raise Exception("hid_init() failed with error code: %d\n" % hid_ret)

		return retval

	def close(self):
		"""
		Close HID connection and clean up.

		Returns True on success.
		Returns False on failure.
		"""

		retval = False

		if hid_close(self.hid) == HID_RET_SUCCESS:
			retval = True

		hid_cleanup()

		return retval

	def send(self, packet, timeout=TIMEOUT):
		"""
		Send a USB packet to the connected USB device.
	
		@packet  - Data, in string format, to send to the USB device.
		@timeout - Send timeout, in milliseconds. Defaults to TIMEOUT.
	
		Returns True on success.
		Returns False on failure.
		"""

		tx = 0
		retval = False

		while tx < len(packet):
			hid_ret = hid_interrupt_write(self.hid, self.wep, packet[tx:tx+self.BLOCK_SIZE], timeout)
			
			if hid_ret != HID_RET_SUCCESS:
				retval = False
				raise Exception("hid_interrupt_write failed with error code 0x%X" % hid_ret)
			else:
				tx += self.BLOCK_SIZE
			
		return retval

	def recv(self, count=BLOCK_SIZE, timeout=TIMEOUT):
		"""
		Read data from the connected USB device.
	
		@len     - Number of bytes to read. Defaults to BLOCK_SIZE.
		@timeout - Read timeout, in milliseconds. Defaults to TIMEOUT.
	
		Returns the received bytes on success.
		Returns None on failure.
		"""

		rx = 0
		data = ''

		if count is None:
			count = self.BLOCK_SIZE
		
		while rx < count:
			hid_ret, packet = hid_interrupt_read(self.hid, self.rep, self.BLOCK_SIZE, timeout)

			if hid_ret != HID_RET_SUCCESS:
				raise Exception("hid_interrupt_read failed with error code 0x%X" % hid_ret)
			else:
				data += packet
				rx += len(packet)

		return data
	
class Gumbi:
	"""
	Primary gumbi class. All other classes that interact with the Gumbi board should be subclassed from this.
	"""

	VID = 0xFFFF
	PID = 0x1337
	ACK = "GUMBIACK"
	NACK = "GUMBINACK"
	MAX_PINS = 128
	MAX_COMMANDS = 16
	RESET_LEN = 1024
	UNUSED = 0xFF
	NULL = "\x00"
	DUMMY_BYTE = "\xFF"

	TBP_DEFAULT = 25
	TOE_DEFAULT = 0

	NOP = 0
	PNORFLASH = 1
	SPIFLASH = 2
	SPIPROM = 3
	I2CPROM = 4
	PING = 5
	INFO = 6
	SPEEDTEST = 7
	GPIO = 8
	GID = 9
	XFER = 10
	PINCOUNT = 11

	EXIT = 0
	READ = 1
	WRITE = 2
	ERASE = 3
	HIGH = 4
	LOW = 5

	MODE_KEY = "MODE"
	MODE_VALUE = None

	def __init__(self, new=True):
		"""
		Class constructor, calls self._open().

		@new  - Set to False to not open a connection to the Gumbi board.
		"""
		self.ts = 0
		self.num_pins = 0
		self.hid = RawHID()
		if new:
			self._open()

	def _open(self):
		"""
		Opens a connection to the Gumbi board.
		"""
		self.hid.open(self.VID, self.PID)

	def _close(self):
		"""
		Closes the connection with the Gumbi board.
		"""
		self.hid.close()

	def ParseConfigLine(self, line):
		"""
		Parses a configuration file line.

		@line - A line from the configuration file.

		Returns the (key, value) pair from the line.
		"""
		key = value = None
		line = line.split('#')[0]
		if '=' in line:
			(key, value) = line.split('=', 1)
			key = key.strip().upper()
			value = value.strip().upper()
			if ',' in value:
				value = value.split(',')
				for i in range(0, len(value)):
					try:
						value[i] = int(value[i])
					except:
						try:
							value[i] = int(value[i], 16)
						except:
							pass
			else:
				try:
					value = [int(value)]
				except:
					try:
						value = [int(value, 16)]
					except:
						pass
		return (key, value)

	def StartTimer(self):
		"""
		Starts the timer.
		"""
		self.ts = time.time()

	def StopTimer(self):
		"""
		Stops the timer and returns the seconds elapsed since StartTimer().
		"""
		return (time.time() - self.ts)

	def Pin2Real(self, pin):
		"""
		Converts user-supplied pin numbers (index 1) to Gumbi board pin numbers (index 0).
		"""
		if pin is not None and pin > 0:
			return (pin - 1)
		else:
			return pin

	def Pack32(self, value):
		"""
		Packs a 32-bit value for transmission to the Gumbi board.
		"""
                return struct.pack("<I", value)

        def Pack16(self, value):
		"""
		Packs a 16-bit value for transmission to the Gumbi board.
		"""
                return struct.pack("<H", value)

        def PackByte(self, value):
		"""
		Packs an 8-bit value for transmission to the Gumbi board.
		"""
                return chr(value)

	def PackDWords(self, data):
		"""
		Packs an array of 32-bit values for transmission to the Gumbi board.
		"""
		pdata = ''
		for dword in data:
			pdata += self.Pack32(dword)
		return pdata

        def PackBytes(self, data):
		"""
		Packs an array of 8-bit values for transmission to the Gumbi board.
		"""
                pdata = ''
                for byte in data:
                        pdata += self.PackByte(byte)
                return pdata

	def PackFiller(self, count):
		"""
		Returns count filler bytes of data.
		"""
		return (self.NULL * count)

	def ReadAck(self):
		"""
		Reads an ACK/NACK from the Gumbi board. Returns True on ACK, raises an exception on NACK.
		"""
		line = self.ReadText() 
		if line != self.ACK:
			print "Instead of ack, I got:", line
			raise Exception(self.ReadText())
		return True

	def SetMode(self, mode):
		"""
		Puts the Gumbi board in the specified mode.
		"""
		self.Write(self.PackByte(mode))
		self.ReadAck()

	def ReadText(self):
		"""
		Reads and returns a new-line terminated string from the Gumbi board.
		"""
		return self.Read().strip(self.NULL)

	def Read(self, n=None):
		"""
		Reads n bytes of data from the Gumbi board. Default n == 1.
		"""
		return self.hid.recv(n)

	def Write(self, data):
		"""
		Sends data to the Gumbi board and verifies acknowledgement.
		"""
		self.hid.send(data)

	def ReadChip(self, start, count):
		"""
		Reads a number of bytes from the target chip, beginning at the given start address.

		@start - Start address.
		@count - Number of bytes to read.

		Returns a string of bytes read from the chip.
		"""
		self.Write(self.config.Pack(self.READ, start, count))
		# Receive the ACK indicating the provided configuration is valid
		self.ReadAck()
		# Receive the ACK indicating that the specified action is valid
		self.ReadAck()
		data = self.Read(count)
		# Receive the final ACK indicating that the read operation is complete
		self.ReadAck()
		return data

	def WriteChip(self, start, data):
		"""
		Writes a number of bytes to the target chip, beginning at the given start address.
		NOT CURRENTLY IMPLEMENTED.

		@start - Address to start writing at.
		@data  - String of data to write.

		Returns True on success, raises and exception on failure.
		"""
		self.Write(self.config.Pack(self.WRITE, start, len(data)))
		self.ReadAck()
		self.ReadAck()
		self.Write(data)
		while True:
			try:
				self.ReadAck()
				break
			except:
				pass
		print "The Write was ACKd!!"
		return True

	def Reset(self):
		"""
		Resets the communications stream with the Gumbi board.
		"""
		self.hid.send(self.PackByte(self.EXIT))
		for i in range(0, self.RESET_LEN):
			self.SetMode(self.NOP)

	def Close(self):
		"""
		Closes the connection with the Gumbi board.
		"""
		return self._close()

class PinCount(Gumbi):
	"""
	Class used to retrieve the number of available I/O pins on the Gumbi board.
	"""

	def Count(self):
		"""
		Returns the number of available I/O pins on the Gumbi board.
		"""
		self.SetMode(self.PINCOUNT)
		return ord(self.Read()[0])

class Configuration(Gumbi):
	"""
	Class responsible for reading config files and building a config data structure to send to the Gumbi board.
	"""

	CONFIG = {
		"TOE"		: [Gumbi.TOE_DEFAULT],
		"TBP"		: [Gumbi.TBP_DEFAULT],
		"ADDRESS"	: [],
		"DATA"		: [],
		"VCC"		: [],
		"GND"		: [],
		"CE"		: [Gumbi.UNUSED, 0],
		"WE"		: [Gumbi.UNUSED, 0],
		"OE"		: [Gumbi.UNUSED, 0],
		"BE"		: [Gumbi.UNUSED, 0],
		"BY"		: [Gumbi.UNUSED, 0],
		"WP"		: [Gumbi.UNUSED, 0],
		"RST"		: [Gumbi.UNUSED, 0],
		"WRITE_COMMANDS": [],
		"SDA"		: [0],
		"CLK"		: [0],
		"SS"		: [0],
		"MISO"		: [0],
		"MOSI"		: [0],
		# These are not part of the config strcture that gets pushed to the Gumbi board
		"PINS"		: [0],
		"TDI"		: [0],
		"TDO"		: [0],
		"TMS"		: [0]
	}
	
	def __init__(self, config, mode, pins=None):
		"""
		Class initializer. Must be called BEFORE SetMode so that it can retrieve the current pin count from the Gumbi board.

		@config - Path to the configuration file.
		@mode   - The expected MODE value in the configuration file.
		@pins   - Number of available I/O pins on the Gumbi board. If not specified, this is detected automatically.
		"""
		self.config = config
		self.cmode = mode
		self.num_pins = pins
		self._parse_config()
		self.package_pins = 0

		if self.num_pins is None:
			pc = PinCount()
			self.num_pins = pc.Count()
			pc.Close()

	def _pin2real(self, pin):
		"""
		Converts the pin number in the config file to the physical Gumbi pin number.
		"""
		pin = self.Pin2Real(pin)

		# If the number of pins in the target package was specified in the config file,
		# then treat the pin numbers as relative to the package type.
		if self.num_pins > 0 and self.package_pins > 0 and pin >= (self.package_pins / 2):
			pin += (self.num_pins - self.package_pins)
	
		return pin
		
	def _shift_pins(self):
		"""
		Shifts all pin numbers to be the appropriate pin number on the Gumbi board.
		"""
		self.CONFIG["ADDRESS"] = self._convert_pin_array(self.CONFIG["ADDRESS"])
		self.CONFIG["DATA"] = self._convert_pin_array(self.CONFIG["DATA"])
		self.CONFIG["VCC"] = self._convert_pin_array(self.CONFIG["VCC"])
		self.CONFIG["GND"] = self._convert_pin_array(self.CONFIG["GND"])
		self.CONFIG["CE"] = self._convert_control_pin(self.CONFIG["CE"])
		self.CONFIG["WE"] = self._convert_control_pin(self.CONFIG["WE"])
		self.CONFIG["OE"] = self._convert_control_pin(self.CONFIG["OE"])
		self.CONFIG["BE"] = self._convert_control_pin(self.CONFIG["BE"])
		self.CONFIG["BY"] = self._convert_control_pin(self.CONFIG["BY"])
		self.CONFIG["WP"] = self._convert_control_pin(self.CONFIG["WP"])
		self.CONFIG["RST"] = self._convert_control_pin(self.CONFIG["RST"])
		self.CONFIG["SDA"][0] = self._pin2real(self.CONFIG["SDA"][0])
		self.CONFIG["CLK"][0] = self._pin2real(self.CONFIG["CLK"][0])
		self.CONFIG["SS"][0] = self._pin2real(self.CONFIG["SS"][0])
		self.CONFIG["MISO"][0] = self._pin2real(self.CONFIG["MISO"][0])
		self.CONFIG["MOSI"][0] = self._pin2real(self.CONFIG["MOSI"][0])

	def _convert_control_pin(self, cp):
		"""
		Converts a control pin array to a valid pin offset on the Gumbi board.
		"""
		cpc = (self.UNUSED, 0)
		if cp is not None and len(cp) > 0:
			if len(cp) == 1:
				cpc = (self._pin2real(cp[0]), 0)
			else:
				cpc = (self._pin2real(cp[0]), cp[1])
		return cpc

	def _convert_pin_array(self, pins):
		"""
		Converts an array of pin numbers to valid pin numbers on the Gumbi board.
		"""
		for i in range(0, len(pins)):
			pins[i] = self._pin2real(pins[i])
		return pins

	def _pack_pins(self, pins):
		"""
		Packs an array of pins into a data structure.
		"""
		pd = self.PackBytes(pins)
		pd += self.PackFiller(self.MAX_PINS - len(pins))
		return pd

	def _pack_write_commands(self):
		pd = self.PackDWords(self.CONFIG["WRITE_COMMANDS"])
		# Each command consists of two 4 byte integers
		pd += self.PackFiller((self.MAX_COMMANDS * 8) - len(self.CONFIG["WRITE_COMMANDS"]))
		return pd

	def _config_mode(self):
		"""
		Returns the mode specified in a configuration file.

		@config - Configuration file path.

		Returns the mode on success. Returns None on failure.
		"""
		for line in open(self.config).readlines():
			(key, value) = self.ParseConfigLine(line)
			if key == self.MODE_KEY:
				return value
		return None

	def _parse_config(self):
		"""
		Parses the specified configuration file.
		"""
		mode_name = self._config_mode()
		if mode_name != self.cmode:
			raise Exception("Wrong mode specified in configuration file. Got '%s', expected '%s'." % (mode_name, self.cmode))

		for line in open(self.config).readlines():
			(key, value) = self.ParseConfigLine(line)
			if key is not None and value is not None:
				if self.CONFIG.has_key(key):
					self.CONFIG[key] = value

		self.package_pins = self.CONFIG["PINS"][0]

	def Pack(self, action, start, count):
		"""
		Packs the configuration data into a string of bytes suitable for transmission to the Gumbi board.
		"""
		self._shift_pins()
		data = self.PackByte(action)
		data += self.Pack32(start)
		data += self.Pack32(count)
		data += self.PackByte(self.CONFIG["TOE"][0])
		data += self.PackByte(self.CONFIG["TBP"][0])
		data += self.PackByte(len(self.CONFIG["WRITE_COMMANDS"]))
		data += self.Pack16(len(self.CONFIG["ADDRESS"]))
		data += self.Pack16(len(self.CONFIG["DATA"]))
		data += self.Pack16(len(self.CONFIG["VCC"]))
		data += self.Pack16(len(self.CONFIG["GND"]))
		data += self._pack_pins(self.CONFIG["ADDRESS"])
		data += self._pack_pins(self.CONFIG["DATA"])
		data += self._pack_pins(self.CONFIG["VCC"])
		data += self._pack_pins(self.CONFIG["GND"])
		data += self._pack_write_commands()
		data += self.PackBytes(self.CONFIG["CE"])
		data += self.PackBytes(self.CONFIG["WE"])
		data += self.PackBytes(self.CONFIG["OE"])
		data += self.PackBytes(self.CONFIG["BE"])
		data += self.PackBytes(self.CONFIG["BY"])
		data += self.PackBytes(self.CONFIG["WP"])
		data += self.PackBytes(self.CONFIG["RST"])
		data += self.PackByte(self.CONFIG["SDA"][0])
		data += self.PackByte(self.CONFIG["CLK"][0])
		data += self.PackByte(self.CONFIG["SS"][0])
		data += self.PackByte(self.CONFIG["MISO"][0])
		data += self.PackByte(self.CONFIG["MOSI"][0])
		print "PACKED DATA LENGTH::::::::::::: ", len(data)
		return data

class GPIO(Gumbi):
	"""
	Class to provide raw read/write access to all I/O pins.
	"""

	def __init__(self):
		"""
		Class constructor.
		"""
		Gumbi.__init__(self)
		self.SetMode(self.GPIO)

	def _exit(self):
		"""
		Exits the Gumbi board from GPIO mode.
		"""
		self.Write(self.PackBytes([self.EXIT, 0]))
		self.ReadAck()

	def PinHigh(self, pin):
		"""
		Sets the specified pin high.
		"""
		self.Write(self.PackBytes([self.HIGH, self.Pin2Real(pin)]))
		print self.ReadText()
		print self.ReadText()
		print self.ReadText()
		self.ReadAck()

	def PinLow(self, pin):
		"""
		Sets the specified pin low.
		"""
		self.Write(self.PackBytes([self.LOW, self.Pin2Real(pin)]))
		self.ReadAck()

	def ReadPin(self, pin):
		"""
		Reads and returns the value of the specified pin.
		High == 1, Low == 0.
		"""
		self.Write(self.PackBytes([self.READ, self.Pin2Real(pin)]))
		return ord(self.Read()[0])

	def Close(self):
		"""
		Exits GPIO mode, closes the Gumbi board connection.
		"""
		self._exit()
		self._close()

class JTAG(GPIO):
	"""
	Wrapper class around GPIO for interfacing with JTAG.
	"""

	MODE = "JTAG"

	def __init__(self, config=None, tdi=0, tdo=0, tms=0, clk=0):
		"""
		Class constructor.

		@config - Path to a configuration file. If not specified, tdi, tdo, tms and clk must be set.
		@tdi    - The pin connected to TDI.
		@tdo    - The pin connected to TDO.
		@tms    - The pin connected to TMS.
		@clk    - The pin connected to CLK.
		"""
		self.tdi = tdi
		self.tdo = tdo
		self.tmd = tmd
		self.clk = clk

		if config is not None:
			self.config = Configuration(config, self.MODE)
			self.tdi = self.config.CONFIG["TDI"][0]
			self.tdo = self.config.CONFIG["TDO"][0]
			self.tms = self.config.CONFIG["TMS"][0]
			self.clk = self.config.CONFIG["CLK"][0]
		
		GPIO.__init__(self)
		self.TDILow()
		self.TMSLow()
		self.ClockLow()

	def TDIHigh(self):
		"""
		Sets the TDI pin high.
		"""
		self.PinHigh(self.tdi)

	def TDILow(self):
		"""
		Sets the TDI pin low.
		"""
		self.PinLow(self.tdi)

	def ReadTDO(self):
		"""
		Reads the current status of the TDO pin.
		"""
		return self.GetPin(self.tdo)

	def TMSHigh(self):
		"""
		Sets the TMS pin high.
		"""
		self.PinHigh(self.tms)

	def TMSLow(self):
		"""
		Sets the TMS pin low.
		"""
		self.PinLow(self.tms)

	def ClockLow(self):
		"""
		Sets the clock pin low.
		"""
		self.PinLow(self.clk)
	
	def ClockHigh(self):
		"""
		Sets the clock pin high.
		"""
		self.PinHigh(self.clk)

	def Clock(self, n=1):
		"""
		Toggles n number of clock cycles.

		@n - Number of clock cycles to send, defaults to 1.
		"""
		for i in range(0, n):
			self.ClockHigh()
			self.ClockLow()

class SpeedTest(Gumbi):
	"""
	Tests the speed of the PC to Gumbi interface.
	"""

	def __init__(self, count):
		"""
		Class constructor.

		@count - Number of bytes to send during the speed test.

		Returns None.
		"""
		Gumbi.__init__(self)
		self.data = ''
		self.count = count
		self.SetMode(self.SPEEDTEST)

	def _test(self):
		"""
		Sends the byte count and reads the data. For internal use only.
		"""
		self.Write(self.Pack32(self.count))
		self.data = self.Read(self.count)

	def Go(self):
		"""
		Runs the speed test.

		Returns the number of seconds it took to transfer self.count bytes.
		"""
		self.StartTimer()
		self._test()
		return self.StopTimer()

	def Validate(self):
		"""
		Validates the received data.

		Returns True if all data was received properly.
		Returns False if data was corrupted.
		"""
		retval = True
		for byte in self.data:
			if byte != self.DUMMY_BYTE:
				retval = False
				break
		return retval

class TransferTest(Gumbi):
	"""
	Test the two-way transfer speed and validates data integrity.
	"""

	XFER_SIZE = 128

	def __init__(self):
		"""
		Class contstructor.
		"""
		self.data = ''
		Gumbi.__init__(self)
		self.SetMode(self.XFER)

	def _xfer(self):
		"""
		Performs the actual data transfer. For internal use only.
		"""
		self.Write(self.DUMMY_BYTE * self.XFER_SIZE)
		self.data = self.Read(self.XFER_SIZE)

	def Go(self):
		"""
		Runs and times the data transfer.

		Returns the number of seconds elapsed during the transfer.
		"""
		self.StartTimer()
		self._xfer()
		return self.StopTimer()

	def Validate(self):
		"""
		Validates the data recieved back from the transfer. Must be called after Go().

		Returns True if data is valid, False if invalid.
		"""
		retval = True
		if len(self.data) >= self.XFER_SIZE:
			for i in range(0, self.XFER_SIZE):
				if self.data[i] != self.DUMMY_BYTE:
					retval = False
					break
		else:
			retval = False

		return retval

class Info(Gumbi):
	"""
	Class to retrieve current Gumbi board information.
	"""

	def Info(self):
		"""
		Returns an array of human-readable board information (version, pin count, etc).
		"""
		data = []

		self.SetMode(self.INFO)
		while True:
			line = self.ReadText()
			if line == self.ACK:
				break
			else:
				data.append(line)
		return data

class Identify(Gumbi):
	"""
	Class to obtain the Gumbi board ID.
	"""

	def Identify(self):
		"""
		Returns the board ID, as reported by the Gumbi board.
		"""
		self.SetMode(self.ID)
		return self.ReadText()

class Ping(Gumbi):
	"""
	Class to perform a ping test to ensure the Gumbi board is operational.
	"""

	def Ping(self):
		"""
		Returns True if the board was successfully pinged. Raises an exception on error.
		"""
		self.SetMode(self.PING)
		return self.ReadAck()

class ParallelFlash(Gumbi):
	"""
	Class for interfacing with parallel memory devices.
	"""

	MODE = "PNORFLASH"
	
	def __init__(self, config):
		"""
		Class constructor.
		"""
		self.config = Configuration(config, self.MODE)
		Gumbi.__init__(self)
		self.SetMode(self.PNORFLASH)

def SPIFlash(Gumbi):
	"""
	Class for interfacing with SPI flash memory devices.
	"""
	MODE = "SPIFLASH"

	def __init__(self, config):
		"""
		Class constructor.
		"""
		self.config = Configuration(config, self.MODE)
		Gumbi.__init__(self)
		self.SetMode(self.SPIFLASH)

def SPIEEPROM(Gumbi):
	"""
	Class for interfacing with SPI EEPROM devices.
	"""

	MODE = "SPIEEPROM"
	
	def __init__(self, config):
		"""
		Class constructor.
		"""
		self.config = Configuration(config, self.MODE)
		Gumbi.__init__(self)
		self.SetMode(self.SPIPROM)

def I2CEEPROM(Gumbi):
	"""
	Class for interfacing with I2C EEPROM devices.
	"""
	
	MODE = "I2CEEPROM"

	def __init__(self, config):
		"""
		Class constructor.
		"""
		self.config = Configureation(config, self.MODE)
		Gumbi.__init__(self)
		self.SetMode(self.I2CPROM)


if __name__ == '__main__':
#	try:

		info = Info()
		for line in info.Info():
			print line
		info.Close()

#		p = PinCount()
#		print "Pin Count: %d" % p.Count()
#		p.Close()

#		xfer = TransferTest()
#		xfer.Go()
#		print "Valid?", xfer.Validate()
#		xfer.Close()

#		speed = SpeedTest(0x40000)
#		print "Speed test finished in", speed.Go(), "seconds."
#		print "Data valid:", speed.Validate()
#		print "Data length:", len(speed.data)
#		open("data.bin", "w").write(speed.data)
#		speed.Close()

#		gpio = GPIO()
#		gpio.PinLow(1)
#		time.sleep(10)
#		gpio.Close()

		flash = ParallelFlash(config="config/39SF020.conf")
#		print "Writing flash..."
#		flash.WriteChip(0, "\xcc")
		print "Reading flash..."
		flash.StartTimer()
		data = flash.ReadChip(0, 1024)
		t = flash.StopTimer()
		flash.Close()
		print "Read 0x%X bytes of flash data in %f seconds" % (len(data), t)
		open("flash.bin", "w").write(data)

#	except Exception, e:
####		print "Error:", e
