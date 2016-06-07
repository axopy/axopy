import time
import socket
import struct
import numpy as np

try:
    import daqflex
except ImportError:
    pass


class Daq(object):
    """
    A base class which fakes DAQ device functionality by generating random
    data.
    """

    def __init__(self, rate, input_range, channel_range, samples_per_read):
        self.rate = rate
        self.input_range = input_range
        self.samples_per_read = samples_per_read

        self.set_channel_range(channel_range)

    def start(self):
        pass

    def read(self):
        d = 0.2*self.input_range*(
            np.random.rand(self.num_channels, self.samples_per_read) - 0.5)
        time.sleep(float(self.samples_per_read/self.rate))
        return d

    def stop(self):
        pass

    def reset(self):
        pass

    def set_channel_range(self, channel_range):
        self.num_channels = channel_range[1] - channel_range[0] + 1


class MccDaq(Daq):
    """
    Access to data read by a Measurement Computing DAQ.

    Parameters
    ----------
    rate : int
        The sampling rate in Hz
    input_range : int
        Input range for the DAQ (+/-) in volts
    channel_range : tuple with 2 ints
        DAQ channels to use, e.g. (lowchan, highchan) obtains data from
        channels lowchan through highchan
    samples_per_read : int
        Number of samples per channel to read in each read operation

    Examples
    --------
    This is a basic example of how to set up the DAQ, read some data, and
    finish.

    >>> from pygesture import daq
    >>> dev = daq.MccDaq(2048, 1, (0, 1), 1024)
    >>> dev.start()
    >>> data = dev.read()
    >>> dev.stop()
    """

    def __init__(self, rate, input_range, channel_range, samples_per_read):
        self.rate = rate
        self.input_range = input_range
        self.channel_range = channel_range
        self.samples_per_read = samples_per_read

        self._initialize()

    def _initialize(self):
        self.device = daqflex.USB_1608G()

        self.device.send_message("AISCAN:XFRMODE=BLOCKIO")
        self.device.send_message("AISCAN:SAMPLES=0")
        self.device.send_message("AISCAN:BURSTMODE=ENABLE")
        self.device.send_message("AI:CHMODE=SE")

        self.device.send_message("AISCAN:RATE=%s" % self.rate)
        self.device.send_message("AISCAN:RANGE=BIP%sV" % self.input_range)

        self.set_channel_range(self.channel_range)

    def start(self):
        """
        Starts the DAQ so it begins reading data. read() should be called as
        soon as possible.
        """
        self.device.flush_input_data()
        self.device.send_message("AISCAN:START")

    def read(self):
        """
        Waits for samples_per_read samples to come in, then returns the data
        in a numpy array. The size of the array is (NUM_CHANNELS,
        SAMPLES_PER_READ).
        """
        data = self.device.read_scan_data(
            self.samples_per_read*self.num_channels, self.rate)

        data = np.array(data, dtype=np.float)
        data = np.reshape(data, (-1, self.num_channels)).T
        for i in range(self.num_channels):
            data[i, :] = self.device.scale_and_calibrate_data(
                data[i, :],
                -self.input_range,
                self.input_range,
                self.calibration_data[i])
        data = data / float(self.input_range)

        return data

    def stop(self):
        """
        Stops the DAQ. It needs to be started again before reading.
        """
        try:
            self.device.send_message("AISCAN:STOP")
        except:
            print('warning: DAQ could not be stopped')
            pass

    def set_channel_range(self, channel_range):
        self.channel_range = channel_range

        self.calibration_data = []
        for ch in range(channel_range[0], channel_range[1]+1):
            self.calibration_data.append(self.device.get_calib_data(ch))

        self.num_channels = len(self.calibration_data)

        self.device.send_message(
            "AISCAN:LOWCHAN={0}".format(channel_range[0]))
        self.device.send_message(
            "AISCAN:HIGHCHAN={0}".format(channel_range[1]))


