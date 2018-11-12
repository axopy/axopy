.. _daq:

================
Data Acquisition
================

.. currentmodule:: axopy.daq

Traditionally, data acquisition (DAQ) refers to the process of capturing and
conditioning signals for recording by a computer. In AxoPy, any source of data
generated or influenced by the subject of the experiment is referred to as
a DAQ.

AxoPy assumes a fairly simple model for collecting data, based on polling.
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

    from axopy.daq import NoiseGenerator

    daq = NoiseGenerator(rate=1000, read_size=100)

    daq.start() # NoiseGenerator doesn't require this, but most do
    for i in range(10):
        data = daq.read()
        process_data(data)
    daq.stop() # again, NoiseGenerator doesn't require this

Here, you'll want to ensure that the ``process_data()`` function does not take
longer than 100 ms to complete, or data acquisition will fall behind the rate
at which it is generated.

Some DAQs are built in to AxoPy, but of course not all of them can be. Check
out pymcc_ and pytrigno_ for a couple examples of working with real data
acquisition hardware.

The DaqStream
=============

One thing to notice about the code above is that every time the ``daq.read()``
operation occurs, *no other code is being run while waiting for the device to
return the new data.* This is sometimes referred to as a blocking operation. In
AxoPy, we usually want some things to be happening *while* the device is
reading in data in the background. This where the :class:`DaqStream` comes in
-- a threaded interface to the underlying hardware.

You'll usually set up your DAQ as above (e.g. ``daq = NoiseGenerator(...)``),
pass it to the :class:`~axopy.experiment.Experiment` as a shared resource, then
the experiment makes the device avaialable to your task implementations in the
form of a :class:`DaqStream`. It has a uniform interface so no matter what kind
of hardware you're using, your task implementation doesn't need to care about
how that all works. You just start/stop and connect/disconnect from the stream.
In order to facilitate this uniform interface, the device the
:class:`DaqStream` wraps needs to expose a specific API as well. This is
defined below:

.. code-block:: text

   Daq
      start - Called once before the first read.
      read  - Request a new buffer of data from the hardware. Parameters (like
              the size of the buffer or number of samples to read should be
              set up in the daq constructor.
      stop  - Called when the user wants the device to stop reading data.


.. _pymcc: https://github.com/ucdrascal/pymcc
.. _pytrigno: https://github.com/ucdrascal/pytrigno
