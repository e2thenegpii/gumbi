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

	def ToggleClock(self, n=1):
		"""
		Toggles the SPI clock.

		@n - Number of times to toggle the clock. Defaults to 1.

		Returns None.
		"""
		for i in range(0, n):
			self.ClockActive()
			self.ClockIdle()

	def ClockIdle(self):
		"""
		Sets the SPI clock to its idle position.

		Returns None.
		"""
		if self.cpol == 0:
			self.PinLow(self.clk)
		else:
			self.PinHigh(self.clk)


	def ClockActive(self):
		"""
		Sets the SPI clock to its active position.
		
		Returns None.
		"""
		if self.cpol == 0:
			self.PinHigh(self.clk)
		else:
			self.PinLow(self.clk)

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
					self.PinHigh(self.mosi)
				else:
					self.PinLow(self.mosi)
				self.ToggleClock(1)

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
