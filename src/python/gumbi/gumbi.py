import struct
import time
import sys
from rawhid import RawHID
	
class Gumbi:
	"""
	This is the primary Python class used to interface with the Gumbi board and handles 
	the communication with the hardware. In most cases you will not need to interface with 
	this class directly, but rather through a subclass.

	Since all classes that interact with the Gumbi board should be subclassed from this class,
	all the methods in the Gumbi class should be available through any subclass, unless the
	subclass has overridden the method (with few exceptions, overriding Gumbi methods is undesirable).
	"""

	VID = 0xFFFF
	PID = 0x1337
	ACK = "GUMBIACK"
	NACK = "GUMBINACK"
	MAX_PINS = 128
	MAX_COMMANDS = 32
	MAX_GPIO_COMMANDS = 31
	MAX_GPIO_BUFFER = 62
	RESET_LEN = 1024
	UNUSED = 0xFF
	NULL = "\x00"
	DUMMY_BYTE = "\xFF"
	BLOCK_SIZE = 64

	TBP_DEFAULT = 25
	TOE_DEFAULT = 0

	NOP = 0
	PARALLEL = 1
	PING = 2
	INFO = 3
	SPEEDTEST = 4
	GPIO = 5
	GID = 6
	XFER = 7
	PINCOUNT = 8
	SCANBUS = 9

	EXIT = 0
	READ = 1
	WRITE = 2
	HIGH = 3
	LOW = 4
	COMMAND = 5

	MODE_KEY = "MODE"
	MODE_VALUE = None

	def __init__(self, new=True):
		"""
		Class constructor, opens a connection to the gumbi board.

		@new  - Set to False to not open a connection to the Gumbi board.

		Returns None.
		"""
		self.ts = 0
		self.num_pins = 0
		self.hid = RawHID(bs=self.BLOCK_SIZE)
		if new:
			self._open()

	def _open(self):
		"""
		Opens a connection to the Gumbi board. For internal use only.
		"""
		self.hid.open(self.VID, self.PID)

	def _exit(self):
		"""
		Place holder _exit method, called by Close(). 

		This should be overridden by the subclass so that the appropriate exit 
		message may be sent to exit the given mode implemented by the subclass.

		Returns None.
		"""
		return None

	def _close(self):
		"""
		Closes the connection with the Gumbi board. For internal use only.
		"""
		self.hid.close()

	def StartTimer(self):
		"""
		Starts a timer.

		Returns None.
		"""
		self.ts = time.time()

	def StopTimer(self):
		"""
		Stops the timer started by StartTimer().

		Returns the seconds elapsed since StartTimer() was called.
		"""
		return (time.time() - self.ts)

	def Pin2Real(self, pin):
		"""
		Converts user-supplied pin numbers (index 1) to Gumbi board pin numbers (index 0).

		@pin - User supplied pin number.

		Returns the Gumbi board pin number.
		"""
		if pin is not None and pin > 0:
			return (pin - 1)
		else:
			return pin

	def Pack32(self, value):
		"""
		Packs a 32-bit value for transmission to the Gumbi board.

		@value - A 32-bit value to pack.

		Returns a 4 byte string.
		"""
                return struct.pack("<I", value)

        def Pack16(self, value):
		"""
		Packs a 16-bit value for transmission to the Gumbi board.

		@value - A 16-bit value to pack.

		Returns a 2 byte string.
		"""
                return struct.pack("<H", value)

        def PackByte(self, value):
		"""
		Packs an 8-bit value for transmission to the Gumbi board.

		@value - An 8-bit value to pack.

		Returns a 1 byte string.
		"""
                return chr(value)

	def PackDWords(self, data):
		"""
		Packs an array of 32-bit values for transmission to the Gumbi board.

		@data - An array of 32-bit values to pack.

		Returns a string len(data)*4 bytes long.
		"""
		pdata = ''
		for dword in data:
			pdata += self.Pack32(dword)
		return pdata

        def PackBytes(self, data):
		"""
		Packs an array of 8-bit values for transmission to the Gumbi board.

		@data - An array of 8-bit values to pack.

		Returns a string len(data) bytes long.
		"""
                pdata = ''
                for byte in data:
                        pdata += self.PackByte(byte)
                return pdata

	def PackFiller(self, count):
		"""
		Returns count filler bytes of data. Used for filling out unused arrays/structures.

		@count - Number of filler bytes required.

		Returns a string of NULL bytes.
		"""
		return (self.NULL * count)

	def ReadAck(self):
		"""
		Reads an ACK/NACK from the Gumbi board. 

		Returns True on ACK, raises an exception on NACK.
		"""
		line = self.ReadText() 
		if line != self.ACK:
			print "Instead of ack, I got:", line
			raise Exception(self.ReadText())
		return True

	def SetMode(self, mode):
		"""
		Puts the Gumbi board in the specified mode.

		@mode - One of: NOP, PARALLEL, SPI, I2C, PING, INFO, SPEEDTEST, GPIO, GID, XFER, PINCOUNT

		Returns None.
		"""
		self.WriteBytes(self.PackByte(mode))
		self.ReadAck()

	def ReadText(self):
		"""
		Reads an ASCII string from the Gumbi board.

		Returns the string read
		"""
		return self.ReadBytes().strip(self.NULL)

	def ReadBytes(self, n=None):
		"""
		Reads n bytes of data from the Gumbi board.

		@n - Number of bytes to read. If not specified, BLOCK_SIZE bytes are read.

		Returns a string of bytes received from the Gumbi board.
		"""
		data = self.hid.recv(n)
		if n is not None:
			data = data[0:n]

		return data

	def WriteBytes(self, data):
		"""
		Sends data to the Gumbi board.
		
		@data - String of bytes to send.

		Returns None.
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

		Returns None.
		"""
		self.WriteBytes(self.config.Pack(self.COMMAND, 0, 0))
		self.ReadAck()
		self.ReadAck()

	def PinCount(self):
		"""
		Queries the Gumbi board for the number of available I/O pins.

		Returns the number of available I/O pins.
		"""
		self.SetMode(self.PINCOUNT)
		return ord(self.ReadBytes()[0])

	def Reset(self):
		"""
		Resets the communications stream with the Gumbi board.

		Returns None.
		"""
		self.hid.send(self.PackByte(self.EXIT))
		for i in range(0, self.RESET_LEN):
			self.SetMode(self.NOP)

	def Close(self):
		"""
		Closes the connection with the Gumbi board.
		This method MUST be called or else subsequent Gumbi instances may fail.

		Returns None.
		"""
		self._exit()
		return self._close()


