#!/usr/bin/env python

import sys
from getopt import getopt as GetOpt, GetoptError
from gumbi import Parallel

class NORFlash(Parallel):

	# Default chip erase time in seconds
	DEFAULT_TSCE = 60

	def ReadChip(self, address=0, count=0):
		"""
		Reads count bytes from the target chip starting at address.
		"""
		if count == 0:
			count = self.config.GetSetting("SIZE")[0]
			if count is None:
				count = 0

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
		vendor = ord(self.Read(0, 1))
		product = ord(self.Read(1, 1))
		return (vendor, product)

        def EraseChip(self):
		"""
		Perform a full erase of the target chip.
		"""
                self.config.SetCommand("ERASE")

		self.config.SetSetting("CMDELAY", self.config.GetSetting("TSCE"))
		if self.config.GetSetting("CMDELAY") is None:
			self.config.SetSetting("CMDELAY", [self.DEFAULT_TSCE])
		
		self.ExecuteCommands()
		return True




if __name__ == "__main__":

	CONFIG_PATH = "examples/config/"

	def wordflip(data):
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

	def usage():
		print ""
		print "Usage: %s [OPTIONS]" % sys.argv[0]
		print ""
		print "\t-i, --id                 Retrieve the vendor and product IDs from the target chip."
		print "\t-e, --erase              Erase the target chip."
		print "\t-r, --read=<file>        Read data from the chip and save it in the specified file"
		print "\t-w, --write=<file>       Write data from the specified file to the chip"
		print "\t-c, --chip=<part no.>    Specify the part number of the target chip"
		print "\t-a, --address=<int>      Specify the starting address [0]"
		print "\t-s, --size=<int>         Specify the number of bytes to read/write"
		print "\t-f, --word-flip=<file>   Word-flip the contents of the specified file"
		print "\t-p, --path=<path>        Set the path to the chip configuration files [%s]" % CONFIG_PATH
		print "\t-h, --help               Show help"
		print ""
		sys.exit(1)

	t = 0
	size = 0
	address = 0
	doid = False
	doerase = False
	chip = None
	infile = None
	config = None
	outfile = None
	flipfile = None

	try:
		opts, args = GetOpt(sys.argv[1:], "iea:s:r:w:c:f:p:h", ["id", "erase", "address=", "size=", "read=", "write=", "chip=", "word-flip=", "--path=", "help"])
	except GetoptError, e:
		print e
		usage()

	for opt, arg in opts:
		if opt in ('-i', '--id'):
			doid = True
		elif opt in ('-e', '--erase'):
			doerase = True
		elif opt in ('-a', '--address'):
			address = int(arg)
		elif opt in ('-s', '--size'):
			size = int(arg)
		elif opt in ('-r', '--read'):
			outfile = arg
		elif opt in ('-w', '--write'):
			infile = arg
		elif opt in ('-c', '--chip'):
			chip = arg
		elif opt in ('-f', '--word-flip'):
			flipfile = arg
		elif opt in ('-p', '--path'):
			CONFIG_PATH = arg + '/'
		elif opt in ('-h', '--help'):
			usage()

	
	if flipfile:
		open("%s.flip" % flipfile, "wb").write(wordflip(open(flipfile, "rb").read()))
		print "File saved to: %s.flip" % flipfile
		sys.exit(0)
	else:
		try:
			config = CONFIG_PATH + chip.upper() + '.conf'
		except:
			print "Please specify the chip type!"
			usage()

	if doid:
		flash = NORFlash(config=config)
		vendor, product = flash.ChipID()
		print "Vendor ID: 0x%X" % vendor
		print "Product ID: 0x%X" % product
		flash.Close()

	if doerase:
		flash = NORFlash(config=config)
		sys.stdout.write("Erasing chip...")
		sys.stdout.flush()
		flash.EraseChip()
		flash.Close()
		print "done."

	if infile:
		flash = NORFlash(config=config)
		
		data = open(infile, "rb").read()
		if not size:
			size = len(data)
		
		print "Writing %d bytes from %s starting at address 0x%X...\n" % (size, infile, address)
		flash.StartTimer()
		flash.WriteChip(address, data[0:size])
		t = flash.StopTimer()
		flash.Close()
		print "\n"

	if outfile:
		flash = NORFlash(config=config)

		if size:
			print "Reading %d bytes starting at address 0x%X...\n" % (size, address)
		else:
			print "Reading all bytes starting at address 0x%X...\n" % (address)

		flash.StartTimer()
		open(outfile, "wb").write(flash.ReadChip(address, size))
		t = flash.StopTimer()
		flash.Close()
		print "\n"

	if t:
		print "Operation completed in", t, "seconds."

