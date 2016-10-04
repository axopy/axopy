"""
Tests communication with and data acquisition from a Measurement Computing
USB1608G DAQ.

DAQFlex needs to be installed in addition to pydaqflex, and on Linux, a udev
rule needs to be added (see `tools/60-mcc.rules` in the main repo directory).
Of course, the device should be connected to the computer.

The tests run by this script are very simple and are by no means exhaustive. It
just sets different numbers of channels and ensures the data received is the
correct shape.
"""

from axopy import daq

# test single-channel first
dev = daq.MccDaq(2048, 1, (0, 0), 1024)
dev.start()
for i in range(4):
    data = dev.read()
    assert data.shape == (1, 1024)
dev.stop()

# test multi-channel
dev.set_channel_range((0, 3))
dev.start()
for i in range(4):
    data = dev.read()
    assert data.shape == (4, 1024)
dev.stop()
