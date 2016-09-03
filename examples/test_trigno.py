"""
Tests communication with and data acquisition from a Delsys Trigno wireless
EMG system.

Delsys Trigno Control Utility needs to be installed and running, and the device
needs to be plugged in.

The tests run by this script are very simple and are by no means exhaustive. It
just sets different numbers of channels and ensures the data received is the
correct shape.
"""

from hcibench import daq

# test single-channel
dev = daq.TrignoDaq((0, 0), 270)
dev.start()
for i in range(4):
    data = dev.read()
    assert data.shape == (1, 270)
dev.stop()

# test multi-channel
dev.set_channel_range((0, 4))
dev.start()
for i in range(4):
    data = dev.read()
    assert data.shape == (5, 270)
dev.stop()
