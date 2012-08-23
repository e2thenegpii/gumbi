import os
from gumbi import Gumbi

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

		PINS		The pin count of the target chip. If this is defined,	0
				the chip pins will automatically be mapped to the 
				pins on the Gumbi board (i.e., on an 8 pin chip, chip 
				pin 1 will be connected to Gumbi pin 1, chip pin 8 will
				be connected to Gumbi pin 64). If this is not defined,
				all specified pins (address, data, CE, etc) will be
				considered absolute pin numbers on the Gumbi board.

		VOLTAGE		The voltage regulator to enable. This value may be	0
				any valid value accepted by Gumbi.SetVoltage. If not
				specified, the currently enabled voltage regulator will
				be used.

	Values in the CONFIG dict can also be viewed/modified using the GetSetting() and
	SetSetting() methods.

	If used, this class instance must be called prior to invoking Gumbi.SetMode().
	"""

	INCLUDE = "INCLUDE"

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
		# These are not part of the config structure that gets pushed to the Gumbi board
		"PINS"		: [0],
		"VOLTAGE"	: [None]
	}
	
	def __init__(self, config, mode, port=None):
		"""
		Class initializer. Must be called BEFORE Gumbi.SetMode so that it can retrieve the current pin count from the Gumbi board.

		@config - Path to the configuration file.
		@mode   - The expected MODE value in the configuration file.

		Returns None.
		"""
		self.config = config
		self.cmode = mode
		self.package_pins = 0
		self.pins_shifted = False
		
		Gumbi.__init__(self, port=port)

		# Get the number of available pins on the Gumbi board
		self.num_pins = self.PinCount()

		# Parse the configuration file/dict
		self._parse_config()

		# If a voltage was specified in the config file, set it
		if self.CONFIG["VOLTAGE"][0] is not None:
			self.SetVoltage(self.CONFIG["VOLTAGE"][0])
		
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
		if pin != self.UNUSED:

			# If the number of pins in the target package was specified in the config file,
			# then treat the pin numbers as relative to the package type.
			if self.num_pins > 0 and self.package_pins > 0 and pin > (self.package_pins / 2):
				pin += (self.num_pins - self.package_pins)

			pin = self.Pin2Real(pin)
	
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
		If the specified config value is a dict, populate self.CONFIG with the contents of the config dict.
		Else, call _parse_config_file to treat config as a path to a configuration file.
		"""
		if type(self.config) == type({}):
			for key,value in self.config.iteritems():
				if type(value) != type([]):
					self.CONFIG[key] = [value]
				else:
					 self.CONFIG[key] = value
		else:
			self._parse_config_file()
		
		if self.CONFIG.has_key("PINS"):
			self.package_pins = self.CONFIG["PINS"][0]

	def _parse_config_file(self):
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
					if key == self.INCLUDE:
						filepath = os.path.dirname(config)
						filename = "%s%s" % (value, os.path.splitext(config)[1])
						self._parse_config(os.path.join(*[filepath, filename]))
					else:
						self.CONFIG[key] = value

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
		Automatically called by Gumbi.Write, Gumbi.Read and Gumbi.ExecuteCommand.
		
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



