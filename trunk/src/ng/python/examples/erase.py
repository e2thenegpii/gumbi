#!/usr/bin/env python

from gumbi import *
from modes import GPIO
from time import sleep

def bits2pins(value, pins):
	high = []
	low = []

	for i in range(0, len(pins)):
		if (value | (1 << i)) == value:
			high.append(pins[i])
		else:
			low.append(pins[i])
	return (high, low)

def wait(msg):
	print msg

#	try:
#		while True:
#			sleep(1)
#	except:
#		pass

vdd = 32
we = 31
oe = 24
ce = 22
vss = 16
addr = [12,11,10,9,8,7,6,5,27,26,23,25,4,28,29,3,2,30]
data = [13,14,15,17,18,19,20,21]

io = GPIO()
io.PinsHigh([vdd,we,oe])
io.PinsLow([vss, ce])
io.PinsLow(addr)

wait("Pins initialized...")

def addrdata(byte, address):
	high,low = bits2pins(address, addr)
	io.PinsHigh(high)
	io.PinsLow(low)
	io.PinLow(we)

	high,low = bits2pins(byte, data)
	io.PinsHigh(high)
	io.PinsLow(low)
	io.PinHigh(we)
	print high
	print low
	wait("0x%X : 0x%X" % (address, byte))

addrdata(0xaa, 0x5555)
addrdata(0x55, 0x2aaa)
addrdata(0x80, 0x5555)
addrdata(0xaa, 0x5555)
addrdata(0x55, 0x2aaa)
addrdata(0x10, 0x5555)

sleep(1)
io.PinLow(we)

io.Close()
