#!/usr/bin/env python

import sys
from gumbi import Parallel

class NORFlash(Parallel):

	# Default chip erase time in seconds
	DEFAULT_TSCE = 60

	def ReadChip(self, address, count):
		"""
		Reads count bytes from the target chip starting at address.
		"""
                return self.Read(address, count, callback=self.PrintProgress)

        def WriteChip(self, address, data):
		"""
		Writes data to the target chip starting at address.
		"""
                self.config.SetCommand("WRITE")
                return self.Write(address, data, callback=self.PrintProgress)

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

		self.ExecuteCommands()
		return True

def WordFlip(data):
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

	data = ''
	size = 1024

	try:
		size = int(sys.argv[1])
		if size < 1024:
			size = 1024
	except:
		pass

	flash = NORFlash(config="examples/config/29LV320.conf")

	try:
		flash.WriteChip(0, "\x01\x02\x03\x04")
		print "Reading %d bytes of data:\n" % size
		flash.StartTimer()
		data = flash.ReadChip(0, size)
#		flash.EraseChip()
		t = flash.StopTimer()
	except:
		pass

	flash.Close()

	print "\n"
	print "Read", len(data), "bytes of data in", t, "seconds"
	open("flash.bin", "wb").write(data)
