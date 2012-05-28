from gumbi import *
from debug import ScanBus

class Parallel(Gumbi):
	"""
	Class for interfacing with parallel devices.
	"""

	MODE = "PARALLEL"
	
	def __init__(self, config=None):
		"""
		Class constructor.

		@config - Path to configuration file.

		Returns None.
		"""
		self.config = Configuration(config, self.MODE)
		Gumbi.__init__(self)
		self.SetMode(self.PARALLEL)
	
	def _exit(self):
		"""
		Exit parallel mode. For internal use only.
		"""
		self.WriteBytes(self.config.Pack(self.EXIT, 0, 0))
		self.ReadAck()
		self.ReadAck()

class Monitor(Gumbi):
	"""
	Class for monitoring input pins on the Gumbi board.
	"""

	def __init__(self, count=0, voltage=0):
		"""
		Class constructor.

		@count - The number of pins to read. Must be a multiple of 16.
			 If 0 or not specified, all pins will be read.
	
		Returns None.
		"""
		Gumbi.__init__(self)
		if voltage != 0:
			self.SetVoltage(voltage)
		self.num_pins = self.PinCount(count)
		self.num_ports = self.num_pins / self.PINS_PER_PORT
		self.SetMode(self.MONITOR)

	def Sniff(self, n):
		"""
		Reads in blocks of pin data.

		@n - Number of locks to read. Each block contains the pin status for every Gumbi pin.

		Returns an array (size n) of dicts with each pin number and pin state.
		"""
		pin_array = []
		bytes_per_iteration = self.num_ports * n

		self.WriteBytes(self.Pack32(n))
		data = self.ReadBytes(bytes_per_iteration)

		for j in range(0, n):
			i = 0
			pins = {}
			offset = j * self.num_ports
			bytes = data[offset:offset+self.num_ports]

			for byte in bytes:
				byte = ord(byte)

				for k in range(0, 8):
					pins[i+1] = ((byte & (1 << k)) >> k)
					i += 1

			pin_array.append(pins)
				

		return pin_array

	def _exit(self):
		"""
		Exit monitor mode. For internal use only.
		"""
		self.WriteBytes(self.Pack32(0))
		self.ReadAck()

		# Tell the Gumbi board to re-scan the I/O bus in order to re-set the pin count to its original value
		self.SetMode(self.SCANBUS)
		self.ReadBytes(1)

class GPIO(Gumbi):
	"""
	Class to provide raw read/write access to all I/O pins.
	"""

	MODE = "GPIO"
	BUFFER = ""

	def __init__(self, config=None, voltage=0):
		"""
		Class constructor.

		@config - Path to configuration file.

		Returns None.
		"""
		self.config = Configuration(config, self.MODE)
		Gumbi.__init__(self)
		if voltage != 0:
			self.SetVoltage(voltage)
		self.SetMode(self.GPIO)
		self._set_conf_pins()

	def _set_conf_pins(self):
		"""
		Sets the Vcc and GND pins specified in the config file. For internal use only.
		"""
		self.PinsHigh(self.config.CONFIG["VCC"])
		self.PinsLow(self.config.CONFIG["GND"])

	def _send_command(self, cmd, pin):
		"""
		Sends a GPIO command.

		Returns None.
		"""
		self.WriteBytes(self.PackBytes([cmd, pin]))
		self.ReadAck()

	def _exit(self):
		"""
		Exits GPIO mode. For internal use only.
		"""
		self._send_command(self.EXIT, 0)

	def PinHigh(self, pin):
		"""
		Sets the specified pin high.

		@pin    - The pin to set high.

		Returns None.
		"""
		self._send_command(self.HIGH, self.Pin2Real(pin))

	def PinsHigh(self, pins):
		"""
		Sets the specified pins high.

		@pins   - A list of pins to set high.

		Returns None.
		"""
		for pin in pins:
			self.PinHigh(pin)

	def PinLow(self, pin):
		"""
		Sets the specified pin low.

		@pin    - The pin to pull low.

		Returns None.
		"""
		self._send_command(self.LOW, self.Pin2Real(pin))

	def PinsLow(self, pins):
		"""
		Sets the specified pins low.
		
		@pins   - A list of pins to set low.

		Returns None.
		"""
		for pin in pins:
			self.PinLow(pin)

	def SetPins(self, high, low):
		"""
		Sets the specified array of pins high and low respectively.
		First the high pins are set, then the low pins.
		These pin set commands are buffered, then flushed at once.

		@high   - A list of pins to set high.
		@low    - A list of pins to set high.

		Returns None.
		"""
		for pin in high:
			self.PinHigh(pin)
		for pin in low:
			self.PinLow(pin)

	def ReadPin(self, pin):
		"""
		Immediately reads the current state of the specified pin.

		@pin - The pin to read.

		Returns 1 if the pin is high, 0 if low.
		"""
		self._send_command(self.READ, self.Pin2Real(pin))
		return ord(self.ReadBytes()[0])

	def ReadPins(self, pins):
		"""
		Immediately reads the values of the specified pins.
		This function will flush the data buffer.

		@pins - A list of pins to read.

		Returns a list of values for each corresponding pin in the pins list (1 == high, 0 == low).
		"""
		states = []

		for pin in pins:
			states.append(self.ReadPin(pin))

		return states
