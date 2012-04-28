#!/usr/bin/env python

from time import sleep
from gumbi import GPIO

io = GPIO()

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

