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

	def ReadChip(self, address, count):
		return self.Read(address, count)

	def WriteChip(self, address, data):
		self.config.SetCommand("WRITE")
		return self.Write(address, data)

	def EraseChip(self):
		self.config.SetCommand("ERASE")
		self.Write(0x00, "\xFF")

def SPI(Gumbi):
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

def I2C(Gumbi):
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

