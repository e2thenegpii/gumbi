#!/usr/bin/env python

import serial
import struct
import time

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
	HIGH = 4
	LOW = 5

	def __init__(self, port=None):
		if port is None:
			port = self.DEFAULT_PORT

		self.serial = serial.Serial(port, self.BAUD)

	def SetMode(self, mode):
		self.Write(Packer().packbyte(mode))

		if self.ReadText() != self.ACK:
			raise Exception(self.ReadText())

		return

	def ReadText(self):
		return self.serial.readline().strip()

	def Read(self, n=1):
		return self.serial.read(n)

	def Write(self, data):
		self.serial.write(data)

	def Close(self):
		return self.serial.close()

class IO:

	def __init__(self, port=None):
		self.gumbi = Gumbi(port)
		self.gumbi.SetMode(self.gumbi.IO)

	def __struct__(self, action, pin):
		return (chr(action) + chr(pin))

	def __exit__(self):
		self.gumbi.Write(self.__struct__(self.gumbi.EXIT, 0))
		return self.gumbi.ReadText()

	def PinHigh(self, pin):
		self.gumbi.Write(self.__struct__(self.gumbi.HIGH, pin))
		return self.gumbi.ReadText()

	def PinLow(self, pin):
		self.gumbi.Write(self.__struct__(self.gumbi.LOW, pin))
		return self.gumbi.ReadText()

	def ReadPin(self, pin):
		self.gumbi.Write(self.__struct__(self.gumbi.READ, pin))
		return ord(self.gumbi.Read(1))

	def Close(self):
		self.__exit__()
		self.gumbi.ReadText()
		self.gumbi.Close()

class SpeedTest:

	def __init__(self, count, port=None):
		self.count = count
		self.gumbi = Gumbi(port)

	def Go(self):
		start = time.time()
		self.__test__()
		time = time.time() - start
		return time

	def __test__(self):
		self.gumbi.SetMode(self.gumbi.SPEED)
		self.gumbi.Write(Packer().pack32(self.count))
		self.gumbi.Read(self.count)

	def Close(self):
		self.gumbi.Close()

class Info:

	def __init__(self, port=None):
		self.gumbi = Gumbi(port)

	def Go(self):
		data = []

		self.gumbi.SetMode(self.gumbi.INFO)
		while True:
			line = self.gumbi.ReadText()
			if line == self.gumbi.ACK:
				break
			else:
				data.append(line)
		return data

	def Close(self):
		self.gumbi.Close()


class Ping:

	def __init__(self, port=None):
		self.gumbi = Gumbi(port)

	def Go(self):
		data = None
		self.gumbi.SetMode(self.gumbi.PING)
		data = self.gumbi.ReadText()
		return data

	def Close(self):
		self.gumbi.Close()

if __name __ == '__main__':
	info = Info()
	print info.Go()
	info.Close()

