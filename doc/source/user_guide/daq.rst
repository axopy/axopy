.. _daq:

================
Data Acquisition
================

.. currentmodule:: axopy.daq

Traditionally, a data acquisition (DAQ) refers to the process of capturing and
conditioning signals for recording by a computer. In axopy, sources of data
generated or influenced by the subject of the experiment is referred to as
a DAQ.

axopy assumes a fairly simple model for collecting data, based on polling.
First, the interface is set up -- this might involve initializing a USB
interface, connecting to a TCP server, setting up initial parameters, etc.
Next, data acquisition is started. Some devices don't require an explicit start
command, but some do. Next, you request data from the device. This is
a blocking operation, meaning the request won't return the data until the data
is ready. You're then free to process, display, or save this data. Then, you
request the next batch of data with another request. It is important to make
sure consecutive requests occur frequently enough that you don't fall behind.

For example, imagine you set up a device to acquire data at 1000 Hz in bunches
of 100 samples::

    from axopy.daq import EmulatedDaq

    daq = EmulatedDaq(rate=1000, read_size=100)

    daq.start() # EmulatedDaq doesn't require this, but most do
    for i in range(10):
        data = daq.read()
        process_data(data)
    daq.stop() # again, EmulatedDaq doesn't require this

Here, you'll want to ensure that the ``process_data()`` function does not take
longer than 100 ms to complete, or data acquisition will fall behind the rate
at which it is generated.

Some DAQs are built in to axopy, but of course not all of them can be.

.. _mcc_daq:

Measurement Computing DAQs
--------------------------

:class:`MccDaq` provides access to Measurement Computing USB data acquisition
devices, thanks to `PyDAQFlex <https://github.com/torfbolt/PyDAQFlex/>`__.

This implementation has been verified to work with the USB-1608G, though it
should work with additional hardware. As long as the device supports analog
input, it should *just work* (TM). Start by installing PyDAQFlex on your chosen
platform. On Windows, that *should* be all that's needed. On Linux, you'll need
to install a udev rule (e.g. create a file ``/etc/udev/rules.d/61-mcc.rules``)
for your device to be accessible by non-root users. Populate the file with
a line like the following::

    SUBSYSTEM=="usb", ATTR{idVendor}=="09db", ATTR{idProduct}=="0110", MODE="0666"

Replace the ``idProduct`` attribute with the product ID of your device (the
example above is for the USB-1608G). The product ID can be found using
``lsusb``. After creating the udev rule, you can log out of your account and
log back in. Finally, try running the ``examples/test_mccdaq.py`` script. If no
errors occur, the device should be set up correctly.

.. _trigno_daq:

Trigno Wireless EMG System
--------------------------

:class:`TrignoEMG` and :class:`TrignoAccel` provide access to data served by
Trigno Control Utility for the Delsys Trigno wireless EMG system. TCU is
Windows-only, but this class can be used to stream data from it on another
machine. TCU works by running a TCP/IP server, with EMG data from the sensors
on one port, accelerometer data on another, and commands/responses on yet
another. These ports are configurable in the TCU GUI. The TCU program must be
running before a :class:`TrignoEMG` or :class:`TrignoAccel` object is created.

EMG data is sampled at 2000 Hz and is in volts (by default) with a range of
±0.011 V. This can be converted to millivolts or normalized by the max range to
get a range of ±11 mV or ±1 (unitless), respectively.

Accelerometer data is sampled at 148.1 Hz and is in g.

You can test operation of the device by running `examples/check_trigno.py` to
see if things are set up correctly -- if no errors occur, it should be ready to
go.
