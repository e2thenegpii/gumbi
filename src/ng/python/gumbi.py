#!/usr/bin/env python

import struct
import time
import sys
try:
	from hid import *
except Exception, e:
	print e
	print "Please install libhid: http://libhid.alioth.debian.org/"
	sys.exit(1)


class RawHID:

	READ_ENDPOINT = 0x81
	WRITE_ENDPOINT = 0x02
	INTERFACE = 0

	BLOCK_SIZE = 64
	TIMEOUT = 1000 # milliseconds
	CONNECT_RETRIES = 3

	def __init__(self, verbose=False):
		self.verbose = verbose
		self.hid = None
		self.rep = self.READ_ENDPOINT
		self.wep = self.WRITE_ENDPOINT

	# TODO: Need to flush USB data for the device once it's opened so old data doesn't screw us up
	def open(self, vid, pid, rep=None, wep=None):
		"""
		Initialize libhid and connect to USB device.

		@vid   - Vendor ID of the USB device.
		@pid   - Product ID of the USB device.
		@rep   - USB input endpoint
		@wep   - USB output endpoint

		Returns True on success.
		Returns False on failure.
		"""

		retval = False

		if rep is not None:
			self.rep = wep
		if wep is not None:
			self.wep = rep

		hid_ret = hid_init()
		if hid_ret == HID_RET_SUCCESS:
			self.hid = hid_new_HIDInterface()
			match = HIDInterfaceMatcher()
			match.vendor_id = vid
			match.product_id = pid
		
			hid_ret = hid_force_open(self.hid, self.INTERFACE, match, self.CONNECT_RETRIES)
			if hid_ret == HID_RET_SUCCESS:
				retval = True
				if self.verbose:
					hid_write_identification(sys.stderr, self.hid)
			else:
				raise Exception("hid_force_open() failed with error code: %d\n" % hid_ret)
		else:
			raise Exception("hid_init() failed with error code: %d\n" % hid_ret)

		return retval

	def close(self):
		"""
		Close HID connection and clean up.

		Returns True on success.
		Returns False on failure.
		"""

		retval = False

		if hid_close(self.hid) == HID_RET_SUCCESS:
			retval = True

		hid_cleanup()

		return retval

	def send(self, packet, timeout=TIMEOUT):
		"""
		Send a USB packet to the connected USB device.
	
		@packet  - Data, in string format, to send to the USB device.
		@timeout - Send timeout, in milliseconds. Defaults to TIMEOUT.
	
		Returns True on success.
		Returns False on failure.
		"""

		tx = 0
		retval = False

		while tx < len(packet):
			hid_ret = hid_interrupt_write(self.hid, self.wep, packet[tx:tx+self.BLOCK_SIZE], timeout)
			
			if hid_ret != HID_RET_SUCCESS:
				retval = False
				raise Exception("hid_interrupt_write failed with error code 0x%X" % hid_ret)
			else:
				tx += self.BLOCK_SIZE
			
		return retval

	def recv(self, count=BLOCK_SIZE, timeout=TIMEOUT):
		"""
		Read data from the connected USB device.
	
		@len     - Number of bytes to read. Defaults to BLOCK_SIZE.
		@timeout - Read timeout, in milliseconds. Defaults to TIMEOUT.
	
		Returns the received bytes on success.
		Returns None on failure.
		"""

		rx = 0
		data = ''

		if count is None:
			count = self.BLOCK_SIZE
		
		while rx < count:
			hid_ret, packet = hid_interrupt_read(self.hid, self.rep, self.BLOCK_SIZE, timeout)

			if hid_ret != HID_RET_SUCCESS:
				print "hid_interrupt_read failed with error code 0x%X" % hid_ret
			else:
				data += packet
				rx += len(packet)

		return data
	
