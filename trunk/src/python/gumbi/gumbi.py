import os
import sys
import time
import math
import struct
import serial
	
class Gumbi:
	"""
	This is the primary Python class used to interface with the Gumbi board and handles 
	the communication with the hardware. In most cases you will not need to interface with 
	this class directly, but rather through a subclass.

	Since all classes that interact with the Gumbi board should be subclassed from this class,
	all the methods in the Gumbi class should be available through any subclass, unless the
	subclass has overridden the method (with few exceptions, overriding Gumbi methods is undesirable).
	"""

	DEBUG = False

	ACK = "A"
	NACK = "N"
	PINS_PER_PORT = 8
	MAX_PINS = 128
	MAX_COMMANDS = 32
	MAX_GPIO_COMMANDS = 31
	MAX_GPIO_BUFFER = 62
	RESET_LEN = 1024
	UNUSED = 0xFF
	NULL = "\x00"
	DUMMY_BYTE = "\xFF"
	SERIAL_PORT = "/dev/ttyACM0"
	
	TBP_DEFAULT = 25
	TOE_DEFAULT = 0

	NOP = 0
	PARALLEL = 1
	PING = 2
	INFO = 3
	SPEEDTEST = 4
	GPIO = 5
	GID = 6
	XFER = 7
	GETPINCOUNT = 8
	SETPINCOUNT = 9
	SCANBUS = 10
	MONITOR = 11
	VOLTAGE = 12

	REGULATORS = {
		0 	: 0x00,
		1	: 0x18,
		1.8	: 0x18,
		2	: 0x18,
		3	: 0x30,
		4.7	: 0x47,
		5	: 0x47
	}

	EXIT = 0
	READ = 1
	WRITE = 2
	HIGH = 3
	LOW = 4
	COMMAND = 5

	MODE_KEY = "MODE"
	MODE_VALUE = None

	def __init__(self, port=None, new=True):
		"""
		Class constructor, opens a connection to the gumbi board.

		@port - Gumbi board serial port, defaults to /dev/ttyACM0.
		@new  - Set to False to not open a connection to the Gumbi board.

		Returns None.
		"""
		self.ts = 0
		self.port = port
		self.num_pins = 0

		if new:
			self._open()

	def _open(self):
		"""
		Opens a connection to the Gumbi board. For internal use only.
		"""
	
		if self.port is not None:
			self.serial = serial.Serial(self.port)
		else:	
			n = 0
			last_error = ''
			prefix = self.SERIAL_PORT[:-1]

			while n < 10:
				try:
					self.port = prefix + str(n)
					self.serial = serial.Serial(self.port)
					break
				except Exception, e:
					last_error = str(e)
					n += 1
					self.port = None

			if self.port is None:
				raise Exception(last_error)
			else:
				self.Reset()

	def _exit(self):
		"""
		Place holder _exit method, called by Close(). 

		This should be overridden by the subclass so that the appropriate exit 
		message may be sent to exit the given mode implemented by the subclass.

		Returns None.
		"""
		return None

	def _close(self):
		"""
		Closes the connection with the Gumbi board. For internal use only.
		"""
		self.serial.close()

	def _flush_serial(self):
		"""
		Flushes the serial port's input and output buffers. For internal use only."
		"""
		self.serial.flushInput()
		self.serial.flushOutput()

	def StartTimer(self):
		"""
		Starts a timer.

		Returns None.
		"""
		self.ts = time.time()

	def StopTimer(self):
		"""
		Stops the timer started by StartTimer().

		Returns the seconds elapsed since StartTimer() was called.
		"""
		return (time.time() - self.ts)

	def Pin2Real(self, pin):
		"""
		Converts user-supplied pin numbers (index 1) to Gumbi board pin numbers (index 0).

		@pin - User supplied pin number.

		Returns the Gumbi board pin number.
		"""
		if pin is not None and pin > 0:
			return (pin - 1)
		else:
			return pin

	def Pack32(self, value):
		"""
		Packs a 32-bit value for transmission to the Gumbi board.

		@value - A 32-bit value to pack.

		Returns a 4 byte string.
		"""
                return struct.pack("<I", value)

        def Pack16(self, value):
		"""
		Packs a 16-bit value for transmission to the Gumbi board.

		@value - A 16-bit value to pack.

		Returns a 2 byte string.
		"""
                return struct.pack("<H", value)

        def PackByte(self, value):
		"""
		Packs an 8-bit value for transmission to the Gumbi board.

		@value - An 8-bit value to pack.

		Returns a 1 byte string.
		"""
                return chr(value)

	def PackDWords(self, data):
		"""
		Packs an array of 32-bit values for transmission to the Gumbi board.

		@data - An array of 32-bit values to pack.

		Returns a string len(data)*4 bytes long.
		"""
		pdata = ''
		for dword in data:
			pdata += self.Pack32(dword)
		return pdata

        def PackBytes(self, data):
		"""
		Packs an array of 8-bit values for transmission to the Gumbi board.

		@data - An array of 8-bit values to pack.

		Returns a string len(data) bytes long.
		"""
                pdata = ''
                for byte in data:
                        pdata += self.PackByte(byte)
                return pdata

	def PackFiller(self, count):
		"""
		Returns count filler bytes of data. Used for filling out unused arrays/structures.

		@count - Number of filler bytes required.

		Returns a string of NULL bytes.
		"""
		return (self.NULL * count)

	def ReadAck(self):
		"""
		Reads an ACK/NACK from the Gumbi board. 

		Returns True on ACK, raises an exception on NACK.
		"""
		line = self.ReadText() 
		if line != self.ACK:
			if line == self.NACK:
				raise Exception("Received NACK from Gumbi board")
			else:
				raise Exception("Received unexpected response from Gumbi board: '%s'" % line)
		return True

	def SetMode(self, mode):
		"""
		Puts the Gumbi board in the specified mode.

		@mode - One of: NOP, PARALLEL, SPI, I2C, PING, INFO, SPEEDTEST, GPIO, GID, XFER, GETPINCOUNT

		Returns None.
		"""
		self.WriteBytes(self.PackByte(mode))
		# ACK acknowledges the receipt of a valid mode
		self.ReadAck()

	def ReadText(self):
		"""
		Reads a new-line terminated ASCII string from the Gumbi board.

		Returns the string read.
		"""
		raw = self.serial.readline()

		if self.DEBUG:
			print ""
			print "ReadText():", raw
			print ""

		return raw.strip()

	def ReadBytes(self, n=None, callback=None):
		"""
		Reads n bytes of data from the Gumbi board.

		@n - Number of bytes to read. If not specified, one byte is read.

		Returns a string of bytes received from the Gumbi board.
		"""
		data = ''

		if n is None:
			n = 1

		try:
			for i in range(0, n):
				data += self.serial.read(1)
				if callback is not None:
					callback(i+1, n)
		except Exception, e:
			print "ReadBytes():", e

		if self.DEBUG:
			print ""
			print "ReadBytes:", len(data)
			for c in data:
				print "\t0x%X" % ord(c)
			print ""

		return data

	def WriteBytes(self, data, callback=None):
		"""
		Sends data to the Gumbi board.
		
		@data - String of bytes to send.

		Returns None.
		"""
		n = len(data)

		try:
			for i in range(0, n):
				self.serial.write(data[i])
				if callback is not None:
					callback(i+1, n)
		except Exception, e:
			print "WriteBytes():", e

		return None

	def Read(self, start, count, callback=None):
		"""
		Reads a number of bytes from the target chip, beginning at the given start address.

		@start - Start address.
		@count - Number of bytes to read.

		Returns a string of bytes read from the chip.
		"""
		self.WriteBytes(self.config.Pack(self.READ, start, count))
	
		# Receive the ACK indicating the provided configuration is valid
		self.ReadAck()
		# Receive the ACK indicating that the specified action is valid
		self.ReadAck()
	
		return self.ReadBytes(count, callback)

	def Write(self, start, data, callback=None):
		"""
		Writes a number of bytes to the target chip, beginning at the given start address.

		@start - Address to start writing at.
		@data  - String of data to write.

		Returns True on success, raises and exception on failure.
		"""
		self.WriteBytes(self.config.Pack(self.WRITE, start, len(data)))
		# Receive the ACK indicating the provided configuration is valid
		self.ReadAck()
		# Receive the ACK indicating that the specified action is valid
		self.ReadAck()
	
		tx = 0
		size = len(data)

		# Write one byte at a time in order to wait for the ACK after each byte is processed.
		while tx < size:
			self.WriteBytes(data[tx:tx+1])

			# Wait for an ACK
			self.ReadAck()
			tx += 1
			if callback is not None:
				callback(tx, size)
		return True

	def ExecuteCommands(self):
		"""
		Runs the commands listed in self.config.CONFIG["COMMANDS"] without any further actions.

		Returns None.
		"""
		self.WriteBytes(self.config.Pack(self.COMMAND, 0, 0))
		# First ACK acknowledges the receipt of a valid configuration
		self.ReadAck()
		# Second ACK acknowledges the receipt of a valid action
		self.ReadAck()
		# Third ACK indicates the completion of the command
		self.ReadAck()

	def PinCount(self, count=0):
		"""
		Gets/sets the number of available I/O pins on the Gumbi board.

		@count - The number of I/O pins to use on the Gumbi board. 
			 If greater than 0, PinCount will change the current setting.
			 If 0 or not specified, PinCount will only get the current setting.

		Returns the number of available I/O pins.
		"""
		if not count or count is None:
			self.SetMode(self.GETPINCOUNT)
		else:
			self.SetMode(self.SETPINCOUNT)
			self.WriteBytes(self.PackByte(count))

		return ord(self.ReadBytes()[0])

	def SetVoltage(self, v):
		"""
		Sets the voltage for the target device connected to the Gumbi board.

		@v - The voltage to set. One of: 0, 1.8, 3, 5.

		Returns None.
		"""
		if self.REGULATORS.has_key(v):
			v = self.REGULATORS[v]
		else:
			v = self.REGULATORS[0]

		self.SetMode(self.VOLTAGE)
		self.WriteBytes(self.PackByte(v))
		# Wait for the ACK indicating the voltage has been set
		self.ReadAck()

	def Reset(self):
		"""
		Attempts to reset the communications stream with the Gumbi board.
		This will exit out of any mode the Gumbi board may be stuck in from a previous unclosed session.

		Returns None.
		"""
		self.WriteBytes(self.EXIT * self.RESET_LEN)
		self._flush_serial()

	def PrintProgress(self, current, total):
		"""
		Displays a progress bar to stdout.

		@current - Current number of bytes.
		@total   - Total number of bytes.

		Returns None.
		"""
		if current > total:
			current = total

		percent = (current / float(total)) * 100
		marks = int(math.floor(percent / 2))
		markstring = "#" * marks
		dotstring = "." * (50 - marks)
		sys.stdout.write("\r[%s%s] %0.2f%% (%d / %d)" % (markstring, dotstring, percent, current, total))
		sys.stdout.flush()

	def Close(self):
		"""
		Closes the connection with the Gumbi board.
		This method MUST be called or else subsequent Gumbi instances may fail.

		Returns None.
		"""
		self._exit()
		return self._close()
