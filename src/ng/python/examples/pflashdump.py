#!/usr/bin/env python

from modes import Parallel

class ParallelFlash(Parallel):

	def ReadChip(self, address, count):
                return self.Read(address, count)

        def WriteChip(self, address, data):
                self.config.SetCommand("WRITE")
                return self.Write(address, data)

        def EraseChip(self):
                self.config.SetCommand("ERASE")
                self.Write(0x00, "\xFF")


pflash = ParallelFlash(config="config/39SF020.conf")
data1 = pflash.ReadChip(0, 1024)
data2 = pflash.ReadChip(0, 1024)
pflash.Close()

if data1 == data2:
	print "Yay!"
else:
	print "Fuck!"

open("flash.bin", "w").write(data1)
