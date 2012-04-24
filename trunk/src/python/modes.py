from gumbi import *

class Parallel(Gumbi):
	"""
	Class for interfacing with parallel devices.
	"""

	MODE = "PARALLEL"
	
	def __init__(self, config=None):
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

	def __init__(self, config=None):
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

	def __init__(self, config=None):
		"""
		Class constructor.
		"""
		self.config = Configuration(config, self.MODE)
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

	MODE = "GPIO"
	BUFFER = ""

	def __init__(self, config=None):
		"""
		Class constructor.
		"""
		self.config = Configuration(config, self.MODE)
		Gumbi.__init__(self)
		self.SetMode(self.GPIO)
		self._set_conf_pins()

	def _set_conf_pins(self):
		"""
		Sets the Vcc and GND pins specified in the config file.
		"""
		self.PinsHigh(self.config.CONFIG["VCC"])
		self.PinsLow(self.config.CONFIG["GND"])

	def _build_command(self, cmd, pin, buffer=False):
		"""
		Builds a command from the specified command code and pin number.
		Buffers data if buffer is set to True.
		"""
		self.BUFFER += self.PackBytes([cmd, pin])

		if not buffer or len(self.BUFFER) == self.MAX_GPIO_BUFFER:
			self.FlushBuffer()

	def _exit(self):
		"""
		Exits GPIO mode.
		"""
		self._build_command(self.EXIT, 0)

	def FlushBuffer(self):
		"""
		Flushes the GPIO data buffer.
		"""
		if len(self.BUFFER) > 0:
			repeat = 0
			num_cmd = len(self.BUFFER) / 2

			data = self.PackBytes([num_cmd, repeat]) + self.BUFFER
			self.BUFFER = ""
		
			self.WriteBytes(data)
			self.ReadAck()

	def PinHigh(self, pin, buffer=False):
		"""
		Sets the specified pin high.
		"""
		self._build_command(self.HIGH, self.Pin2Real(pin), buffer)

	def PinsHigh(self, pins, buffer=False):
		"""
		Sets the specified pins high.
		"""
		for pin in pins:
			self.PinHigh(pin, buffer)

	def PinLow(self, pin, buffer=False):
		"""
		Sets the specified pin low.
		"""
		self._build_command(self.LOW, self.Pin2Real(pin), buffer)

	def PinsLow(self, pins, buffer=False):
		"""
		Sets the specified pins low.
		"""
		for pin in pins:
			self.PinLow(pin, buffer)

	def SetPins(self, high, low):
		"""
		Sets the specified array of pins high and low respectively.
		"""
		for pin in high:
			self.PinHigh(pin, True)
		for pin in low:
			self.PinLow(pin, True)
		self.FlushBuffer()

	def ReadPin(self, pin):
		"""
		Reads and returns the value of the specified pin.
		High == 1, Low == 0.
		"""
		self._build_command(self.READ, self.Pin2Real(pin))
		data = ord(self.ReadBytes()[0])
		return data

	def ReadPins(self, pins):
		"""
		Reads and returns the value of the specified pins.
		High == 1, Low == 0.
		"""
		data = []
		rx = ''
		i = 0

		# Data MUST be flushed prior to entering the below loop. If not, _build_command may
		# automatically flush the buffer for us. The resulting data returned from reading
		# the specified pins will then interfere with the next ReadAck call the next time the
		# buffer is flushed.
		self.FlushBuffer()

		while i < len(pins):
			count = 0

			# Only send MAX_GPIO_COMMANDS read commands at a time
			for pin in pins[i:i+self.MAX_GPIO_COMMANDS]:
				self._build_command(self.READ, self.Pin2Real(pins[i]), True)
				i += 1
				count += 1

			# Make sure the buffer is flushed in case len(pins) < self.MAX_GPIO_COMMANDS
			self.FlushBuffer()
			# Read back count number of bytes
			rx += self.ReadBytes(count)

		# Convert all bytes to numbers
		for i in range(0, len(rx)):
			data.append(ord(rx[i]))

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
