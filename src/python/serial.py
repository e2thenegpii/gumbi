from modes import GPIO
from gumbi import Configuration

class SPI(GPIO):
	"""
	Class for interfacing with SPI devices.
	TODO: Make this subclassed from GPIO.
	"""

	MODE = "SPI"

	def __init__(self, config=None):
		"""
		Class constructor.
	
		@config - Path to configuration file.

		Returns None.
		"""
		self.config = Configuration(config, self.MODE)
		GPIO.__init__(self)
		self.SetMode(self.SPI)

	def Start(self):
		self.WriteBytes(self.config.Pack(self.START, 0, 0))
		self.ReadAck()
		self.ReadAck()

	def Stop(self):
		self.WriteBytes(self.config.Pack(self.STOP, 0, 0))
		self.ReadAck()
		self.ReadAck()

	def _exit(self):
		"""
		Exit SPI mode. For internal use only.
		"""
		self.WriteBytes(self.config.Pack(self.EXIT, 0, 0))
		self.ReadAck()
		self.ReadAck()

class I2C(GPIO):
	"""
	Class for interfacing with I2C devices.
	TODO: Make this subclassed from GPIO.
	"""
	
	MODE = "I2C"

	def __init__(self, config=None):
		"""
		Class constructor.

		@config - Path to configuration file.

		Returns None.
		"""
		self.config = Configuration(config, self.MODE)
		Gumbi.__init__(self)
		self.SetMode(self.I2C)

	def _exit(self):
		"""
		Exit I2C mode. For internal use only.
		"""
		self.WriteBytes(self.config.Pack(self.EXIT, 0, 0))
		self.ReadAck()
		self.ReadAck()

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

	def WriteBits(self, data):
		"""
		Clocks data into TDI.
		"""
		for bit in data:
			if bit:
				self.PinHigh(self.tdi, True)
			else:
				self.PinLow(self.tdi, True)
			self.PinHigh(self.clock, True)
			self.PinLow(self.clock, True)

		self.FlushBuffer()

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
