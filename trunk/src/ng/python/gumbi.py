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
	MAX_COMMANDS = 32
	RESET_LEN = 1024
	UNUSED = 0xFF
	NULL = "\x00"
	DUMMY_BYTE = "\xFF"

	TBP_DEFAULT = 25
	TOE_DEFAULT = 0

	NOP = 0
	PFLASH = 1
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
	HIGH = 3
	LOW = 4

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

	def _exit(self):
		"""
		Exits the Gumbi board from GPIO mode.
		"""
		self.Write(self.PackBytes([self.EXIT, 0]))
		self.ReadAck()

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
			# Multple value delimiters are: ',', ';', ':'
			value = value.strip().upper().replace(";", ",").replace(":", ",")
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
		
		return self.Read(count)

	def WriteChip(self, start, data):
		"""
		Writes a number of bytes to the target chip, beginning at the given start address.
		NOT CURRENTLY IMPLEMENTED.

		@start - Address to start writing at.
		@data  - String of data to write.

		Returns True on success, raises and exception on failure.
		"""
		self.Write(self.config.Pack(self.WRITE, start, len(data)))
		# Receive the ACK indicating the provided configuration is valid
		self.ReadAck()
		# Receive the ACK indicating that the specified action is valid
		self.ReadAck()
	
		# TODO: Send data 64 bytes at a time until all data is sent	
		self.Write(data)

		# DEBUG
		while True:
			try:
				text = self.ReadText()
				print text
				if text == self.ACK:
					break
			except:
				pass
		#END DEBUG

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
		self._exit()
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
		"COMMANDS"	: [],
		"SDA"		: [Gumbi.UNUSED, 0],
		"CLK"		: [Gumbi.UNUSED, 0],
		"SS"		: [Gumbi.UNUSED, 0],
		"MISO"		: [Gumbi.UNUSED, 0],
		"MOSI"		: [Gumbi.UNUSED, 0],
		# These are not part of the config strcture that gets pushed to the Gumbi board
		"PINS"		: [0]
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
		self.CONFIG["SDA"] = self._convert_control_pin(self.CONFIG["SDA"])
		self.CONFIG["CLK"] = self._convert_control_pin(self.CONFIG["CLK"])
		self.CONFIG["SS"] = self._convert_control_pin(self.CONFIG["SS"])
		self.CONFIG["MISO"] = self._convert_control_pin(self.CONFIG["MISO"])
		self.CONFIG["MOSI"] = self._convert_control_pin(self.CONFIG["MOSI"])

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

	def _pack_commands(self, commands):
		pd = self.PackDWords(commands)
		pd += self.PackFiller((self.MAX_COMMANDS * 4) - len(pd))
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
				self.CONFIG[key] = value

		self.package_pins = self.CONFIG["PINS"][0]

	def SetCommand(self, commands):
		"""
		Sets the list of commands to execute prior to running an action.
		"""
		if commands is not None and self.CONFIG.has_key(commands):
			self.CONFIG["COMMANDS"] = self.CONFIG[commands]

	def Pack(self, action, start, count, commands=[]):
		"""
		Packs the configuration data into a string of bytes suitable for transmission to the Gumbi board.
		
		@action   - Action (READ, WRITE, EXIT, etc).
		@start    - Start address.
		@count    - Number of bytes.
		@commands - A list of commands to write to the chip prior to performing the action.

		Returns a packed data string.
		"""
		self._shift_pins()
		data = self.PackByte(action)
		data += self.Pack32(start)
		data += self.Pack32(count)
		data += self.PackByte(self.CONFIG["TOE"][0])
		data += self.PackByte(self.CONFIG["TBP"][0])
		data += self.Pack16(len(self.CONFIG["ADDRESS"]))
		data += self.Pack16(len(self.CONFIG["DATA"]))
		data += self.Pack16(len(self.CONFIG["VCC"]))
		data += self.Pack16(len(self.CONFIG["GND"]))
		data += self.PackByte(len(self.CONFIG["COMMANDS"]))
		data += self._pack_pins(self.CONFIG["ADDRESS"])
		data += self._pack_pins(self.CONFIG["DATA"])
		data += self._pack_pins(self.CONFIG["VCC"])
		data += self._pack_pins(self.CONFIG["GND"])
		data += self._pack_commands(self.CONFIG["COMMANDS"])
		data += self.PackBytes(self.CONFIG["CE"])
		data += self.PackBytes(self.CONFIG["WE"])
		data += self.PackBytes(self.CONFIG["OE"])
		data += self.PackBytes(self.CONFIG["BE"])
		data += self.PackBytes(self.CONFIG["BY"])
		data += self.PackBytes(self.CONFIG["WP"])
		data += self.PackBytes(self.CONFIG["RST"])
		data += self.PackBytes(self.CONFIG["SDA"])
		data += self.PackBytes(self.CONFIG["CLK"])
		data += self.PackBytes(self.CONFIG["SS"])
		data += self.PackBytes(self.CONFIG["MISO"])
		data += self.PackBytes(self.CONFIG["MOSI"])
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
		self.ReadAck()

	def PinsHigh(self, pins):
		"""
		Sets the specified pins high.
		"""
		for pin in pins:
			self.PinHigh(pin)

	def PinLow(self, pin):
		"""
		Sets the specified pin low.
		"""
		self.Write(self.PackBytes([self.LOW, self.Pin2Real(pin)]))
		self.ReadAck()

	def PinsLow(self, pins):
		"""
		Sets the specified pins low.
		"""
		for pin in pins:
			self.PinLow(pin)

	def ReadPin(self, pin):
		"""
		Reads and returns the value of the specified pin.
		High == 1, Low == 0.
		"""
		self.Write(self.PackBytes([self.READ, self.Pin2Real(pin)]))
		return ord(self.Read()[0])

	def ReadPins(self, pins):
		"""
		Reads and returns the value of the specified pins.
		High == 1, Low == 0.
		"""
		data = []
		for pin in pins:
			data.append(self.ReadPin(pin))
		return data

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

	MODE = "PARALLEL"
	
	def __init__(self, config):
		"""
		Class constructor.
		"""
		self.config = Configuration(config, self.MODE)
		Gumbi.__init__(self)
		self.SetMode(self.PARALLEL)

	def id(self):
		self.config.SetCommand("ID")
		data = self.ReadChip(0x00, 2)
		vendor = ord(data[0])
		product = ord(data[1])
		return (vendor, product)

	def read(self, address, count):
		return self.ReadChip(address, count)

	def write(self, address, data):
		self.config.SetCommand("WRITE")
		return self.WriteChip(address, data)

	def erase(self):
		self.config.SetCommand("ERASE")
		self.WriteChip(0x00, "\xFF")

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

#		flash = ParallelFlash(config="config/39SF020.conf")
#		print "Writing flash..."
#		flash.WriteChip(0, "\xcc")
#		flash.Close()

		flash = ParallelFlash(config="config/39SF020.conf")
		print "Reading flash..."
		flash.StartTimer()
		data = flash.ReadChip(0, 1024)
		t = flash.StopTimer()
		flash.Close()
		print "Read 0x%X bytes of flash data in %f seconds" % (len(data), t)
		open("flash.bin", "w").write(data)

#	except Exception, e:
####		print "Error:", e
