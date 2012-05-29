from gumbi import *
from debug import ScanBus

class Monitor(Gumbi):
	"""
	Class for monitoring input pins on the Gumbi board.
	"""

	def __init__(self, count=0, voltage=None):
		"""
		Class constructor.

		@count - The number of pins to read. Must be a multiple of 16.
			 If 0 or not specified, all pins will be read.
	
		Returns None.
		"""
		Gumbi.__init__(self)
		if voltage is not None:
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
		# When told to read back 0 iterations, monitor mode will ACK and exit
		self.ReadAck()

		# Tell the Gumbi board to re-scan the I/O bus in order to re-set the pin count to its original value
		self.SetMode(self.SCANBUS)
		# Dummy read to get the number of I/O pins returned by SCANBUS mode
		self.ReadBytes(1)
