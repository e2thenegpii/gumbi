import struct
import time
import sys
from rawhid import RawHID
	
class Gumbi:
	"""
	This is the primary Python class used to interface with the Gumbi board and handles 
	the communication with the hardware. In most cases you will not need to interface with 
	this class directly, but rather through a subclass.
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
	BLOCK_SIZE = 64

	TBP_DEFAULT = 25
	TOE_DEFAULT = 0

	NOP = 0
	PARALLEL = 1
	SPI = 2
	I2CPROM = 3
	PING = 4
	INFO = 5
	SPEEDTEST = 6
	GPIO = 7
	GID = 8
	XFER = 9
	PINCOUNT = 10

	EXIT = 0
	READ = 1
	WRITE = 2
	HIGH = 3
	LOW = 4
	COMMAND = 5
	START = 6
	STOP = 7

	MODE_KEY = "MODE"
	MODE_VALUE = None

	def __init__(self, new=True):
		"""
		Class constructor, calls self._open().

		@new  - Set to False to not open a connection to the Gumbi board.
		"""
		self.ts = 0
		self.num_pins = 0
		self.hid = RawHID(bs=self.BLOCK_SIZE)
		if new:
			self._open()

	def _open(self):
		"""
		Opens a connection to the Gumbi board.
		"""
		self.hid.open(self.VID, self.PID)

	def _exit(self):
		"""
		Place holder _exit method. This should be overridden by the subclass so that the
		appropriate exit message may be sent to exit the given mode implemented by the subclass.
		"""
		return None

	def _close(self):
		"""
		Closes the connection with the Gumbi board.
		"""
		self.hid.close()

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
			print "Instead of ack, I got:"
			for i in line:
				print "0x%X" % ord(i)
			raise Exception(self.ReadText())
		return True

	def SetMode(self, mode):
		"""
		Puts the Gumbi board in the specified mode.
		"""
		self.WriteBytes(self.PackByte(mode))
		self.ReadAck()

	def ReadText(self):
		"""
		Reads and returns a new-line terminated string from the Gumbi board.
		"""
		return self.ReadBytes().strip(self.NULL)

	def ReadBytes(self, n=None):
		"""
		Reads n bytes of data from the Gumbi board. Default n == 1.
		"""
		return self.hid.recv(n)

	def WriteBytes(self, data):
		"""
		Sends data to the Gumbi board and verifies acknowledgement.
		"""
		self.hid.send(data)

	def Read(self, start, count):
		"""
		Reads a number of bytes from the target chip, beginning at the given start address.

		@start - Start address.
		@count - Number of bytes to read.

		Returns a string of bytes read from the chip.
		"""
		self.WriteBytes(self.config.Pack(self.READ, start, count))
	
		# Receive the ACK indicating the provided configuration is valid
		self.ReadAck()
		# Receive the ACK indicating that the specified action is valid
		self.ReadAck()
	
		return self.ReadBytes(count)

	def Write(self, start, data):
		"""
		Writes a number of bytes to the target chip, beginning at the given start address.
		NOT CURRENTLY IMPLEMENTED.

		@start - Address to start writing at.
		@data  - String of data to write.

		Returns True on success, raises and exception on failure.
		"""
		self.WriteBytes(self.config.Pack(self.WRITE, start, len(data)))
		# Receive the ACK indicating the provided configuration is valid
		self.ReadAck()
		# Receive the ACK indicating that the specified action is valid
		self.ReadAck()
	
		# Even though the RawHID class will chunk data into BLOCK_SIZE chunks for us,
		# we do it ourselves in order to wait for the ACK after each block is processed.
		tx = 0
		while tx < len(data):
			self.WriteBytes(data[tx:tx+self.BLOCK_SIZE])

			# Wait for an ACK, ignoring timeout exceptions (writes could take a while)
			while True:
				try:
					self.ReadAck()
					tx += self.BLOCK_SIZE
					break
				except:
					continue

		return True

	def ExecuteCommands(self):
		"""
		Runs the commands listed in self.config.CONFIG["COMMANDS"] without any further actions.
		"""
		self.WriteBytes(self.config.Pack(self.COMMAND, 0, 0))
		self.ReadAck()
		self.ReadAck()
		return True

	def PinCount(self):
		"""
		Returns the number of available I/O pins on the Gumbi board.
		"""
		self.SetMode(self.PINCOUNT)
		return ord(self.ReadBytes()[0])

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


class Configuration(Gumbi):
	"""
	This class parses configuration files that can be used by Gumbi based code and applications, and
	builds the command structure that is sent to the Gumbi hardware. 

	If used, this class instance should be called prior to invoking Gumbi.SetMode().
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
		"CMDELAY"	: [0],
		"RECONFIGURE"	: [0],
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
		self.pins_shifted = False

		if self.num_pins is None:
			Gumbi.__init__(self)
			self.num_pins = self.PinCount()
			self.Close()

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
		if not self.pins_shifted:
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
			self.pins_shifted = True

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
		if self.config and self.config is not None:
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

		if self.config and self.config is not None:
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

	def Pack(self, action, start, count):
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
		data += self.PackByte(self.CONFIG["CMDELAY"][0])
		data += self.PackByte(self.CONFIG["RECONFIGURE"][0])
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



