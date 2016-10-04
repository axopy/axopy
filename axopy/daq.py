import time
import socket
import struct
import numpy as np

try:
    import daqflex
except ImportError:
    pass


class EmulatedDaq(object):
    """
    An emulated data acquisition device which generates random data.

    Each sample of the generated data is sampled from a zero-mean Gaussian
    distribution with variance determined by the amplitude specified, which
    corresponds to three standard deviations. That is, approximately 99.7% of
    the samples should be within the desired peak amplitude.

    :class:`EmulatedDaq` is meant to emulate data acquisition devices that
    block on each request for data until the data is available. See
    :meth:`read` for details.

    Parameters
    ----------
    rate : int, optional
        Sample rate in Hz. Default is 1000.
    num_channels : int, optional
        Number of "channels" to generate. Default is 1.
    amplitude : float, optional
        Approximate peak amplitude of the signal to generate. Specifically, the
        amplitude represents three standard deviations for generating the
        Gaussian distributed data. Default is 1.
    read_size : int, optional
        Number of samples to generate per :meth:`read()` call. Default is 100.
    """

    def __init__(self, rate=1000, num_channels=1, amplitude=1.0,
                 read_size=100):
        self.rate = rate
        self.num_channels = num_channels
        self.amplitude = amplitude
        self.read_size = read_size

        self._sigma = amplitude / 3

        self._t_last_read = None
        self._t_per_read = float(self.read_size / self.rate)

    def start(self):
        pass

    def read(self):
        """
        Generates zero-mean Gaussian data.

        This method blocks (calls ``time.sleep()``) to emulate other data
        acquisition units which wait for the requested number of samples to be
        read. The amount of time to block is calculated such that consecutive
        calls will always return with constant frequency, assuming the calls
        occur faster than required (i.e. processing doesn't fall behind).

        Returns
        -------
        data : ndarray, shape (num_channels, read_size)
            The generated data.
        """
        t = time.time()
        if self._t_last_read is None:
            time.sleep(self._t_per_read)
        else:
            try:
                time.sleep(self._t_per_read - (t - self._t_last_read))
            except ValueError:
                # if we're not meeting real-time requirement, don't wait
                pass

        data = self._sigma * np.random.randn(self.num_channels, self.read_size)

        self._t_last_read = time.time()
        return data

    def stop(self):
        pass

    def reset(self):
        pass


class MccDaq(object):
    """
    Measurement Computing data acquisition device.

    Use of this class requires `PyDAQFlex
    <https://github.com/torfbolt/PyDAQFlex/>`__.

    For more information, refer to the :ref:`User Guide <mcc_daq>`.

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
    devname : str, optional
        Name of the device as implemented in PyDAQFlex.  Default is
        ``'USB_1608G'``.
    """

    def __init__(self, rate, input_range, channel_range, samples_per_read,
                 devname='USB_1608G'):
        self.rate = rate
        self.input_range = input_range
        self.channel_range = channel_range
        self.samples_per_read = samples_per_read

        self.devname = devname

        self._initialize()

    def _initialize(self):
        self.device = getattr(daqflex, self.devname)()

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
    Delsys Trigno wireless EMG system.

    Requires the Trigno Control Utility to be running.

    For more information, refer to the :ref:`User Guide <trigno_daq>`.

    Parameters
    ----------
    channel_range : tuple with 2 ints
        Sensor channels to use, e.g. (lowchan, highchan) obtains data from
        channels lowchan through highchan
    samples_per_read : int
        Number of samples per channel to read in each read operation
    addr : str, default='localhost'
        IP address the TCU server is running on.

    Attributes
    ----------
    RATE : int
        EMG data sample rate.
    CMD_PORT : int
        Port the command server runs on, specified by TCU.
    EMG_PORT : int
        Port the EMG server runs on, specified by TCU.
    BYTES_PER_CHANNEL : int
        Number of bytes per sample per channel.
    NUM_CHANNELS : int
        Number of channels in the system.
    MIN_RECV_SIZE : int
        Minimum recv size in bytes (16 sensors * 4 bytes/channel).
    COMM_TERM : str
        Command string termination.
    SCALE : float
        Scaling factor to apply to output to get a (-1, 1) range.
    """

    RATE = 2000
    CMD_PORT = 50040
    EMG_PORT = 50041
    BYTES_PER_CHANNEL = 4
    NUM_CHANNELS = 16
    MIN_RECV_SIZE = NUM_CHANNELS * BYTES_PER_CHANNEL
    COMM_TERM = '\r\n\r\n'
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
        """
        Tell the device to begin streaming data.

        You should call ``read()`` soon after this, though the device typically
        takes about two seconds to send back the first batch of data.
        """
        self._send_cmd('START')

    def read(self):
        """
        Request a sample of data from the device.

        This is a blocking method, meaning it returns only once the requested
        number of samples are available.
        """
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
        """Tell the device to stop streaming data."""
        self._send_cmd('STOP')

    def reset(self):
        """Restart the connection to the Trigno Control Utility server."""
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
