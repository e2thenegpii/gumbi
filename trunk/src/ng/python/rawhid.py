from hid import *

class RawHID:
	"""
	HID communications class.
	"""

	READ_ENDPOINT = 0x81
	WRITE_ENDPOINT = 0x02
	INTERFACE = 0

	BLOCK_SIZE = 64
	TIMEOUT = 100000 # milliseconds
	CONNECT_RETRIES = 3

	def __init__(self, verbose=False):
		self.verbose = verbose
		self.hid = None
		self.rep = self.READ_ENDPOINT
		self.wep = self.WRITE_ENDPOINT

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
			self.rep = rep
		if wep is not None:
			self.wep = wep

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

	def flush(self):
		"""
		Flushes the HID receive data.
		"""
		try:
			while True:
				self.recv()
		except:
			return

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
				raise Exception("hid_interrupt_read failed with error code 0x%X" % hid_ret)
			else:
				data += packet
				rx += len(packet)

		return data

