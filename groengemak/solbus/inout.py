# Definitions for in/out relations to a Modbus, in terms of named
# Coils, Switches, Inputs and HoldingRegisters.


class Coils:
	"""Coils in a Modbus setup can be written to and read from.
	   This class defines a set on any given slave, as a
	   dictionary that maps informal names to their coil number.
	   
	   The same slave may have multiple instances of this class,
	   as well as other classes, defined against it.
	"""

	def __init__ (self, modbus, slave, name2coilnr):
		self.modbus = modbus
		self.slave  = slave
		self.dict   = name2coilnr
		self.vals   = { }

	def __setitem__ (self, coilnm, coilval):
		assert (coilnm in self.dict)
		self.vals [coilnm] = coilval
		self.modbus.write_coil (
					self.slave,
					self.dict [coilnm],
					coilval)

	def __getitem__ (self, coilnm):
		assert (coilnm in self.dict)
		if not coilnm in self.vals:
			coilvals = self.modbus.read_coils (
					self.slave,
					self.dict [coilnm])
			assert (len (coilvals) == 1)
			self.vals [coilnm] = coilvals [0]
		return self.vals [coilnm]


class Switches:
	"""Switches in a Modbus setup are 1-bit values that can be read.
	   This class defines a set on any given slave, as a
	   dictionary that maps informal names to their coil number.
	   
	   The same slave may have multiple instances of this class,
	   as well as other classes, defined against it.
	"""

	def __init__ (self, modbus, slave, name2switchnr):
		self.modbus = modbus
		self.slave  = slave
		self.dict   = name2switchnr
		self.vals   = { }

	def __getitem__ (self, switchnm):
		assert (switchnm in self.dict)
		if not switchnm in self.vals:
			switchvals = self.modbus.read_switches (
					self.slave,
					self.dict [switchnm])
			assert (len (switchvals) == 1)
			self.vals [switchnm] = switchvals [0]
		return self.vals [switchnm]


class Inputs:
	"""Inputs in a Modbus setup define 16-bit values that can
	   be read as desired.
	   
	   The same slave may have multiple instances of this class,
	   as well as other classes, defined against it.
	"""

	def __init__ (self, modbus, slave, name2inputnr):
		self.modbus = modbus
		self.slave  = slave
		self.dict   = name2inputnr

	def __getitem__ (self, inputnm):
		assert (inputnm in self.dict)
		if not inputnm in self.vals:
			inputvals = self.modbus.read_inputs (
					self.slave,
					self.dict [inputnm])
			assert (len (inputvals) == 1)
			self.vals [inputnm] = inputvals [0]
		return self.vals [inputnm]


class HoldingRegisters:
	"""HoldingRegisters in a Modbus setup can be read from and
	   written to, and configure a device.
	   
	   The same slave may have multiple instances of this class,
	   as well as other classes, defined against it.
	"""

	def __init__ (self, modbus, slave, name2holdregnr):
		self.modbus = modbus
		self.slave  = slave
		self.dict   = name2holdregnr
		self.vals   = { }

	def __setitem__ (self, holdregnm, holdregval):
		assert (holdregnm in self.dict)
		self.vals [holdregnm] = holdregval
		self.modbus.write_holdreg (
					self.slave,
					self.dict [holdregnm],
					holdregval)

	def __getitem__ (self, holdregnm):
		assert (holdregnm in self.dict)
		if not holdregnm in self.vals:
			holdregvals = self.modbus.read_holdregs (
					self.slave,
					self.dict [holdregnm])
			assert (len (holdregvals) == 1)
			self.vals [holdregnm] = holdregvals [0]
		return self.vals [holdregnm]