class TrignoDaq(object):
    """
    Access to data served by Trigno Control Utility for the Delsys Trigno
    wireless EMG system. TCU is Windows-only, but this class can be used to
    stream data from it on another machine. TCU runs a TCP/IP server, with EMG
    data from the sensors on one port and accelerometer data on another. Only
    EMG data retrieval is currently implemented. The TCU must be running before
    a TrignoDaq object can be instantiated. The signal range of the Trigno
    wireless sensors is 11 mV (according to the user's guide), so scaling is
    performed on the signal to achieve an output ranging from -1 to 1.

    Parameters
    ----------
    channel_range : tuple with 2 ints
        Sensor channels to use, e.g. (lowchan, highchan) obtains data from
        channels lowchan through highchan
    samples_per_read : int
        Number of samples per channel to read in each read operation
    addr : str, default='localhost'
        IP address the TCU server is running on.

    Examples
    --------
    This is a basic example of how to set up the DAQ, read some data, and
    finish.

    >>> from pygesture import daq
    >>> dev = daq.TrignoDaq('127.0.0.1', (0, 1), 1024)
    >>> dev.start()
    >>> data = dev.read()
    >>> dev.close()
    """

    """EMG data sample rate. Cannot be changed."""
    RATE = 2000
    """Port the command server runs on, specified by TCU."""
    CMD_PORT = 50040
    """Port the EMG server runs on, specified by TCU."""
    EMG_PORT = 50041
    """Number of bytes per sample per channel."""
    BYTES_PER_CHANNEL = 4
    """Number of channels in the system."""
    NUM_CHANNELS = 16
    """Minimum recv size in bytes (16 sensors * 4 bytes/channel)."""
    MIN_RECV_SIZE = NUM_CHANNELS * BYTES_PER_CHANNEL
    """Command string termination."""
    COMM_TERM = '\r\n\r\n'
    """Scaling factor to apply to output to get a (-1, 1) range."""
    SCALE = 1 / 0.011

    def __init__(self, channel_range, samples_per_read, addr='localhost'):
        self.channel_range = channel_range
        self.samples_per_read = samples_per_read
        self.addr = addr

        self.input_range = 1
        self.rate = self.RATE

        self._initialize()

    def _initialize(self):
        self.set_channel_range(self.channel_range)

        # create command socket and consume the servers initial response
        self.comm_socket = socket.create_connection(
            (self.addr, self.CMD_PORT), 2)
        self.comm_socket.recv(1024)

        # create the EMG data socket
        self.emg_socket = socket.create_connection(
            (self.addr, self.EMG_PORT), 2)

    def start(self):
        self._send_cmd('START')

    def read(self):
        l_des = self.samples_per_read * self.MIN_RECV_SIZE
        l = 0
        packet = bytes()
        while l < l_des:
            try:
                packet += self.emg_socket.recv(l_des - l)
            except socket.timeout:
                l = len(packet)
                packet += b'\x00' * (l_des - l)
                raise DisconnectException
            l = len(packet)

        data = np.asarray(
            struct.unpack(
                '<'+'f'*self.NUM_CHANNELS*self.samples_per_read, packet))
        data = np.transpose(data.reshape((-1, self.NUM_CHANNELS)))
        data = data[self.channel_range[0]:self.channel_range[1]+1, :]
        data *= self.SCALE
        return data

    def stop(self):
        self._send_cmd('STOP')

    def reset(self):
        self._initialize()

    def __del__(self):
        try:
            self.comm_socket.close()
        except:
            pass

    def set_channel_range(self, channel_range):
        self.channel_range = channel_range
        self.num_channels = channel_range[1] - channel_range[0] + 1

    def _send_cmd(self, command):
        self.comm_socket.send(self._cmd(command))
        resp = self.comm_socket.recv(128)
        self._validate(resp)

    @staticmethod
    def _cmd(command):
        return bytes("{}{}".format(
            command, TrignoDaq.COMM_TERM), encoding='ascii')

    @staticmethod
    def _validate(response):
        s = str(response)
        if 'OK' not in s:
            print("warning: TrignoDaq command failed: {}".format(s))


class DisconnectException(Exception):
    pass
