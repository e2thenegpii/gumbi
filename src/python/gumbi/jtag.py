from modes import GPIO
from gumbi import Configuration

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
			self.tdi = self.config.GetSetting("TDI")[0]
			self.tdo = self.config.GetSetting("TDO")[0]
			self.tms = self.config.GetSetting("TMS")[0]
			self.clk = self.config.GetSetting("CLK")[0]
		
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
		return self.ReadPin(self.tdo)

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
				self.PinHigh(self.tdi)
			else:
				self.PinLow(self.tdi)
			self.PinHigh(self.clock)
			self.PinLow(self.clock)

	def Reset(self):
		"""
		Reset the JTAG chain.
		"""
		self.PinHigh(self.tms)
		self.Clock(5)

	def Clock(self, n=1):
		"""
		Toggles n number of clock cycles.

		@n - Number of clock cycles to send, defaults to 1.
		"""
		for i in range(0, n):
			self.PinHigh(self.clk)
			self.PinLow(self.clk)

