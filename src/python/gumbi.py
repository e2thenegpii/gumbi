#!/usr/bin/env python

import serial
import struct
import time

EXIT = 0
READ = 1
WRITE = 2
ERASE = 3

class Pin:

	NUM_DEVICES = 4
	PINS_PER_DEVICE = 16
	PINS_PER_REGISTER = 8
	REGISTERS_PER_DEVICE = 2

	GPIOA = 0x12
	GPIOB = 0x13

	def __init__(self, pin, active=0):
		self.addr = 0
		self.reg = self.GPIOA
		self.bit = 0
		self.inuse = 0
		self.active = active

		if pin and pin <= (self.PINS_PER_DEVICE * self.NUM_DEVICES):
			self.inuse = 1

			# Calculate which chip address this pin is located on
			self.addr = ((pin-1) / self.PINS_PER_DEVICE)

			# Calculate which bit in the GPIO register needs to be set for this pin
			self.bit = (pin - (((pin-1) / self.PINS_PER_DEVICE) * self.PINS_PER_DEVICE)) - 1

			# Is this pin in GPIOB?
			if self.bit > self.PINS_PER_REGISTER:
				self.reg = self.GPIOB
				self.bit -= self.PINS_PER_REGISTER

	def struct(self):
		data = chr(self.addr)
		data += chr(self.reg)
		data += chr(self.bit)
		data += chr(self.inuse)
		data += chr(self.active)

		return data
	
class Configuration:

	MAX_PINS = 64

	def __init__(self, address=[], data=[], gnd=[], vcc=[], ce=(0,0), we=(0,0), oe=(0,0), be=(0,0), by=(0,0), wp=(0,0), rst=(0,0)):
		self.action = READ
		self.num_addr_pins = len(address)
		self.num_data_pins = len(data)
		self.num_gnd_pins = len(gnd)
		self.num_vcc_pins = len(vcc)
		self.addrs = address
		self.data = data
		self.vcc = vcc
		self.gnd = gnd
		self.ce = ce
		self.we = we
		self.oe = oe
		self.be = be
		self.by = by
		self.wp = wp
		self.rst = rst
		self.address = 0
		self.count = 0

	def __set_action__(self, action):
		self.action = action

	def __pack32__(self, value):
		return struct.pack("<I", value)

	def __pack16__(self, value):
		return struct.pack("<H", value)

	def __packpins__(self, pins):
		data = ''

		for pin in pins:
			data += Pin(pin).struct()
		for na in range(len(pins), self.MAX_PINS):
			data += Pin(0).struct()

		return data

	def Read(self):
		self.__set_action__(READ)

	def Write(self):
		self.__set_action__(WRITE)

	def Erase(self):
		self.__set_action__(ERASE)
	
	def Exit(self):
		self.__set_action__(EXIT)

	def Start(self, address):
		self.address = address

	def Count(self, count):
		self.count = count
	
	def struct(self):
		pc = 0

		data = chr(self.action)
		data += self.__pack32__(self.address)
		data += self.__pack32__(self.count)
		data += self.__pack16__(self.num_addr_pins)
		data += self.__pack16__(self.num_data_pins)
		data += self.__pack16__(self.num_vcc_pins)
		data += self.__pack16__(self.num_gnd_pins)

		data += self.__packpins__(self.addrs)
		data += self.__packpins__(self.data)
		data += self.__packpins__(self.vcc)
		data += self.__packpins__(self.gnd)

		data += Pin(self.ce[0], self.ce[1]).struct()
		data += Pin(self.we[0], self.we[1]).struct()
		data += Pin(self.oe[0], self.oe[1]).struct()
		data += Pin(self.be[0], self.be[1]).struct()
		data += Pin(self.by[0], self.by[1]).struct()
		data += Pin(self.wp[0], self.wp[1]).struct()
		data += Pin(self.rst[0], self.rst[1]).struct()

		return data

class Command:

	NOP = 0
	PFLASH = 1
	SPIFLASH = 2
	SPIEEPROM = 3
	I2CEEPROM = 4
	PING = 5
	DEBUG = 6
	SPEED = 7
	RAWIO = 8

	def __init__(self, config):
		self.mode = self.NOP
		self.config = config

	def __struct__(self):
		data = chr(self.mode) + self.config.struct()
		return data

	def ParallelFlash(self):
		self.mode = self.PFLASH
		return self.__struct__()

	def SPIFlash(self):
		self.mode = self.SPIFLASH
		return self.__struct__()

	def SPIEEPROM(self):
		self.mode = self.SPIEERPOM
		return self.__struct__()

	def I2CEEPROM(self):
		self.mode= self.I2CEEPROM
		return self.__struct__()

	def Ping(self):
		self.mode = self.PING
		return self.__struct__()

	def Debug(self):
		self.mode = self.DEBUG
		return self.__struct__()

	def Speed(self):
		self.mode = self.SPEED
		return self.__struct__()

	def IO(self):
		self.mode = self.RAWIO
		return self.__struct__()

class IO:

	def __init__(self, pin, hl=0, rw=READ):	
		self.rw = rw
		self.pin = Pin(pin, hl)

	def struct(self):
		data = chr(self.rw)
		data += self.pin.struct()
		return data

class Gumbi:

	ACK = "ACK"
	NACK = "NACK"
	BAUD = 9600
	DEFAULT_PORT = '/dev/ttyUSB0'

	def __init__(self, port=None):
		if port is None:
			port = self.DEFAULT_PORT

		self.serial = serial.Serial(port, self.BAUD)

	def Execute(self, conf):
		ack = None
		data = []

		self.Write(conf)

		while ack is None:
			line = self.ReadText()

			if line.startswith(self.ACK):
				ack = self.ACK
			elif line.startswith(self.NACK):
				ack = self.NACK
			else:
				data.append(line)
		
		return (ack, data)

	def ReadText(self):
		return self.serial.readline().strip()

	def Read(self, n=1):
		return self.serial.read(n)

	def Write(self, data):
		self.serial.write(data)

	def Close(self):
		return self.serial.close()


config = Configuration(vcc=[1,2,3,4,5,6,7,8])
cmd = Command(config)
gumbi = Gumbi()
print gumbi.Execute(cmd.Debug())
print gumbi.Execute(cmd.IO())
gumbi.Write(IO(1,0).struct())
print gumbi.Read()
gumbi.Close()


