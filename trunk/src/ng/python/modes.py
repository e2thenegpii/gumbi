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


