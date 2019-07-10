# groengemak -> solbus.modbus
#
# Modbus over interfaces like RS-485.
#
# From: Rick van Rein <rick@groengemak.nl>


chr8 = chr
def chr16 (o):
	assert (0 <= o <= 0xffff)
	return chr (o & 0x00ff) + chr (o >> 8)

ord8 = ord
def ord16 (cc):
	assert (len (cc) == 2)
	return ord (cc [0]) + (ord (cc [1]) << 8)


class Modbus:
	"""The generic Modbus class implements functions for
	   driving coils and reading coils, switches and
	   inputs.  The sendmsg and recvmsg methods should be
	   overridden in a subclass.
	"""

	def __init__ (self, name):
		self.name = name

	def sendmsg (self, slave, function, data):
		"""Subclasses should override sendmsg so it
		   can be used to send messages over the
		   Modbus instance.
		"""
		raise NotImplementedError ('subclass needs sendmsg')

	def recvmsg (self, slave, function, datasz, timeout=5):
		"""Subclasses should override recvmsg so it
		   can be used to send messages over the
		   Modbus instance.
		"""
		raise NotImplementedError ('subclass needs recvmsg')

	def write_coil (self, slave, coilnr, value):
		"""Set a value to a single coil.
		"""
		data = chr16 (coilnr) + chr16 (0x00ff if value else 0x0000)
		self.sendmsg (slave, 5, data)
		self.recvmsg (slave, 5, len (data))

	def write_coils (self, slave, coil1, values):
		"""Set a sequence of values to the coils starting
		   from the coil1 number.
		"""
		data = chr16 (coil1) + chr16 (len (values))
		#TODO# Append values, 8 at a time
		self.sendmsg (slave, 15, data)
		self.recvmsg (slave, 15, 4)

	def _read1 (self, slave, function, first, count):
		data = chr16 (first) + chr16 (count)
		self.sendmsg (slave, function, data)
		values = self.recvmsg (slave, function, 1 + ((count + 7) >> 3))
		assert (ord8 (values [0] == count))
		#TODO# Unpack the bit sequence
		return [0] * count

	def read_coils (self, slave, coil1, numcoils=1):
		"""Get a sequence of numcoils values for the coils
		   starting from the coil1 number.
		"""
		return self._read1 (slave, 1, coil1, numcoils)

	def read_switches (self, slave, swi1, numswi=1):
		"""Get a sequence of numswi values for the switches
		   starting from the swi1 number.
		"""
		return self._read1 (slave, 2, swi1, numswi)

	def _read16 (self, slave, function, first, count):
		data = chr16 (first) + chr16 (count)
		self.sendmsg (slave, function, data)
		values = self.recvmsg (slave, function, 1 + 2 * count)
		assert (ord8 (values [0] == count))
		#TODO# Unpack the word sequence
		return [0] * count

	def read_inputs (self, slave, input1, numinputs=1):
		"""Get a sequence of numinputs values for the inputs
		   starting from the input1 number.
		"""
		return self._read16 (slave, 4, input1, numinputs)

	def read_holdregs (self, slave, reg1, numregs=1):
		"""Get a sequence of numregs values for the holding
		   registers starting from the reg1 number.
		"""
		return self._read16 (slave, 3, reg1, numregs)

	def write_holdreg (self, slave, reg, value):
		"""Set a value for a given holding register.
		"""
		data = chr16 (reg) + chr16 (value)
		self.sendmsg (slave, 6, data)
		self.recvmsg (slave, 6, len (data))

	def write_holdregs (self, slave, reg1, values):
		"""Set the given values to the holding registers
		   starting at the reg1 number.
		"""
		data = chr16 (reg1) + chr16 (len (values)) + chr8 (2 * len (values))
		for v in values:
			data += chr16 (v)
		self.sendmsg (slave, 16, data)
		self.recvmsg (slave, 16, 4)


class RS485 (Modbus):
	"""The Modbus class for RS-485 serial connections.
	   There are basic sendmsg and recvmsg methods, but the
	   superclass Modbus defines generic methods that may
	   be more useful, and can be used to drive and read
	   coils and to look at switches and inputs.
	"""

	def __init__ (self, serdev, name=None, baud=9600, ascii=False):
		Modbus.__init__ (self, name or serdev)
		assert (ascii == False)
		serio = open (serdev, 'rw')
		self.serio = serio
		#TODO# set baud rate

	def close (self):
		self.serio.close ()
		self.serio = None

	def _crc (self, msg):
		"""Compute the CRC code for Modbus serial communication.
		"""
		csum = 0xffff
		#DEBUG# print ('CRC init\t0x%04x' % csum)
		for msgb in map (ord, msg):
			csum ^= msgb
			for n in range (8):
				#DEBUG# print ('CRC xord\t0x%04x' % csum)
				#DEBUG# print ('CRC move\t0x%04x|%d' % (csum >> 1, csum & 0x0001))
				if csum & 0x0001 != 0x0000:
					csum ^= 0x14002
					#DEBUG# print ('CRC poly\t0x%04x' % (csum >> 1))
				csum >>= 1
				#DEBUG# print ('CRC next\t0x%04x' % csum)
		return chr8 (csum & 0x00ff) + chr8 (csum >> 8)

	def sendmsg (self, slave, function, data):
		"""Elementary message send routine.  Used internally
		   as part of higher-level functions.  We prefix the
		   slave and function, and append the checksum.
		"""
		msg = chr8 (slave) + chr8 (function) + data
		csum = self._crc (msg)
		msg += csum
		self.serio.write (msg)

	def recvmsg (self, slave, function, datasz, timeout=5):
		"""Elementary message receive routine.  Used internally
		   as part of higher-level functions.  We check that the
		   slave and function are prefixed, and the checksum is
		   appended.
		"""
		#TODO# Use timeout, and know how much to expect
		msg = self.serio.read (1 + 1 + datasz + 2)
		assert (msg [0] == chr8 (slave))
		assert (msg [1] == chr8 (function))
		assert (self._crc (msg [:-2]) == msg [-2:])
		return msg [2:-2]

