# Generic Drivers for Solbus, such as Modbus.RS485
#
# From: Rick van Rein <rick@groengemak.nl>


import time


class Solbus (object):
	"""Generic driver class for Solbus, to be inherited by
	   concrete bus drivers.  Each bus supports a number of
	   generic Device kinds that can be driven, each of
	   which introduces data to poll and to write.  It is
	   the purpose of the Solbus to interact with these
	   devices and to schedule their consumption patterns.
	   
	   Devices will be added with a set of modes, for which
	   a few standard names exist:
	   
	     * "off"  is switched off by automation,
	     * "on"   is switched on  by automation,
	     * "man"  is manually overridden.
	"""

	def __init__ (self, name, gridname='home'):
		"""Create a new Driver, and set it up for the given
		   grid (defaulting to the home grid) and match its
		   sampling period.
		"""
		self.name = name
		self.devs = { }
		self.powm = { }
		self.vals = { }
		self.grid = Grid.byname (gridname)
		self.wait = self.grid.period

	def __str__ (self):
		constnm = self.grid.name
		if constnm != 'home':
			return 'Solbus %s@%s' % (self.name,constnm)
		else:
			return 'Solbus %s' % (self.name,)

	def add_device (self, devnm, devobj):
		"""Introduce a new device on the bus.
		   
		   The newly added device will be addressable as
		   a dictionary item from the bus, and its value
		   can be set and get via that route.  The value
		   will be taken from the last poll, if available.
		"""
		assert (devnm not in self.devs)
		self.devs [devnm] = devobj
		self.mode [devnm] = 'init'

	def __getitem__ (self, devnm):
		assert (devnm in self.devs)
		devobj = self.devs [devnm]
		assert (devobj.is_readable)
		if devnm not in self.vals:
			self.vals [devnm] = devobj.get ()
		return self.vals [devnm]

	def __setitem__ (self, devnm, newval):
		assert (devnm in self.devs)
		devobj = self.devs [devnm]
		assert (devobj.is_writeable)
		devobj.set (newval)
		self.vals [devnm] = newval

	def poll (self):
		"""Iterate over the bus to poll bus members.
		   This routine is not usually called by users of
		   this class, but internally as part of running
		   the bus.
		"""
		for (devnm,devobj) in self.devs.iteritems ():
			newvals = { }
			try:
				devval = devobj.get ()
				newvals [devnm] = devval
			except Exception as exc:
				#TODO# Write exc to syslog
				print ('Exception while polling %s on bus %s:\n%s' % (devnm, self.name, exc))
			#TODO# Process changes
			self.vals = newvals

	def run_forever (self):
		"""Run the polling of the bus in a thread-blocking
		   infinite loop.
		"""
		while True:
			#TODO# Mention polling starts on syslog
			self.poll ()
			#TODO# Mention polling ends on syslog
			time.sleep (self.wait)


class Soldev (object):
	"""Generic class for a device on a Solbus.  Actual drivers for
	   devices should inherit from here.
	"""

	def __init__ (self, solbus, name, readable=True, writeable=True):
		"""Setup this device to occur on the given generic
		   Solbus.  By default, it is assumed that the
		   device is both readable and writeable, which
		   can of course be overridden as seen fit.
		"""
		solbus.add_device (name, self)


class PowerClaim (object):
	"""Power claims represent a predicted need for power to come.
	   To this end, it defines a mapping from starting timestamp
	   to how many Watts will be needed from then on.  If the end
	   time is known, it should set 0 Watt from that time on.
	   
	   Power Claims may not always be certain.  They are however
	   assumed to always have a normal distribution, defined by an
	   average (avg) and standard deviation (stddev).  The code
	   is safe to work on with stddev==0 for absolute certainty.
	   The certainty is a function of time, though it is not
	   usually updated to make it completely certain in hindsight,
	   so past values merely indicate what was scheduled for then.
	   
	   Power claims have a priority level, ranging from 10 for
	   manual overrides (which are not usually made explicit) down
	   to 0 for barely important requests.  Priority is also a
	   function of time; heating systems for instance, may need
	   a regular dosage of Watts to maintain desired temperatures.
	   
	   There are a few flags that define how flexible a power claim
	   is.  A claim that can_be_suspended allows temporary
	   interruptions even if power is already being applied.  Claims
	   that can_be_delayed allow insertion of delays between phases
	   of the time sequence.  And claims that can_be_reset allow
	   the breakdown of applied power and will cause a reset.
	   
	   All these forms of flexibility are triggered with methods:
	   suspend/resume, delay, reset.  The PowerClaim subclass can
	   implement these when one of the can_be_ is set to True.  The
	   flags all default to False.  These functions serve a similar
	   purpose as callbacks that would otherwise have been supplied
	   literally.
	"""

	def __init__ (self, name, solbus):
		self.name = name
		self.solbus = solbus
		self.grid = solbus.grid
		self.can_be_suspended = False
		self.can_be_delayed = False
		self.can_be_reset = False
		now = time.time ()
		self.started = now
		self.time2power = { now: 0 }
		self.time2priority = { now: 0 }

	def _str__ (self):
		return 'power claim %s' % (self.name,)


class Grid (object):
	"""Solar systems may consist of multiple Solbus instances,
	   perhaps with different subclasses.  Grids integrate several
	   these Solbus parts to act as a whole.  One Solbus is
	   understood to be dedicated to one Grid.
	   
	   Grids are the places where control is exercised over the
	   power requirements related to Solbus inputs and outputs.
	"""

	name2grid = { }

	@staticmethod
	def byname (name):
		if name not in name2grid:
			name2grid [name] = Grid (name=name)
		return name2grid [name]

	@staticmethod
	def home ():
		return Grid.byname ('home')

	def __init__ (self, name='home', period=300):
		"""Create a new Grid object.  The period sets the
		   sampling period in seconds, defaulting to 5 minutes.
		"""
		self.name = name
		self.list = [ ]
		self.power = 0

	def add_solbus (self, solbus):
		"""Add a Solbus to this Grid.
		"""
		assert (solbus.grid == self)
		self.list.append (solbus)

	def balance_power (self, wattlist):
		"""Add the balance of power for a given number of seconds
		   or 5 minutes otherwise.  Generated solar energie is
		   included as a negative number of watts and actual use
		   from solar or otherwise is positive; the task of the
		   Grid is to schedule devices to come as close to zero
		   as possible.
		   
		   The only interesting thing for balancing power is the
		   sum of wattlist entries; however, it may serve future
		   statistical analysis and trend prediction to see them
		   in the same detail split-up as on the Solbus.
		"""
		self.wattlist = wattlist

	def predict_power (self, wattlist, future=0):
		"""Add an amount of power for the future (default starting
		   now) periods as provided in the wattlist that lists the
		   individual watts for each period.
		"""
		raise NotImplementedError ("predict_power")

	def claim_power (self, claim, after=0, period=None):
		"""Claim power, as specified in a PowerClaim object.
		   The return value is True when approved, or False
		   if not.  In case of approval, the flexibility of
		   the PowerClaim object may be used to suspend, delay
		   or reset to PowerClaim when requirements of higher
		   priority arise, which will then be communicated
		   through the corresponding calls in the claim.  Note
		   that this may mean that a delay or suspension is
		   requested before returning the claim's acceptance.
		"""
		raise NotImplementedError ("claim_power")

	def retract_claim (self, claim):
		"""Retract a power claim after it returned True from
		   a call to claim_power.  It may be recalculated and
		   cycle back into the system.
		"""
		raise NotImplementedError ("retract_claim")

