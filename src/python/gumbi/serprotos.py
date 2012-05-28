from modes import GPIO
from gumbi import Configuration

class SPI(GPIO):
	"""
	Class for interfacing with SPI devices.
	"""

	MODE = "SPI"

	def __init__(self, config=None, miso=0, mosi=0, ss=0, clk=0, cpol=0, cpha=0):
		"""
		Class constructor.
	
		@config - Path to configuration file.

		Returns None.
		"""
		self.miso = miso
		self.mosi = mosi
		self.ss = ss
		self.clk = clk
		self.cpol = cpol
		self.cpha = cpha

		if config is not None:
			self.config = Configuration(config, self.MODE)
			self.miso = self.config.GetSetting("MISO")[0]
			self.mosi = self.config.GetSetting("MOSI")[0]
			self.ss = self.config.GetSetting("SS")[0]
			self.clk = self.config.GetSetting("CLK")[0]
			self.cpol = self.config.GetSetting("CPOL")[0]
			self.cpha = self.config.GetSetting("CPHA")[0]

			# CPOL and CPHA are optional; default to 0
			if self.cpol is None:
				self.cpol = 0
			if self.cpha is None:
				self.cpha = 0

		GPIO.__init__(self)
		self.ClockIdle()

	def ToggleClock(self, n=1, buffer=False):
		"""
		Toggles the SPI clock.

		@n - Number of times to toggle the clock. Defaults to 1.

		Returns None.
		"""
		for i in range(0, n):
			self.ClockActive(buffer)
			self.ClockIdle(buffer)

	def ClockIdle(self, buffer=False):
		"""
		Sets the SPI clock to its idle position.

		@buffer - Set to True to buffer the action.
		
		Returns None.
		"""
		if self.cpol == 0:
			self.PinLow(self.clk, buffer)
		else:
			self.PinHigh(self.clk, buffer)


	def ClockActive(self, buffer=False):
		"""
		Sets the SPI clock to its active position.

		@buffer - Set to True to buffer the action.
		
		Returns None.
		"""
		if self.cpol == 0:
			self.PinHigh(self.clk, buffer)
		else:
			self.PinLow(self.clk, buffer)

	def Start(self):
		"""
		Starts an SPI transaction.
		
		Returns None.
		"""
		self.PinLow(self.ss)

	def Stop(self):
		"""
		Stops an SPI transaction.
		
		Returns None.
		"""
		self.PinHigh(self.ss)

	def Send(self, data):
		"""
		Sends data over the SPI bus.

		@data - Bytes of data to send.

		Returns None.
		"""
		for byte in data:
			i = 7
			while i >= 0:
				if (byte & (1 << i)) > 0:
					self.PinHigh(self.mosi, True)
				else:
					self.PinLow(self.mosi, True)
				self.ToggleClock(1, True)
		self.FlushBuffer()

	def Receive(self, n=1):
		"""
		Reads data from the SPI bus.

		@n - Number of bytes to read. Defaults to 1.

		Returns a string of bytes read from the SPI bus.
		"""
		data = ''

		for i in range(0, n):

			j=7
			while j >= 0:
				if cpol == cpha:
					self.ClockActive(True)
					bit = self.ReadPin(self.miso)
					self.ClockIdle()
				else:
					self.ClockActive(True)
					self.ClockIdle(True)
					bit = self.ReadPin(self.miso)

				if bit:
					byte |= (1 << j)
				j += 1

			data += chr(byte)

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
				self.PinHigh(self.tdi, True)
			else:
				self.PinLow(self.tdi, True)
			self.PinHigh(self.clock, True)
			self.PinLow(self.clock, True)

		self.FlushBuffer()

	def Reset(self):
		"""
		Reset the JTAG chain.
		"""
		self.PinHigh(self.tms, True)
		self.Clock(5)

	def Clock(self, n=1):
		"""
		Toggles n number of clock cycles.

		@n - Number of clock cycles to send, defaults to 1.
		"""
		for i in range(0, n):
			self.PinHigh(self.clk, True)
			self.PinLow(self.clk, True)
		self.FlushBuffer()

