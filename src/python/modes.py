from gumbi import *

class Parallel(Gumbi):
	"""
	Class for interfacing with parallel devices.
	"""

	MODE = "PARALLEL"
	
	def __init__(self, config):
		"""
		Class constructor.
		"""
		self.config = Configuration(config, self.MODE)
		Gumbi.__init__(self)
		self.SetMode(self.PARALLEL)
	
	def _exit(self):
		"""
		Exit parallel mode.
		"""
		self.WriteBytes(self.config.Pack(self.EXIT, 0, 0))
		self.ReadAck()
		self.ReadAck()

class SPI(Gumbi):
	"""
	Class for interfacing with SPI devices.
	"""
	MODE = "SPI"

	def __init__(self, config):
		"""
		Class constructor.
		"""
		self.config = Configuration(config, self.MODE)
		Gumbi.__init__(self)
		self.SetMode(self.SPI)

	def _exit(self):
		"""
		Exit SPI mode.
		"""
		self.WriteBytes(self.config.Pack(self.EXIT, 0, 0))
		self.ReadAck()
		self.ReadAck()

class I2C(Gumbi):
	"""
	Class for interfacing with I2C devices.
	"""
	
	MODE = "I2C"

	def __init__(self, config):
		"""
		Class constructor.
		"""
		self.config = Configureation(config, self.MODE)
		Gumbi.__init__(self)
		self.SetMode(self.I2C)

	def _exit(self):
		"""
		Exit I2C mode.
		"""
		self.WriteBytes(self.config.Pack(self.EXIT, 0, 0))
		self.ReadAck()
		self.ReadAck()

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
		Exits GPIO mode.
		"""
		self.WriteBytes(self.PackBytes([self.EXIT, 0]))
		self.ReadAck()

	def PinHigh(self, pin):
		"""
		Sets the specified pin high.
		"""
		self.WriteBytes(self.PackBytes([self.HIGH, self.Pin2Real(pin)]))
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
		self.WriteBytes(self.PackBytes([self.LOW, self.Pin2Real(pin)]))
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
		self.WriteBytes(self.PackBytes([self.READ, self.Pin2Real(pin)]))
		return ord(self.ReadBytes()[0])

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
