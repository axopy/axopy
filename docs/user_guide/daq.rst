.. _daq:

================
Data Acquisition
================

.. currentmodule:: axopy.daq

Traditionally, a data acquisition (DAQ) refers to the process of capturing and
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

.. _pymcc: https://github.com/ucdrascal/pymcc
.. _pytrigno: https://github.com/ucdrascal/pytrigno
