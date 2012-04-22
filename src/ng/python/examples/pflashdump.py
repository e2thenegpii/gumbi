#!/usr/bin/env python

from modes import Parallel

class ParallelFlash(Parallel):

	# Default chip erase time in uS
	DEFAULT_TSCE = 10000000

	def ReadChip(self, address, count):
		"""
		Reads count bytes from the target chip starting at address.
		"""
                return self.Read(address, count)

        def WriteChip(self, address, data):
		"""
		Writes data to the target chip starting at address.
		"""
                self.config.SetCommand("WRITE")
                return self.Write(address, data)

	def ChipID(self):
		"""
		This is a generic method to obtain the vendor and product ID of parallel flash chips.
		It may not work for some chips; for others, you may need to connect an external high voltage power source to certian pins. 
		Consult your chip's datasheet.

		Returns a tuple of (vendor id, product id).
		"""
		self.config.SetCommand("ID")
		vendor = ord(self.Read(0, 1)[0])
		product = ord(self.Read(1, 1)[0])
		return (vendor, product)

        def EraseChip(self):
		"""
		Perform a full erase of the target chip.
		"""
                self.config.SetCommand("ERASE")

		#TODO: The maximum possible TSCE delay is only a few seconds.
		#      Need a wrapper in the AVR code to handle londer delays for chip erases.
		try:
			self.config.CONFIG["CMDELAY"] = self.config.CONFIG["TSCE"]
		except:
			self.config.CONFIG["CMDELAY"] = [self.DEFAULT_TSCE]

		# TODO: Why does ExecuteCommands() need to be invoked twice for the erase to work?
		self.ExecuteCommands()
		self.ExecuteCommands()
		return True

if __name__ == "__main__":

	pflash = ParallelFlash(config="config/39SF020.conf")
	vendor, product = pflash.ChipID()
	pflash.Close()

	print "Vendor ID:  0x%X" % vendor
	print "Product ID: 0x%X" % product
