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
	UNUSED = 0xFF
	TEST_BYTE = "\xFF"

	NOP = 0
	PFLASH = 1
	SPIFLASH = 2
	SPIEEPROM = 3
	I2CEEPROM = 4
	PING = 5
	INFO = 6
	SPEED = 7
	GPIO = 8
	ID = 9

	EXIT = 0
	READ = 1
	WRITE = 2
	ERASE = 3
	HIGH = 4
	LOW = 5

	def __init__(self, port=None):
		"""
		Class constructor, calls self._open().
		@port - Gumbi serial port.
		"""
		self.ts = 0
		self.serial = None
		self._open(port)

	def _open(self, port):
		"""
		Opens a connection to the Gumbi board.
		"""
		if port is None:
			port = self.DEFAULT_PORT
		self.serial = serial.Serial(port, self.BAUD)

	def _close(self):
		"""
		Closes the connection with the Gumbi board.
		"""
		self.serial.close()

	def StartTimer(self):
		"""
		Starts the timer.
		"""
		self.ts = time.time()

	def StopTimer(self):
		"""
		Stops the timer and returns the seconds elapsed since StartTimer().
		"""
		return (time.time() - self.ts)

	def Pin2Real(self, pin):
		"""
		Converts user-supplied pin numbers (index 1) to Gumbi board pin numbers (index 0).
		"""
		return (pin - 1)

	def Pack32(self, value):
		"""
		Packs a 32-bit value for transmission to the Gumbi board.
		"""
                return struct.pack("<I", value)

        def Pack16(self, value):
		"""
		Packs a 16-bit value for transmission to the Gumbi board.
		"""
                return struct.pack("<H", value)

        def PackByte(self, value):
		"""
		Packs an 8-bit value for transmission to the Gumbi board.
		"""
                return chr(value)

        def PackBytes(self, data):
		"""
		Packs an array of 8-bit values for transmission to the Gumbi board.
		"""
                pdata = ''
                for byte in data:
                        pdata += self.PackByte(byte)
                return pdata

	def PackFiller(self, count):
		"""
		Returns count filler bytes of data.
		"""
		return ("\x00" * count)

	def ReadAck(self):
		"""
		Reads an ACK/NACK from the Gumbi board. Returns True on ACK, raises an exception on NACK.
		"""
		if self.Read(1) != self.ACK:
			raise Exception(self.ReadText())
		return True

	def SetMode(self, mode):
		"""
		Puts the Gumbi board in the specified mode.
		"""
		self.Write(self.PackByte(mode))

	def ReadText(self):
		"""
		Reads and returns a new-line terminated string from the Gumbi board.
		"""
		return self.serial.readline().strip()

	def Read(self, n=1):
		"""
		Reads n bytes of data from the Gumbi board. Default n == 1.
		"""
		return self.serial.read(n)

	def Write(self, data):
		"""
		Sends data to the Gumbi board and verifies acknowledgement.
		"""
		self.serial.write(data)
		self.ReadAck()

	def Reset(self):
		"""
		Resets the communications stream with the Gumbi board.
		"""
		self.serial.write(self.PackByte(self.EXIT))
		for i in range(0, self.RESET_LEN):
			self.SetMode(self.NOP)

	def Close(self):
		"""
		Closes the connection with the Gumbi board.
		"""
		return self._close()

class GPIO(Gumbi):
	"""
	Class to provide raw read/write access to all I/O pins.
	"""

	def __init__(self, port=None):
		"""
		Class constructor.
		"""
		Gumbi.__init__(self, port)
		self.SetMode(self.GPIO)

	def _exit(self):
		"""
		Exits the Gumbi board from GPIO mode.
		"""
		self.Write(self.PackBytes([self.EXIT, 0]))

	def PinHigh(self, pin):
		"""
		Sets the specified pin high.
		"""
		self.Write(self.PackBytes([self.HIGH, self.Pin2Real(pin)]))

	def PinLow(self, pin):
		"""
		Sets the specified pin low.
		"""
		self.Write(self.PackBytes([self.LOW, self.Pin2Real(pin)]))

	def ReadPin(self, pin):
		"""
		Reads and returns the value of the specified pin.
		High == 1, Low == 0.
		"""
		self.Write(self.PackBytes([self.READ, self.Pin2Real(pin)]))
		return ord(self.Read(1))

	def Close(self):
		"""
		Exits GPIO mode, closes the Gumbi board connection.
		"""
		self._exit()
		self._close()

