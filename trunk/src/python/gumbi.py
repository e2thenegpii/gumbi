#!/usr/bin/env python

import serial
import struct
import time

class Gumbi:
	"""
	Primary gumbi class. All other classes should be subclassed from this.
	"""

	ACK = "A"
	NACK = "N"
	BAUD = 9600
	DEFAULT_PORT = '/dev/ttyUSB0'
	MAX_PINS = 128
	RESET_LEN = 1024
	UNUSED = 0xFF
	TEST_BYTE = "\xFF"

	NOP = 0
	PFLASH = 1
	SPIFLASH = 2
	SPIEEPROM = 3
	I2CEEPROM = 4
	PING = 5
	INFO = 6
	SPEED = 7
	GPIO = 8
	ID = 9

	EXIT = 0
	READ = 1
	WRITE = 2
	ERASE = 3
	HIGH = 4
	LOW = 5

	MODE_KEY = "MODE"
	MODE_VALUE = None

	def __init__(self, port=None, new=True):
		"""
		Class constructor, calls self._open().

		@port - Gumbi serial port.
		@new  - Set to False to not open a connection to the Gumbi board.
		"""
		self.ts = 0
		self.serial = None
		if new:
			self._open(port)

	def _open(self, port):
		"""
		Opens a connection to the Gumbi board.
		"""
		if port is None:
			port = self.DEFAULT_PORT
		self.serial = serial.Serial(port, self.BAUD)

	def _close(self):
		"""
		Closes the connection with the Gumbi board.
		"""
		self.serial.close()

	def _parse_config_line(self, line):
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
						pass
			else:
				try:
					value = int(value)
				except:
					pass
		return (key, value)

	def ConfigMode(self, config):
		"""
		Returns the mode specified in a configuration file.

		@config - Configuration file path.

		Returns the mode on success. Returns None on failure.
		"""
		for line in open(config).readlines():
			(key, value) = self._parse_config_line(line)
			if key == self.MODE_KEY:
				return value
		return None

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
		return (pin - 1)

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
		return ("\x00" * count)

	def ReadAck(self):
		"""
		Reads an ACK/NACK from the Gumbi board. Returns True on ACK, raises an exception on NACK.
		"""
		if self.Read(1) != self.ACK:
			raise Exception(self.ReadText())
		return True

	def SetMode(self, mode):
		"""
		Puts the Gumbi board in the specified mode.
		"""
		self.Write(self.PackByte(mode))

	def ReadText(self):
		"""
		Reads and returns a new-line terminated string from the Gumbi board.
		"""
		return self.serial.readline().strip()

	def Read(self, n=1):
		"""
		Reads n bytes of data from the Gumbi board. Default n == 1.
		"""
		return self.serial.read(n)

	def Write(self, data):
		"""
		Sends data to the Gumbi board and verifies acknowledgement.
		"""
		self.serial.write(data)
		self.ReadAck()

	def Reset(self):
		"""
		Resets the communications stream with the Gumbi board.
		"""
		self.serial.write(self.PackByte(self.EXIT))
		for i in range(0, self.RESET_LEN):
			self.SetMode(self.NOP)

	def Close(self):
		"""
		Closes the connection with the Gumbi board.
		"""
		return self._close()

class GPIO(Gumbi):
	"""
	Class to provide raw read/write access to all I/O pins.
	"""

	def __init__(self, port=None):
		"""
		Class constructor.
		"""
		Gumbi.__init__(self, port)
		self.SetMode(self.GPIO)

	def _exit(self):
		"""
		Exits the Gumbi board from GPIO mode.
		"""
		self.Write(self.PackBytes([self.EXIT, 0]))

	def PinHigh(self, pin):
		"""
		Sets the specified pin high.
		"""
		self.Write(self.PackBytes([self.HIGH, self.Pin2Real(pin)]))

	def PinLow(self, pin):
		"""
		Sets the specified pin low.
		"""
		self.Write(self.PackBytes([self.LOW, self.Pin2Real(pin)]))

	def ReadPin(self, pin):
		"""
		Reads and returns the value of the specified pin.
		High == 1, Low == 0.
		"""
		self.Write(self.PackBytes([self.READ, self.Pin2Real(pin)]))
		return ord(self.Read(1))

	def Close(self):
		"""
		Exits GPIO mode, closes the Gumbi board connection.
		"""
		self._exit()
		self._close()

class SpeedTest(Gumbi):

	def __init__(self, count, port=None):
		Gumbi.__init__(self, port)
		self.data = ''
		self.count = count
		self.SetMode(self.SPEED)

	def _test(self):
		self.Write(self.Pack32(self.count))
		self.data = self.Read(self.count)

	def Go(self):
		self.StartTimer()
		self._test()
		return self.StopTimer()

	def Validate(self):
		retval = True
		for byte in self.data:
			if byte != self.TEST_BYTE:
				retval = False
				break
		return retval

