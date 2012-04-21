#!/usr/bin/env python

from modes import Parallel

class ParallelFlash(Parallel):

	def ReadChip(self, address, count):
                return self.Read(address, count)

        def WriteChip(self, address, data):
                self.config.SetCommand("WRITE")
                return self.Write(address, data)

        def EraseChip(self):
		# Erasing doesn't work, may need to use GPIO or add an action to the AVR code
                self.config.SetCommand("ERASE")
                self.Write(0x00, "\xFF")

if __name__ == "__main__":
	pflash = ParallelFlash(config="config/39SF020.conf")
	pflash.WriteChip(0, "\xca\xcb\xcc")
	data = pflash.ReadChip(0, 1024)
	pflash.Close()

	open("flash.bin", "w").write(data)