class Gumbi:
	"""
	Primary gumbi class. All other classes that interact with the Gumbi board should be subclassed from this.
	"""

	VID = 0x16C0 
	PID = 0x0480
	ACK = "GUMBIACK"
	NACK = "GUMBINACK"
	MAX_PINS = 128
	RESET_LEN = 1024
	UNUSED = 0xFF
	NULL = "\x00"
	TEST_BYTE = "\xFF"

	NOP = 0
	PFLASH = 1
	SPIFLASH = 2
	SPIEEPROM = 3
	I2CEEPROM = 4
	PING = 5
	INFO = 6
	SPEEDTEST = 7
	GPIO = 8
	GID = 9
	XFER = 10

	EXIT = 0
	READ = 1
	WRITE = 2
	ERASE = 3
	HIGH = 4
	LOW = 5

	MODE_KEY = "MODE"
	MODE_VALUE = None

	def __init__(self, new=True):
		"""
		Class constructor, calls self._open().

		@new  - Set to False to not open a connection to the Gumbi board.
		"""
		self.ts = 0
		self.hid = RawHID(verbose=True)
		if new:
			self._open()

	def _open(self):
		"""
		Opens a connection to the Gumbi board.
		"""
		self.hid.open(self.VID, self.PID)

	def _close(self):
		"""
		Closes the connection with the Gumbi board.
		"""
		self.hid.close()

	def _parse_config_line(self, line):
		"""
		Parses a configuration file line.

		@line - A line from the configuration file.

		Returns the (key, value) pair from the line.
		"""
		key = value = None
		line = line.split('#')[0]
		if '=' in line:
			(key, value) = line.split('=', 1)
			key = key.strip().upper()
			value = value.strip().upper()
			if ',' in value:
				value = value.split(',')
				for i in range(0, len(value)):
					try:
						value[i] = int(value[i])
					except:
						pass
			else:
				try:
					value = [int(value)]
				except:
					pass
		return (key, value)

	def ConfigMode(self, config):
		"""
		Returns the mode specified in a configuration file.

		@config - Configuration file path.

		Returns the mode on success. Returns None on failure.
		"""
		for line in open(config).readlines():
			(key, value) = self._parse_config_line(line)
			if key == self.MODE_KEY:
				return value
		return None

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
		return (self.NULL * count)

	def ReadAck(self):
		"""
		Reads an ACK/NACK from the Gumbi board. Returns True on ACK, raises an exception on NACK.
		"""
		line = self.ReadText() 
		if line != self.ACK:
			print "Instead of ack, I got:", line
			raise Exception(self.ReadText())
		return True

	def SetMode(self, mode):
		"""
		Puts the Gumbi board in the specified mode.
		"""
		self.Write(self.PackByte(mode))
		self.ReadAck()

	def ReadText(self):
		"""
		Reads and returns a new-line terminated string from the Gumbi board.
		"""
		return self.Read().strip(self.NULL)

	def Read(self, n=None):
		"""
		Reads n bytes of data from the Gumbi board. Default n == 1.
		"""
		return self.hid.recv(n)

	def Write(self, data):
		"""
		Sends data to the Gumbi board and verifies acknowledgement.
		"""
		self.hid.send(data)

	def Reset(self):
		"""
		Resets the communications stream with the Gumbi board.
		"""
		self.hid.send(self.PackByte(self.EXIT))
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

	def __init__(self):
		"""
		Class constructor.
		"""
		Gumbi.__init__(self)
		self.SetMode(self.GPIO)

	def _exit(self):
		"""
		Exits the Gumbi board from GPIO mode.
		"""
		self.Write(self.PackBytes([self.EXIT, 0]))
		self.ReadAck()

	def PinHigh(self, pin):
		"""
		Sets the specified pin high.
		"""
		self.Write(self.PackBytes([self.HIGH, self.Pin2Real(pin)]))
		print self.ReadText()
		print self.ReadText()
		print self.ReadText()
		self.ReadAck()

	def PinLow(self, pin):
		"""
		Sets the specified pin low.
		"""
		self.Write(self.PackBytes([self.LOW, self.Pin2Real(pin)]))
		self.ReadAck()

	def ReadPin(self, pin):
		"""
		Reads and returns the value of the specified pin.
		High == 1, Low == 0.
		"""
		self.Write(self.PackBytes([self.READ, self.Pin2Real(pin)]))
		return ord(self.Read()[0])

	def Close(self):
		"""
		Exits GPIO mode, closes the Gumbi board connection.
		"""
		self._exit()
		self._close()