class SpeedTest(Gumbi):

	def __init__(self, count, port=None):
		Gumbi.__init__(self, port)
		self.data = ''
		self.count = count
		self.SetMode(self.SPEED)

	def _test(self):
		self.Write(self.Pack32(self.count))
		self.data = self.Read(self.count)

	def Go(self):
		self.StartTimer()
		self._test()
		return self.StopTimer()

	def Validate(self):
		retval = True
		for byte in self.data:
			if byte != self.TEST_BYTE:
				retval = False
				break
		return retval

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

class ParallelFlash(Gumbi):
	
	def __init__(self, latchd=0, address=[], data=[], vcc=[], gnd=[], ce=(Gumbi.UNUSED,0), we=(Gumbi.UNUSED,0), oe=(Gumbi.UNUSED,0), be=(Gumbi.UNUSED,0), by=(Gumbi.UNUSED,0), wp=(Gumbi.UNUSED,0), rst=(Gumbi.UNUSED,0), port=None):
		self.latch_delay = latchd
		self.address = self._convert_pin_array(address)
		self.data = self._convert_pin_array(data)
		self.vcc = self._convert_pin_array(vcc)
		self.gnd = self._convert_pin_array(gnd)
		self.ce = self._convert_control_pin(ce)
		self.we = self._convert_control_pin(we)
		self.oe = self._convert_control_pin(oe)
		self.be = self._convert_control_pin(be)
		self.by = self._convert_control_pin(by)
		self.wp = self._convert_control_pin(wp)
		self.rst = self._convert_control_pin(rst)

		Gumbi.__init__(self, port)
		self.SetMode(self.PFLASH)

	def _convert_control_pin(self, cp):
		return (self.Pin2Real(cp[0]), cp[1])

	def _convert_pin_array(self, pins):
		for i in range(0, len(pins)):
			pins[i] = self.Pin2Real(pins[i])
		return pins

	def _pack_pins(self, pins):
		pd = self.PackBytes(pins)
		pd += self.PackFiller(self.MAX_PINS - len(pins))
		return pd

	def _struct(self, action, start, count):
		data = self.PackByte(action)
		data += self.Pack32(start)
		data += self.Pack32(count)
		data += self.PackByte(self.latch_delay)
		data += self.Pack16(len(self.address))
		data += self.Pack16(len(self.data))
		data += self.Pack16(len(self.vcc))
		data += self.Pack16(len(self.gnd))
		data += self._pack_pins(self.address)
		data += self._pack_pins(self.data)
		data += self._pack_pins(self.vcc)
		data += self._pack_pins(self.gnd)
		data += self.PackBytes(self.ce)
		data += self.PackBytes(self.we)
		data += self.PackBytes(self.oe)
		data += self.PackBytes(self.be)
		data += self.PackBytes(self.by)
		data += self.PackBytes(self.wp)
		data += self.PackBytes(self.rst)
		return data

	def ReadFlash(self, start, count):
		data = self._struct(self.READ, start, count)
		self.Write(data)
		self.ReadAck()
		return self.Read(count)

	def WriteFlash(self, addr, data):
		self.Write(self._struct(self.WRITE, start, len(data)))
		self.Write(data)
		return self.ReadAck()


if __name__ == '__main__':
#	try:
		info = Info()
		for line in info.Info():
			print line
		info.Close()

		print "Starting test run..."
		s = SpeedTest(1024)
		t = s.Go()
		v = s.Validate()
		s.Close()
		print "Read 1024 bytes in", t, "seconds"
		print "Data valid:", v

		flash = ParallelFlash(address=[12,11,10,9,8,7,6,5,27,26,23,25,4,3,2,30], data=[13,14,15,17,18,19,20,21], vcc=[32], gnd=[16], ce=(22,0), we=(31,0), oe=(24,0))
		flash.StartTimer()
		data = flash.ReadFlash(0, 1024) #262144)
		t = flash.StopTimer()
		flash.Close()

		print "Read 1024 bytes in", t, "seconds"
		open("flash.bin", "w").write(data)
#	except Exception, e:
##		print "Error:", e
