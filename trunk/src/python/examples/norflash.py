#!/usr/bin/env python

from gumbi import Parallel

class NORFlash(Parallel):

	# Default chip erase time in seconds
	DEFAULT_TSCE = 60

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

		try:
			self.config.CONFIG["CMDELAY"] = self.config.CONFIG["TSCE"]
		except:
			self.config.CONFIG["CMDELAY"] = [self.DEFAULT_TSCE]

		# TODO: Why does ExecuteCommands() need to be invoked twice for the erase to work?
		self.ExecuteCommands()
		self.ExecuteCommands()
		return True

	def FlipEndianess(self, data):
		"""
		Word-flips a given data string.

		@data - String of data to flip.

		Returns converted data.
		"""
		i = 0
		fdata = ''

		while i < len(data):
			fdata += data[i+1] + data[i]
			i += 2

		return fdata


if __name__ == "__main__":
	flash = NORFlash(config="examples/config/29LV320.conf")
	flash.StartTimer()
	data = flash.ReadChip(0, 1024)
	t = flash.StopTimer()
	flash.Close()
