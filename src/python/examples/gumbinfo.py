#!/usr/bin/env python

import sys
from time import sleep
from gumbi import GPIO, Info, ScanBus


def blinki():
	io = GPIO(voltage=3)

	try:
		while True:
	
			i = 1

			while i <= 32:
				io.PinHigh(i)
				io.PinLow(i+1)
				i += 2

			while i <= 64:
				io.PinLow(i)
				io.PinHigh(i+1)
				i += 2

			sleep(2)

			io.PinsLow(range(1, 65))

	except KeyboardInterrupt:
		pass

	io.Close()

def info():
#	s = ScanBus()
#	s.Scan()
#	s.Close()

	i = Info()
	for line in i.Info():
		print line
	i.Close()



if __name__ == '__main__':
	def usage():
		print "Usage: %s [--info | --led]" % sys.argv[0]
		sys.exit(1)

	def main():
		try:
			if sys.argv[1] == '--info':
				info()
			elif sys.argv[1] == '--led':
				blinki()
			else:
				raise Exception('bad args')
		except:
			usage()

	main()
