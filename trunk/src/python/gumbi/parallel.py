from gumbi import Gumbi
from configuration import Configuration

class Parallel(Gumbi):
	"""
	Class for interfacing with parallel devices.
	"""

	MODE = "PARALLEL"
	
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
		self.SetMode(self.PARALLEL)
	
	def _exit(self):
		"""
		Exit parallel mode. For internal use only.
		"""
		self.WriteBytes(self.config.Pack(self.EXIT, 0, 0))
		# First ACK indicates receipt of a valid config
		self.ReadAck()
		# Second ACK indicates the EXIT comand was received successfully
		self.ReadAck()
