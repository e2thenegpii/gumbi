#!/usr/bin/env python

import serial
import struct
import timeit

class Packer:

	def pack32(self, value):
		return struct.pack("<I", value)

	def pack16(self, value):
		return struct.pack("<H", value)

	def packbyte(self, value):
		return chr(value)
	
	def packbytes(self, data):
		pdata = ''

		for byte in data:
			pdata += self.pack8(byte)

		return pdata

class Gumbi:

	ACK = "ACK"
	NACK = "NACK"
	BAUD = 9600
	DEFAULT_PORT = '/dev/ttyUSB0'
	MAX_PINS = 128

	NOP = 0
	PFLASH = 1
	SPIFLASH = 2
	SPIEEPROM = 3
	I2CEEPROM = 4
	PING = 5
	INFO = 6
	SPEED = 7
	IO = 8

	EXIT = 0
	READ = 1
	WRITE = 2
	ERASE = 3

	def __init__(self, port=None):
		if port is None:
			port = self.DEFAULT_PORT

		self.serial = serial.Serial(port, self.BAUD)

	def SetMode(self, mode):
		self.Write(Packer().packbyte(mode))
		return self.ReadText()

	def ReadText(self):
		return self.serial.readline().strip()

	def Read(self, n=1):
		return self.serial.read(n)

	def Write(self, data):
		self.serial.write(data)

	def Close(self):
		return self.serial.close()

class SpeedTest:

	def __init__(self, count, port=''):
		if not port:
			self.port = None
		self.count = count
		self.gumbi = Gumbi(port)

	def Go(self):
		t = timeit.Timer("SpeedTest(%d, '%s')._test()" % (self.count, self.port), "from __main__ import SpeedTest")
		time = t.timeit(1)
		self.Close()
		return time

	def _test(self):
		if self.gumbi.SetMode(self.gumbi.SPEED) == self.gumbi.ACK:
			self.gumbi.Write(Packer().pack32(self.count))
			self.gumbi.Read(self.count)
		self.Close()

	def Close(self):
		self.gumbi.Close()


print SpeedTest(128)
