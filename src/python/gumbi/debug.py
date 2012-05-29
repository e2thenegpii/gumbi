from gumbi import *

class SpeedTest(Gumbi):
	"""
	Tests the speed of the PC to Gumbi interface.
	"""

	def __init__(self, count):
		"""
		Class constructor.

		@count - Number of bytes to send during the speed test.

		Returns None.
		"""
		Gumbi.__init__(self)
		self.data = ''
		self.count = count
		self.SetMode(self.SPEEDTEST)

	def _test(self):
		"""
		Sends the byte count and reads the data. For internal use only.
		"""
		self.WriteBytes(self.Pack32(self.count))
		self.data = self.ReadBytes(self.count)

	def Go(self):
		"""
		Runs the speed test.

		Returns the number of seconds it took to transfer self.count bytes.
		"""
		self.StartTimer()
		self._test()
		return self.StopTimer()

	def Validate(self):
		"""
		Validates the received data.

		Returns True if all data was received properly.
		Returns False if data was corrupted.
		"""
		retval = True
		for byte in self.data:
			if byte != self.DUMMY_BYTE:
				retval = False
				break
		return retval

class TransferTest(Gumbi):
	"""
	Test the two-way transfer speed and validates data integrity.
	"""

	XFER_SIZE = 128

	def __init__(self):
		"""
		Class contstructor.
		"""
		self.data = ''
		Gumbi.__init__(self)
		self.SetMode(self.XFER)

	def _xfer(self):
		"""
		Performs the actual data transfer. For internal use only.
		"""
		self.WriteBytes(self.DUMMY_BYTE * self.XFER_SIZE)
		self.data = self.ReadBytes(self.XFER_SIZE)

	def Go(self):
		"""
		Runs and times the data transfer.

		Returns the number of seconds elapsed during the transfer.
		"""
		self.StartTimer()
		self._xfer()
		return self.StopTimer()

	def Validate(self):
		"""
		Validates the data recieved back from the transfer. Must be called after Go().

		Returns True if data is valid, False if invalid.
		"""
		retval = True
		if len(self.data) >= self.XFER_SIZE:
			for i in range(0, self.XFER_SIZE):
				if self.data[i] != self.DUMMY_BYTE:
					retval = False
					break
		else:
			retval = False

		return retval

class Info(Gumbi):
	"""
	Class to retrieve current Gumbi board information.
	"""

	def Info(self):
		"""
		Returns an array of human-readable board information (version, pin count, etc).
		"""
		data = []

		self.SetMode(self.INFO)
		while True:
			line = self.ReadText()
			if line == self.ACK:
				break
			else:
				data.append(line)
		return data

class Identify(Gumbi):
	"""
	Class to obtain the Gumbi board ID.
	"""

	def ID(self):
		"""
		Returns the board ID, as reported by the Gumbi board.
		"""
		self.SetMode(self.GID)
		return self.ReadText()

class Ping(Gumbi):
	"""
	Class to perform a ping test to ensure the Gumbi board is operational.
	"""

	def Ping(self):
		"""
		Returns True if the board was successfully pinged. Raises an exception on error.
		"""
		self.SetMode(self.PING)
		# If successful, PING mode will return one ACK
		return self.ReadAck()

class ScanBus(Gumbi):
	"""
	Class to perform a bus scan for I/O expansion chips.
	"""

	def Scan(self):
		"""
		Returns the number of available I/O pins.
		"""
		self.SetMode(self.SCANBUS)
		return ord(self.ReadBytes(1)[0])