class SpeedTest(Gumbi):
	"""
	Tests the speed of the PC to Gumbi interface.
	"""

	def __init__(self, count):
		"""
		Class constructor.

		@count - Number of bytes to send during the speed test.

		Returns None.
		"""
		Gumbi.__init__(self)
		self.data = ''
		self.count = count
		self.SetMode(self.SPEEDTEST)

	def _test(self):
		"""
		Sends the byte count and reads the data. For internal use only.
		"""
		self.Write(self.Pack32(self.count))
		self.data = self.Read(self.count)

	def Go(self):
		"""
		Runs the speed test.

		Returns the number of seconds it took to transfer self.count bytes.
		"""
		self.StartTimer()
		self._test()
		return self.StopTimer()

	def Validate(self):
		"""
		Validates the received data.

		Returns True if all data was received properly.
		Returns False if data was corrupted.
		"""
		retval = True
		for byte in self.data:
			if byte != self.TEST_BYTE:
				retval = False
				break
		return retval

class TransferTest(Gumbi):

	XFER_SIZE = 128

	def __init__(self):
		self.data = ''
		self.count = self.XFER_SIZE

		Gumbi.__init__(self)
		self.SetMode(self.XFER)

	def _xfer(self):
		self.Write(self.TEST_BYTE * self.count)
		self.data = self.Read(self.count)

	def Go(self):
		self.StartTimer()
		self._xfer()
		return self.StopTimer()

	def Validate(self):
		retval = True
		if len(self.data) >= self.count:
			print "Got %d bytes of data back" % len(self.data)
			for i in range(0, self.count):
				if self.data[i] != self.TEST_BYTE:
					print "data[%d] == 0x%.2X doesn't match expected byte 0x%.2X" % (i, ord(self.data[i]), ord(self.TEST_BYTE))
					retval = False
					#break
		else:
			print "Data len invalid:", len(self.data)
			retval = False

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

	MODE_VALUE = "PARALLEL"
	CONFIG = {
		"TOE"		: [0],
		"ADDRESS"	: [],
		"DATA"		: [],
		"VCC"		: [],
		"GND"		: [],
		"CE"		: [Gumbi.UNUSED, 0],
		"WE"		: [Gumbi.UNUSED, 0],
		"OE"		: [Gumbi.UNUSED, 0],
		"BE"		: [Gumbi.UNUSED, 0],
		"BY"		: [Gumbi.UNUSED, 0],
		"WP"		: [Gumbi.UNUSED, 0],
		"RST"		: [Gumbi.UNUSED, 0]
	}
	
	def __init__(self, config=None, toe=0, address=[], data=[], vcc=[], gnd=[], ce=None, we=None, oe=None, be=None, by=None, wp=None, rst=None):
		if config is None:
			self.CONFIG["TOE"] = [toe]
			self.CONFIG["ADDRESS"] = address
			self.CONFIG["DATA"] = data
			self.CONFIG["VCC"] = vcc
			self.CONFIG["GND"] = gnd
			self.CONFIG["CE"] = ce
			self.CONFIG["WE"] = we
			self.CONFIG["OE"] = oe
			self.CONFIG["BE"] = be
			self.CONFIG["BY"] = by
			self.CONFIG["WP"] = wp
			self.CONFIG["RST"] = rst
		else:
			self.ReadConfig(config)
		
		self._shift_pins()

		Gumbi.__init__(self)
		self.SetMode(self.PFLASH)

	def _shift_pins(self):
		self.CONFIG["ADDRESS"] = self._convert_pin_array(self.CONFIG["ADDRESS"])
		self.CONFIG["DATA"] = self._convert_pin_array(self.CONFIG["DATA"])
		self.CONFIG["VCC"] = self._convert_pin_array(self.CONFIG["VCC"])
		self.CONFIG["GND"] = self._convert_pin_array(self.CONFIG["GND"])
		self.CONFIG["CE"] = self._convert_control_pin(self.CONFIG["CE"])
		self.CONFIG["WE"] = self._convert_control_pin(self.CONFIG["WE"])
		self.CONFIG["OE"] = self._convert_control_pin(self.CONFIG["OE"])
		self.CONFIG["BE"] = self._convert_control_pin(self.CONFIG["BE"])
		self.CONFIG["BY"] = self._convert_control_pin(self.CONFIG["BY"])
		self.CONFIG["WP"] = self._convert_control_pin(self.CONFIG["WP"])
		self.CONFIG["RST"] = self._convert_control_pin(self.CONFIG["RST"])

	def _convert_control_pin(self, cp):
		cpc = (self.UNUSED, 0)
		if cp is not None and len(cp) > 0:
			if len(cp) == 1:
				cpc = (self.Pin2Real(cp[0]), 0)
			else:
				cpc = (self.Pin2Real(cp[0]), cp[1])
		return cpc

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
		data += self.PackByte(self.CONFIG["TOE"][0])
		data += self.Pack16(len(self.CONFIG["ADDRESS"]))
		data += self.Pack16(len(self.CONFIG["DATA"]))
		data += self.Pack16(len(self.CONFIG["VCC"]))
		data += self.Pack16(len(self.CONFIG["GND"]))
		data += self._pack_pins(self.CONFIG["ADDRESS"])
		data += self._pack_pins(self.CONFIG["DATA"])
		data += self._pack_pins(self.CONFIG["VCC"])
		data += self._pack_pins(self.CONFIG["GND"])
		data += self.PackBytes(self.CONFIG["CE"])
		data += self.PackBytes(self.CONFIG["WE"])
		data += self.PackBytes(self.CONFIG["OE"])
		data += self.PackBytes(self.CONFIG["BE"])
		data += self.PackBytes(self.CONFIG["BY"])
		data += self.PackBytes(self.CONFIG["WP"])
		data += self.PackBytes(self.CONFIG["RST"])
		return data

	def ReadConfig(self, config):
		mode_name = self.ConfigMode(config)
		if mode_name != self.MODE_VALUE:
			raise Exception("Wrong mode specified in configuration file. Got '%s', expected '%s'." % (mode_name, self.MODE_VALUE))

		for line in open(config).readlines():
			(key, value) = self._parse_config_line(line)
			if key is not None and value is not None:
				if self.CONFIG.has_key(key):
					self.CONFIG[key] = value

	def ReadFlash(self, start, count):
		data = self._struct(self.READ, start, count)
		self.Write(data)
		self.ReadAck()
		self.ReadAck()
		return self.Read(count)

	def WriteFlash(self, addr, data):
		self.Write(self._struct(self.WRITE, start, len(data)))
		self.Write(data)
		self.ReadAck()
		return self.ReadAck()


if __name__ == '__main__':
#	try:

		info = Info()
		for line in info.Info():
			print line
		info.Close()

#		xfer = TransferTest()
#		xfer.Go()
#		print "Valid?", xfer.Validate()
#		xfer.Close()

#		speed = SpeedTest(0x40000)
#		print "Speed test finished in", speed.Go(), "seconds."
#		print "Data valid:", speed.Validate()
#		print "Data length:", len(speed.data)
#		open("data.bin", "w").write(speed.data)
#		speed.Close()

#		gpio = GPIO()
#		gpio.PinLow(1)
#		time.sleep(10)
#		gpio.Close()

#		flash = ParallelFlash(config="config/39SF020.conf")
#		print "Reading flash..."
#		flash.StartTimer()
#		data = flash.ReadFlash(0, 0x40000)
#		t = flash.StopTimer()
#		flash.Close()

#		print "Read 0x%X bytes of flash data in %f seconds" % (len(data), t)
#		open("flash.bin", "w").write(data)

#	except Exception, e:
###		print "Error:", e
