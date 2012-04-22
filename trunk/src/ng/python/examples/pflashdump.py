#!/usr/bin/env python

from modes import Parallel

class ParallelFlash(Parallel):

	# Default chip erase time in uS
	DEFAULT_TSCE = 10000000

	def ReadChip(self, address, count):
                return self.Read(address, count)

        def WriteChip(self, address, data):
                self.config.SetCommand("WRITE")
                return self.Write(address, data)

        def EraseChip(self):
                self.config.SetCommand("ERASE")

		try:
			self.config.CONFIG["CMDELAY"] = self.config.CONFIG["TSCE"]
		except:
			self.config.CONFIG["CMDELAY"] = [self.DEFAULT_TSCE]

		# TODO: Why does ExecuteCommands need to be invoked twice for the erase to work?
		self.ExecuteCommands()
		self.ExecuteCommands()

		return True

if __name__ == "__main__":
	pflash = ParallelFlash(config="config/39SF020.conf")
	data = pflash.ReadChip(0, 1024)
	pflash.Close()

	open("flash.bin", "w").write(data)
