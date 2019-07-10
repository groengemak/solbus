# SolBus: Home Automation for Solar Energy

> *SolBus is a management system for solar energy.  The aim is to
> schedule high-power actions in the time that the Sun is producing
> electricity, as much as possible.  This often translates in savings
> that improve the ROI from solar panels.*

SolBus is a general bus mechanism, but it is initially designed
around the common combination of Modbus RTU over RS-485.


## Intro to Modbus RTU and RS-485

The bus protocol for home automation is commonly used.  It used to be
a PLC control bus, but is also quite nice for home automation.

  * RS-485 is a serial protocol that differs from RS-232 by being
    point-to-point but an asynchronous bus connecting multilpe devices.

  * RS-485 also differs from RS-232 in using two wires, usually called
    `A+` and `B-`, carrying symmetric signals over distances that can
    easily span a home.

  * Modbus is a simple query/reply protocol that is often run on RS-485,
    addressing a slave and typical functions are to drive relays and
    read switches or other boolean inputs, or 16-bit values that may have
    come from an analog input, a counter, or such.  One function may work
    on a sequence of relays or inputs.

  * Modbus RTU is the binary version of the protocol that is mandatory
    to implement.  The Modbus ASCII variant is like a hexdump, so it
    hardly adds value and is not often implemented.  It is very common
    to see Modbus RTU devices run over RS-485.

  * Typical Modbus setups use one master and a number of slaves.  There
    is a 16-bit CRC code in Modbus RTU, allowing a multi-master mode if
    masters detect collisions, and retry after a random interval.

End points for Modbus RTU over RS-485 and readily available, and not
necessarily expensive.

Among the devices, there are also relays between RS-232 and RS-485, and
between USB and RS-485.  Either may be useful to plug into a server, though
an RS-232 relay is probably easier to use with embedded hardware such as
a Rasperry Pi or Pyboard.  You should be happy to use USB for your laptop,
to monitor and debug the traffic flow.

Tools also exist, and we will document a few open source variants here.


## Simple Usage Pattern

SolBus is a Python library whose main program looks like a configuration file:

**TODO:IMPRESSION-ONLY**

```
from groengemak import solbus

# Create a bus interface for Modbus over RS-485 at /dev/ttyUSB0
bus = solbus.Modbus (solbus.RS485 ('/dev/ttyUSB0', baud=9600))

# Device 15 on this bus drives relays/coils to operate our boiler
boiler_coils = solbus.Coils (bus, 15, { 'heatpump':2, 'shower':3 })
boiler_coils.heatpump = 0
boiler_coils.shower = 0

# Device 15 also receives temperature measurements
boiler_temps = solbus.Inputs (bus, 15, { 'bottemp':10001, 'toptemp':10002 })

# Create a rule that drives the temperature to 55 degrees Centigrade
range55bot = solbus.rule.Range (boiler_temps.bottemp, high=54)
range55top = solbus.rule.Range (boiler_temps.toptemp, high=54)
range55bad  = solbus.rule.Or (range55bot, range55top)
bus.cause (range55bad, boiler_coils.heatpump)

# Device 13 detects if the shower is running
shower = solbus.Switch (bus, 13, { 'running':1 })

# Create a rule that stops the shower after 20 minutes
shower_ok = solbus.rule.Period (shower.running, start=0, stop=120)
bus.cause (shower_ok, boiler_coils.shower)

# Now run the bus until the end of times
bus.run_forever ()
```

The purpose of the SolBus package is to supply the classes that enable
this kind of scripting, and connect it to a Modbus run over RS-485.


## Running your Controller

The result should easily run on a Raspberry Pi or Pyboard, or similar.
You can also consider running it as a Docker image on a server that you
are already running anyway, using something like `--device=/dev/ttyUSB0`
to pass the serial port into the container.

The result does assume Python, so it is not fit for the smallest of
platforms.  However, to respect even those, we might opt for an export
option that would produce code for a compiler such as SDCC to implement
this protocol on top of a basic read/write API for a serial port.

