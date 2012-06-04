#!/usr/bin/env python

import os
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
		self.read_data = ''
		
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

	def VendorID(self):
		"""
		This is a generic method to obtain the vendor ID of a parallel flash chip.
		It may not work for all chips; consult the chip's datasheet.

		Returns the vendor ID.
		"""
		self.config.SetCommand("ID")
		return ord(self.Read(0, 2)[0])

	def ProductID(self):
		"""
		This is a generic method to obtain the product ID of a parallel flash chip.
		It may not work for all chips; consult the chip's datasheet.

		Returns the product ID.
		"""
		self.config.SetCommand("ID")
		return ord(self.Read(1, 2)[0])

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

	CONFIG_PATH = "bin/config/"
	CONF_EXT = '.conf'
	PORT = None

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

	def chip_list():
		chips = []

		for filename in os.listdir(CONFIG_PATH):
			if filename.endswith(CONF_EXT):
				chips.append(filename.strip(CONF_EXT))

		chips.sort()
		return chips

	def list_chips():
		print ""
		print "Supported chips:\n"
		for chip in chip_list():
			print "\t", chip
		print ""

	def usage():
		print ""
		print "Usage: %s [OPTIONS]" % sys.argv[0]
		print ""
		print "\t-i, --id                 Retrieve the vendor and product IDs from the target chip"
		print "\t-e, --erase              Erase the target chip"
		print "\t-l, --list               List supported chips"
		print "\t-r, --read=<file>        Read data from the chip and save it in the specified file"
		print "\t-w, --write=<file>       Write data from the specified file to the chip"
		print "\t-c, --chip=<part no.>    Specify the part number of the target chip"
		print "\t-a, --address=<int>      Specify the starting address [0]"
		print "\t-s, --size=<int>         Specify the number of bytes to read/write"
		print "\t-f, --word-flip=<file>   Word-flip the contents of the specified file"
		print "\t-p, --path=<path>        Set the path to the chip configuration files [%s]" % CONFIG_PATH
		print "\t-v, --verbose            Enabled verbose output"
		print "\t-h, --help               Show help"
		print ""
		sys.exit(1)





	ACTIONS = {}
	ACTION_LIST = ['vendorid', 'productid', 'erase', 'write', 'read']

	t = 0
	size = 0
	address = 0
	doid = False
	doerase = False
	verbose = False
	chip = None
	infile = None
	config = None
	outfile = None
	flipfile = None

	try:
		opts, args = GetOpt(sys.argv[1:], "iela:s:r:w:c:f:p:vh", ["id", "erase", "list", "address=", "size=", "read=", "write=", "chip=", "word-flip=", "--path=", "help"])
	except GetoptError, e:
		print e
		usage()

	for opt, arg in opts:
		if opt in ('-i', '--id'):
			ACTIONS['vendorid'] = True
			ACTIONS['productid'] = True
		elif opt in ('-e', '--erase'):
			ACTIONS['erase'] = True
		elif opt in ('-l', '--list'):
			list_chips()
			sys.exit(0)
		elif opt in ('-a', '--address'):
			address = int(arg)
		elif opt in ('-s', '--size'):
			size = int(arg)
		elif opt in ('-r', '--read'):
			ACTIONS['read'] = arg
		elif opt in ('-w', '--write'):
			ACTIONS['write'] = arg
		elif opt in ('-c', '--chip'):
			chip = arg
		elif opt in ('-f', '--word-flip'):
			open("%s.flip" % flipfile, "wb").write(wordflip(open(arg, "rb").read()))
			print "File saved to: %s.flip" % arg
			sys.exit(0)
		elif opt in ('-p', '--path'):
			CONFIG_PATH = arg + '/'
		elif opt in ('-v', '--verbose'):
			verbose = True
		elif opt in ('-h', '--help'):
			usage()

	
	try:
		config = os.path.join(*[CONFIG_PATH, chip.upper() + CONF_EXT])
	except:
		print "Please specify the chip type!"
		usage()

	for action in ACTION_LIST:

		if ACTIONS.has_key(action):
			
			t = 0
			if verbose:
				sys.stdout.write("Connecting to Gumbi board...")
				sys.stdout.flush()

			flash = NORFlash(config=config, port=PORT)

			if verbose:
				print "connected."
			
			if action == 'vendorid':
				print "Vendor ID: 0x%X" % flash.VendorID()

			elif action == 'productid':
				print "Product ID: 0x%X" % flash.ProductID()
		
			elif action == 'erase':
				sys.stdout.write("Erasing chip...")
				sys.stdout.flush()
				flash.EraseChip()
				print "done."

			elif action == 'write':
				data = open(ACTIONS['write'], "rb").read()
				if not size:
					size = len(data)
			
				print "Writing %d bytes from %s starting at address 0x%X...\n" % (size, ACTIONS['write'], address)
				flash.StartTimer()
				flash.WriteChip(address, data[0:size])
				t = flash.StopTimer()
				print "\n"

			elif action == 'read':
				if size:
					print "Reading %d bytes starting at address 0x%X...\n" % (size, address)
				else:
					print "Reading all bytes starting at address 0x%X...\n" % (address)

				flash.StartTimer()
				open(ACTIONS['read'], "wb").write(flash.ReadChip(address, size))
				t = flash.StopTimer()
				print "\n"

			flash.Close()

			if t:
				print "Operation completed in", t, "seconds."

			if action == 'id':
				sys.exit(0)