class Configuration(Gumbi):
	"""
	This class parses configuration files that can be used by Gumbi based code and
	applications, and builds the command structure that is sent to the Gumbi hardware. 

	Configuration files consist of KEY=VALUE pairs, one per line. Comments are also
	allowed. Example:
		
		# Timeout period, in milliseconds
		TIMEOUT=10
		# List of FOO pins
		FOO=1,2,3,4

	All data read from the configuration file will be stored in the CONFIG dictionary.
	All values are stored in the CONFIG dict as lists.

	There are some configuration values that are pre-defined in the CONFIG dict. These
	values are used to generate the configuration data structure that is passed down
	to the Gumbi board:

		KEY		DESCRIPTION						DEFAULT VALUE
		---------------------------------------------------------------------------------------
		TOE		Output Enable wait period, in uS. Used as a 		0
				general pin latch wait period. In most cases, 
				this can be 0.

		TBP		Byte Program wait period, in uS. Used as a wait		25
				period by some modes after a byte of data is written.

		ADDRESS		An ordered list of address pins. Primarily used		[]
				for parallel mode.

		DATA		An ordered list of data pins. Primarily used for	[]
				parallel mode.

		VCC		A list of pins that need to be pulled high to Vcc.	[]

		GND		A list of pins that need to be pulled low to ground.	[]

		CE		The chip enable pin, and its active state (0 is		[255, 0]
				active low, 1 is active high). This pin is asserted
				when activating a chip in parallel mode.

		WE		The write enable pin, and its active state (0 is	[255, 0]
				active low, 1 is active high). This pin is asserted
				when writing data to a chip in parallel mode.

		RE		The read enable pin, and its active state (0 is		[255, 0]
				active low, 1 is active high). This pin is asserted
				when reading data from a chip in parallel mode.


		OE		The output enable pin, and its active state (0 is	[255, 0]
				active low, 1 is active high). This pin is asserted
				when reading data from a chip in parallel mode.

		BE		The byte enable pin, and its active state (0 is		[255, 0]
				active low, 1 is active high). This pin is asserted
				if the number of defined data pins is less than or
				equal to 8 in parallel mode.

		BY		The chip busy pin, and its active state (0 is		[255, 0]
				active low, 1 is active high). This pin is polled
				before sending commands to chips in parallel mode.

		WP		The write protect pin, and its active state (0 is	[255, 0]
				active low, 1 is active high). This pin is deasserted
				in parallel mode.

		RST		The chip reset pin, and its active state (0 is		[255, 0]
				active low, 1 is active high). This pin is deasserted
				in parallel mode.

		COMMANDS	A list of commands to be executed prior to a read	[]
				or write opration. The commands will vary based on
				the selected mode of operation.

		CMDELAY		The delay period, in seconds, to wait after executing	0
				the commands listed in COMMANDS.

		RECONFIGURE	If set to 1, the Gumbi board will configure the		0
				I/O pins each time an action is received. If 0,
				the I/O pins will only be configured once.

	Values in the CONFIG dict can also be viewed/modified using the GetSetting() and
	SetSetting() methods.

	If used, this class instance must be called prior to invoking Gumbi.SetMode().
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
		"RE"		: [Gumbi.UNUSED, 0],
		"OE"		: [Gumbi.UNUSED, 0],
		"BE"		: [Gumbi.UNUSED, 0],
		"BY"		: [Gumbi.UNUSED, 0],
		"WP"		: [Gumbi.UNUSED, 0],
		"RST"		: [Gumbi.UNUSED, 0],
		"COMMANDS"	: [],
		"CMDELAY"	: [0],
		"RECONFIGURE"	: [0],
		# These are not part of the config strcture that gets pushed to the Gumbi board
		"PINS"		: [0]
	}
	
	def __init__(self, config, mode, pins=None):
		"""
		Class initializer. Must be called BEFORE SetMode so that it can retrieve the current pin count from the Gumbi board.

		@config - Path to the configuration file.
		@mode   - The expected MODE value in the configuration file.
		@pins   - Number of available I/O pins on the Gumbi board. If not specified, this is detected automatically.

		Returns None.
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
		For internal use only.
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
		For internal use only.
		"""
		if not self.pins_shifted:
			self.CONFIG["ADDRESS"] = self._convert_pin_array(self.CONFIG["ADDRESS"])
			self.CONFIG["DATA"] = self._convert_pin_array(self.CONFIG["DATA"])
			self.CONFIG["VCC"] = self._convert_pin_array(self.CONFIG["VCC"])
			self.CONFIG["GND"] = self._convert_pin_array(self.CONFIG["GND"])
			self.CONFIG["CE"] = self._convert_control_pin(self.CONFIG["CE"])
			self.CONFIG["WE"] = self._convert_control_pin(self.CONFIG["WE"])
			self.CONFIG["RE"] = self._convert_control_pin(self.CONFIG["RE"])
			self.CONFIG["OE"] = self._convert_control_pin(self.CONFIG["OE"])
			self.CONFIG["BE"] = self._convert_control_pin(self.CONFIG["BE"])
			self.CONFIG["BY"] = self._convert_control_pin(self.CONFIG["BY"])
			self.CONFIG["WP"] = self._convert_control_pin(self.CONFIG["WP"])
			self.CONFIG["RST"] = self._convert_control_pin(self.CONFIG["RST"])
			self.pins_shifted = True

	def _convert_control_pin(self, cp):
		"""
		Converts a control pin array to a valid pin offset on the Gumbi board.
		For internal use only.
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
		For internal use only.
		"""
		for i in range(0, len(pins)):
			pins[i] = self._pin2real(pins[i])
		return pins

	def _pack_pins(self, pins):
		"""
		Packs an array of pins into a data structure. For internal use only.
		"""
		pd = self.PackBytes(pins)
		pd += self.PackFiller(self.MAX_PINS - len(pins))
		return pd

	def _pack_commands(self, commands):
		"""
		Packs the CONFIG["COMMANDS"] values for transmission to the Gumbi board.
		Returns the mode on success. Returns None on failure.
		"""
		pd = self.PackDWords(commands)
		pd += self.PackFiller((self.MAX_COMMANDS * 4) - len(pd))
		return pd

	def _config_mode(self):
		"""
		Returns the mode specified in a configuration file. For internal use only.
		"""
		if self.config and self.config is not None:
			for line in open(self.config).readlines():
				(key, value) = self.ParseConfigLine(line)
				if key == self.MODE_KEY:
					return value
		return None

	def _parse_config(self):
		"""
		Parses the specified configuration file. For internal use only.
		"""
		mode_name = self._config_mode()
		if mode_name is not None and mode_name != self.cmode:
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
		What constitutes a valid command will vary based on the current Gumbi mode.

		@commands - A list of commands, or a configuration key identifier string.

		Returns None.
		"""
		if type(commands) == type([]):
			self.CONFIG["COMMANDS"] = commands
		elif commands is not None and self.CONFIG.has_key(commands):
			self.CONFIG["COMMANDS"] = self.CONFIG[commands]

	def GetSetting(self, key):
		"""
		Returns the value of the specified CONFIG dict key.

		@key - The CONFIG key name.

		Returns the key value on success, None on failure.
		"""
		value = None

		if self.CONFIG.has_key(key):
			value = self.CONFIG[key]
		return value

	def SetSetting(self, key, value):
		"""
		Sets the value for the specified CONFIG dict key.
		
		@key   - The CONFIG key name.
		@value - The CONFIG key value.

		Returns None.
		"""
		self.CONFIG[key] = value

	def Pack(self, action, start, count):
		"""
		Packs the configuration data into a strinig of bytes suitable for transmission to the Gumbi board.
		Automatically called by Gumbi.Write and Gumbi.Read.
		
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
		data += self.PackBytes(self.CONFIG["RE"])
		data += self.PackBytes(self.CONFIG["OE"])
		data += self.PackBytes(self.CONFIG["BE"])
		data += self.PackBytes(self.CONFIG["BY"])
		data += self.PackBytes(self.CONFIG["WP"])
		data += self.PackBytes(self.CONFIG["RST"])
		return data



