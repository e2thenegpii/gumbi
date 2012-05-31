#!/usr/bin/env python

import sys
from time import sleep
from gumbi import Gumbi, GPIO, Info, ScanBus


def blinki():
	io = GPIO(voltage=3)

	try:
		print "Starting Gumbi LED test. Press Ctrl+C to quit."

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

def voltage(v):
	g = Gumbi()
	g.SetVoltage(v)
	g.Close()

def scan():
	s = ScanBus()
	s.Scan()
	s.Close()

def info():
	i = Info()
	for line in i.Info():
		print line
	i.Close()



if __name__ == '__main__':
	def usage():
		print "Usage: %s [--info | --led | --scan | --voltage <0|2|3|5>]" % sys.argv[0]
		sys.exit(1)

	def main():
		try:
			if sys.argv[1] == '--info':
				info()
			elif sys.argv[1] == '--led':
				blinki()
			elif sys.argv[1] == '--scan':
				scan()
				info()
			elif sys.argv[1] == '--voltage':
				voltage(int(sys.argv[2]))
				info()
			else:
				raise Exception('bad args')
		except Exception, e:
			print e
			usage()

	main()
