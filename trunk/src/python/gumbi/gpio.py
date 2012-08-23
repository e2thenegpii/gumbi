from gumbi import *
from configuration import *

class GPIO(Gumbi):
	"""
	Class to provide raw read/write access to all I/O pins.
	"""

	MODE = "GPIO"

	def __init__(self, config=None, voltage=None, port=None):
		"""
		Class constructor.

		@config - Path to configuration file.

		Returns None.
		"""
		self.config = Configuration(config, self.MODE, port)
		Gumbi.__init__(self, port=port)
		if voltage is not None:
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
		# GPIO mode will return an ACK once the specified command is completed
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
