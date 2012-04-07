#!/usr/bin/env python

import serial
import struct
import time

class Gumbi:
	"""
	Primary gumbi class. All other classes should be subclassed from this.
	"""

	ACK = "A"
	NACK = "N"
	BAUD = 9600
	DEFAULT_PORT = '/dev/ttyUSB0'
	MAX_PINS = 128
	RESET_LEN = 1024

	NOP = 0
	PFLASH = 1
	SPIFLASH = 2
	SPIEEPROM = 3
	I2CEEPROM = 4
	PING = 5
	INFO = 6
	SPEED = 7
	IO = 8
	ID = 9

	EXIT = 0
	READ = 1
	WRITE = 2
	ERASE = 3
	HIGH = 4
	LOW = 5

	def __init__(self, port=None):
		self.serial = None
		self._open(port)

	def _open(self, port):
		if port is None:
			port = self.DEFAULT_PORT
		self.serial = serial.Serial(port, self.BAUD)

	def _close(self):
		self.serial.close()

	def Pin2Real(self, pin):
		return (pin - 1)

	def Pack32(self, value):
                return struct.pack("<I", value)

        def Pack16(self, value):
                return struct.pack("<H", value)

        def PackByte(self, value):
                return chr(value)

        def PackBytes(self, data):
                pdata = ''

                for byte in data:
                        pdata += self.PackByte(byte)

                return pdata

	def ReadAck(self):
		if self.Read(1) != self.ACK:
			raise Exception(self.ReadText())
		return True

	def SetMode(self, mode):
		self.Write(self.PackByte(mode))

	def ReadText(self):
		return self.serial.readline().strip()

	def Read(self, n=1):
		return self.serial.read(n)

	def Write(self, data):
		self.serial.write(data)
		self.serial.flush()
		self.ReadAck()

	def Reset(self):
		self.serial.write(self.PackByte(self.EXIT))
		for i in range(0, self.RESET_LEN):
			self.serial.write(self.PackByte(self.NOP))
		self.SetMode(self.NOP)
		time.sleep(1)

	def Close(self):
		return self._close()

class IO(Gumbi):

	def __init__(self, port=None):
		Gumbi.__init__(self, port)
		self.SetMode(self.IO)

	def _exit(self):
		self.Write(self.PackBytes([self.EXIT, 0]))

	def PinHigh(self, pin):
		self.Write(self.PackBytes([self.HIGH, self.Pin2Real(pin)]))

	def PinLow(self, pin):
		self.Write(self.PackBytes([self.LOW, self.Pin2Real(pin)]))

	def ReadPin(self, pin):
		self.Write(self.PackBytes([self.READ, self.Pin2Real(pin)]))
		return ord(self.Read(1))

	def Close(self):
		self._exit()
		self._close()

class SpeedTest(Gumbi):

	def __init__(self, count, port=None):
		Gumbi.__init__(self, port)
		self.count = count
		self.SetMode(self.SPEED)

	def _test(self):
		self.Write(self.Pack32(self.count))
		for i in range(0, self.count):
			self.Read(1)

	def Go(self):
		time.sleep(1)
		start = time.time()
		self._test()
		t = time.time() - start
		return t

class Info(Gumbi):

	def Info(self):
		data = []

		self.SetMode(self.INFO)
		while True:
			line = self.ReadText()
			if line == self.ACK:
				break
			else:
				data.append(line)
		return data

class Identify(Gumbi):

	def Identify(self):
		self.SetMode(self.ID)
		return self.ReadText()

class Ping(Gumbi):

	def Ping(self):
		self.SetMode(self.PING)
		return self.ReadAck()


if __name__ == '__main__':
	try:
		info = Info()
		print info.Info()
		info.Close()

		id = Identify()
		print id.Identify()
		id.Close()

		io = IO()
		io.PinHigh(1)
		io.PinHigh(2)
		print io.ReadPin(3)
		io.Close()

	except Exception, e:
		print "Error:", e