class Info(Gumbi):

	def Info(self):
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

	def Identify(self):
		self.SetMode(self.ID)
		return self.ReadText()

class Ping(Gumbi):

	def Ping(self):
		self.SetMode(self.PING)
		return self.ReadAck()

class ParallelFlash(Gumbi):

	MODE_VALUE = "PARALLEL"
	CONFIG = {
		"TOE"		: [0],
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
		"RST"		: [Gumbi.UNUSED, 0]
	}
	
	def __init__(self, config=None, toe=0, address=[], data=[], vcc=[], gnd=[], ce=None, we=None, oe=None, be=None, by=None, wp=None, rst=None, port=None):
		if config is None:
			self.CONFIG["TOE"] = [toe]
			self.CONFIG["ADDRESS"] = self._convert_pin_array(address)
			self.CONFIG["DATA"] = self._convert_pin_array(data)
			self.CONFIG["VCC"] = self._convert_pin_array(vcc)
			self.CONFIG["GND"] = self._convert_pin_array(gnd)
			self.CONFIG["CE"] = self._convert_control_pin(ce)
			self.CONFIG["WE"] = self._convert_control_pin(we)
			self.CONFIG["OE"] = self._convert_control_pin(oe)
			self.CONFIG["BE"] = self._convert_control_pin(be)
			self.CONFIG["BY"] = self._convert_control_pin(by)
			self.CONFIG["WP"] = self._convert_control_pin(wp)
			self.CONFIG["RST"] = self._convert_control_pin(rst)
		else:
			self.ReadConfig(config)

		Gumbi.__init__(self, port)
		self.SetMode(self.PFLASH)

	def _convert_control_pin(self, cp):
		cpc = (self.UNUSED, 0)
		if cp is not None and len(cp) > 0:
			if len(cp) == 1:
				cpc = (self.Pin2Real(cp[0]), 0)
			else:
				cpc = (self.Pin2Real(cp[0]), cp[1])
		return cpc

	def _convert_pin_array(self, pins):
		for i in range(0, len(pins)):
			pins[i] = self.Pin2Real(pins[i])
		return pins

	def _pack_pins(self, pins):
		pd = self.PackBytes(pins)
		pd += self.PackFiller(self.MAX_PINS - len(pins))
		return pd

	def _struct(self, action, start, count):
		data = self.PackByte(action)
		data += self.Pack32(start)
		data += self.Pack32(count)
		data += self.PackByte(self.CONFIG["TOE"][0])
		data += self.Pack16(len(self.CONFIG["ADDRESS"]))
		data += self.Pack16(len(self.CONFIG["DATA"]))
		data += self.Pack16(len(self.CONFIG["VCC"]))
		data += self.Pack16(len(self.CONFIG["GND"]))
		data += self._pack_pins(self.CONFIG["ADDRESS"])
		data += self._pack_pins(self.CONFIG["DATA"])
		data += self._pack_pins(self.CONFIG["VCC"])
		data += self._pack_pins(self.CONFIG["GND"])
		data += self.PackBytes(self.CONFIG["CE"])
		data += self.PackBytes(self.CONFIG["WE"])
		data += self.PackBytes(self.CONFIG["OE"])
		data += self.PackBytes(self.CONFIG["BE"])
		data += self.PackBytes(self.CONFIG["BY"])
		data += self.PackBytes(self.CONFIG["WP"])
		data += self.PackBytes(self.CONFIG["RST"])
		return data

	def ReadConfig(self, config):
		mode_name = self.ConfigMode(config)
		if mode_name != self.CONFIG_MODE:
			raise Exception("Wrong mode specified in configuration file. Got '%s', expected '%s'." % (mode_name, self.CONFIG_MODE))

		for line in open(config).readlines():
			(key, value) = self._parse_config_line(line)
			if key is not None and value is not None:
				if self.CONFIG.has_key(key):
					self.CONFIG[key] = value
		for key, value in self.CONFIG.iteritems():
			print key, "=", value

	def ReadFlash(self, start, count):
		data = self._struct(self.READ, start, count)
		self.Write(data)
		self.ReadAck()
		return self.Read(count)

	def WriteFlash(self, addr, data):
		self.Write(self._struct(self.WRITE, start, len(data)))
		self.Write(data)
		return self.ReadAck()


if __name__ == '__main__':
	try:

		info = Info()
		for line in info.Info():
			print line
		print ""
		info.Close()

		flash = ParallelFlash(config="config/39SF020.conf")
		print "Reading flash..."
		flash.StartTimer()
		data = flash.ReadFlash(0, 0x40000)
		t = flash.StopTimer()
		flash.Close()

		print "Read 0x40000 bytes in", t, "seconds"
		open("flash.bin", "w").write(data)
	except Exception, e:
		print "Error:", e
