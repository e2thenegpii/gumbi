#!/usr/bin/env python

from time import sleep
from modes import GPIO

def wait():
	sleep(.25)


i = 1
io = GPIO()

try:
	while True:
		while i <= 32:
			io.PinHigh(i)
			io.PinLow(i+1)
			wait()
			i += 2

		while i <= 64:
			io.PinLow(i)
			io.PinHigh(i+1)
			wait()
			i += 2

		sleep(5)

		io.PinsLow(range(1, 65))

		sleep(1)

except KeyboardInterrupt:
	pass

io.Close()

