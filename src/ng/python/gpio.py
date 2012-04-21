from gumbi import *

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
