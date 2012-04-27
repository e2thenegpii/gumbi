#!/usr/bin/env python

from gumbi import GPIO

def bits2pins(value, pins):
	high = []
	low = []

	for i in range(0, len(pins)):
		if (value | (1 << i)) == value:
			high.append(pins[i])
		else:
			low.append(pins[i])
	return (high, low)

def addrdata(byte, address):
	high,low = bits2pins(address, addr)
	io.SetPins(high, low)
	io.PinLow(we)

	high,low = bits2pins(byte, data)
	io.SetPins(high, low)
	io.PinHigh(we)



vdd = 32
we = 31
oe = 24
ce = 22
vss = 16
addr = [12,11,10,9,8,7,6,5,27,26,23,25,4,28,29,3,2,30]
data = [13,14,15,17,18,19,20,21]

io = GPIO()
io.SetPins([vdd,we,oe], [vss, ce])

addrdata(0xaa, 0x5555)
addrdata(0x55, 0x2aaa)
addrdata(0x90, 0x5555)

io.PinHigh(ce)
addrdata(0x00, 0x0000)

io.SetPins([], [oe, ce])
print "Vendor ID:", io.ReadPins(data)

addrdata(0x00, 0x0001)
print "Product ID:", io.ReadPins(data)

io.Close()
