"""
Built-In Devices
================

This example demonstrates some input devices built into AxoPy for testing as
well as other hardware devices. Pass the following options to try out different
devices:

rainbow
    Basic use of a NoiseGenerator to show lots of colorful random data.
bar
    Basic use of a NoiseGenerator and a Pipeline to show a bar plot using
    temporally filtered data.
polar
    Basic use of a RandomWalkGenerator to with a polar plot.
keyboard
    Basic use of a Keyboard to show roughly-timed keyboard inputs.
keystick
    Neat use of a filter to get joystick-like inputs from a keyboard.
emgsim
    A silly EMG simulator that uses smoothed 'wasd' key presses to modulate the
    amplitude of Gaussian noise -- they kinda look like EMG signals!
mouse
    Basic use of a Mouse for velocity input.
trignoemg
    Delsys Trigno system EMG channels. Requires ``pytrigno``.
trignoacc
    Delsys Trigno system ACC channels. Requires ``pytrigno``.
trignoimu
    Delsys Trigno system IMU channels. Requires ``pytrigno``.
quattroemg
    Delsys Trigno system Quattro EMG channels. Requires ``pytrigno``.
quattroimu
    Delsys Trigno system Quattro IMU channels. Requires ``pytrigno``.
myoemg
    Myo armband EMG channels. Requires ``myo-python`` and ``pydaqs``.
myoimu
    Myo armband IMU channels. Requires ``myo-python`` and ``pydaqs``.
nidaq
    NIDAQ device. Requires ``nidaqmx`` and ``pydaqs``.
blackrock
    Blackrock Neuroport device. Requires ``cbpy`` and ``pydaqs``.
cyberglove
    Cyberglove Systems data glove. Requires ``cyberglove``.
"""

import sys
import argparse
import numpy as np
from axopy.task import Oscilloscope, BarPlotter, PolarPlotter
from axopy.experiment import Experiment
from axopy.daq import NoiseGenerator, RandomWalkGenerator, Keyboard, Mouse
from axopy.pipeline import Pipeline, Callable, Windower


def rainbow():
    num_channels = 16
    dev = NoiseGenerator(rate=2000, num_channels=num_channels, read_size=200)
    channel_names = ['Ch ' + str(i) for i in range(1, num_channels+1)]
    run(dev, channel_names=channel_names)


def bar():
    num_channels = 10
    channel_names = ['Ch ' + str(i) for i in range(1, num_channels+1)]
    dev = NoiseGenerator(
        rate=100,
        num_channels=num_channels,
        amplitude=5.0,
        read_size=10)
    pipeline = Pipeline([
        Windower(100),
        Callable(lambda x: np.mean(x, axis=1, keepdims=True))])
    Experiment(daq=dev, subject='test').run(BarPlotter(
        pipeline=pipeline, channel_names=channel_names,
        group_colors=[[255, 204, 204]], yrange=(-0.5, 0.5)))


def polar():
    num_channels = 5
    dev = RandomWalkGenerator(
        rate=60,
        num_channels=num_channels,
        amplitude=0.03,
        read_size=1)
    # Polar plot can only show non-negative values
    pipeline = Pipeline([Callable(lambda x: np.abs(x))])
    Experiment(daq=dev, subject='test').run(PolarPlotter(
        pipeline, color=[0, 128, 255], fill=True, n_circles=10, max_value=5.))


def keyboard():
    keys = list('wasd')
    dev = Keyboard(keys=keys)
    # need a windower to show something interesting in the oscilloscope
    pipeline = Pipeline([Windower(10)])
    run(dev, pipeline, channel_names=keys)


def keystick():
    keys = list('wasd')
    dev = Keyboard(rate=20, keys=keys)
    pipeline = Pipeline([
        # window to average over
        Windower(10),
        # mean along rows
        Callable(lambda x: np.mean(x, axis=1, keepdims=True)),
        # window to show in the oscilloscope
        Windower(60)
    ])
    run(dev, pipeline, channel_names=keys)


def mouse():
    dev = Mouse(rate=20)
    pipeline = Pipeline([
        # just for scaling the input since it's in pixels
        Callable(lambda x: x/100),
        # window to show in the oscilloscope
        Windower(40)
    ])
    channel_names = list('xy')
    run(dev, pipeline, channel_names=channel_names)


def emgsim():
    keys = list('wasd')
    # sampling rate of the simulated EMG data
    fs = 2000
    # update rate of the generated data
    update_rate = 20
    # gain to use in noise generation
    gain = 0.25
    # number of seconds of data the oscilloscope shows
    osc_view_time = 5

    samp_per_input = int(fs / update_rate)

    pipeline = Pipeline([
        # get keyboard inputs of past second
        Windower(update_rate),
        # take mean over last second and apply a gain
        Callable(lambda x: np.mean(x, axis=1, keepdims=True)),
        # generate noise with amplitude of previous output
        Callable(lambda x, k: gain * x * np.random.randn(x.shape[0], k),
                 func_args=(samp_per_input,)),
        # window for pretty display in oscilloscope
        Windower(osc_view_time * update_rate * samp_per_input),
    ])

    dev = Keyboard(rate=update_rate, keys=keys)
    run(dev, pipeline, channel_names=keys)


def trignoemg():
    from pytrigno import TrignoEMG
    n_channels = 8
    dev = TrignoEMG(
        channels=range(1, n_channels+1),
        samples_per_read=200,
        zero_based=False,
        units='normalized',
        data_port=50043)
    pipeline = Pipeline([Windower(20000)])
    channel_names = ['EMG ' + str(i) for i in range(1, n_channels+1)]
    run(dev, pipeline, channel_names=channel_names)


def trignoacc():
    from pytrigno import TrignoACC
    n_channels = 8
    dev = TrignoACC(
        channels=range(1, n_channels+1),
        samples_per_read=12,
        data_port=50042,
        zero_based=False)
    pipeline = Pipeline([Windower(1200)])
    channel_names = ['Acc ' + str(i) + '_' + axis for i in
                     range(1, n_channels+1) for axis in ['x', 'y', 'z']]
    run(dev, pipeline, channel_names=channel_names)


def trignoimu():
    from pytrigno import TrignoIMU
    n_channels = 2
    dev = TrignoIMU(
        channels=range(1, n_channels+1),
        samples_per_read=12,
        imu_mode='raw',
        data_port=50044,
        zero_based=False)
    pipeline = Pipeline([Windower(1200)])
    channel_names = [mod + '_' + str(i) + '_' + axis
                     for i in range(1, n_channels+1)
                     for mod in ['Acc', 'Gyro', 'Mag']
                     for axis in ['x', 'y', 'z']]
    run(dev, pipeline, channel_names=channel_names)


def quattroemg():
    from pytrigno import QuattroEMG
    n_sensors = 2
    dev = QuattroEMG(
        sensors=range(1, n_sensors+1),
        samples_per_read=200,
        zero_based=False,
        mode=313,
        units='normalized',
        data_port=50043)
    pipeline = Pipeline([Windower(20000)])
    channel_names = [str(i) + channel for i in range(1, n_sensors + 1)
                     for channel in ['A', 'B', 'C', 'D']]
    run(dev, pipeline, channel_names=channel_names)


def quattroimu():
    from pytrigno import QuattroIMU
    n_sensors = 2
    dev = QuattroIMU(
        sensors=range(1, n_sensors + 1),
        samples_per_read=12,
        data_port=50044,
        mode=313,
        zero_based=False)
    pipeline = Pipeline([Windower(1200)])
    channel_names = [str(i) + '_' + axis for i in range(1, n_sensors + 1)
                     for axis in ['a', 'b', 'c', 'd']]
    run(dev, pipeline, channel_names=channel_names)


def myoemg():
    import myo
    from pydaqs.myo import MyoEMG
    # Set the dir where myo-sdk is stored
    myo.init(sdk_path=r'C:\Users\nak142\Coding\myo-python\myo-sdk-win-0.9.0')
    n_channels = 8
    dev = MyoEMG(channels=range(n_channels), samples_per_read=20)
    pipeline = Pipeline([Windower(2000)])
    channel_names = ['EMG ' + str(i) for i in range(1, n_channels+1)]
    run(dev, pipeline, channel_names=channel_names, yrange=(-150, 150))


def myoimu():
    import myo
    from pydaqs.myo import MyoIMU
    myo.init(sdk_path=r'C:\Users\nak142\Coding\myo-python\myo-sdk-win-0.9.0')
    dev = MyoIMU(samples_per_read=5)
    pipeline = Pipeline([Windower(500)])
    channel_names = list('wxyz')
    run(dev, pipeline, channel_names=channel_names)


def nidaq():
    from pydaqs.nidaq import Nidaq
    n_channels = 4
    dev = Nidaq(
        channels=range(n_channels),
        samples_per_read=200,
        rate=2000,
        zero_based=False)
    pipeline = Pipeline([Windower(20000)])
    channel_names = ['EMG ' + str(i) for i in range(1, n_channels+1)]
    run(dev, pipeline, channel_names=channel_names)


def arduino():
    from pydaqs.arduino import ArduinoDAQ
    pins = [0, 1, 2]
    dev = ArduinoDAQ(
        rate=1000,
        port='COM5',
        pins=pins,
        samples_per_read=10,
        zero_based=True)
    pipeline = Pipeline([Windower(10000)])
    channel_names = ['A ' + str(i) for i in pins]
    run(dev, pipeline, channel_names=channel_names, yrange=(0, 1))


def blackrock():
    from pydaqs.blackrock import Blackrock
    from axopy.gui.main import get_qtapp
    n_channels = 1
    # Needed to avoid having Cerelink create the QCoreApplication
    _ = get_qtapp()
    dev = Blackrock(channels=range(1, n_channels + 1), samples_per_read=20)
    pipeline = Pipeline([Windower(5000)])
    channel_names = ['EMG ' + str(i) for i in range(1, n_channels+1)]
    run(dev, pipeline, channel_names=channel_names, yrange=(-1000, 1000))


def cyberglove():
    from cyberglove import CyberGlove
    n_df = 18
    s_port = 'COM6'
    dev = CyberGlove(
        n_df=n_df,
        s_port=s_port,
        samples_per_read=1,
        cal_path=None)
    pipeline = Pipeline([Windower(1000)])
    channel_names = ['DOF ' + str(i) for i in range(1, n_df+1)]
    run(dev, pipeline, channel_names=channel_names, yrange=(0, 200))


def run(dev, pipeline=None, **kwargs):
    # run an experiment with just an oscilloscope task
    Experiment(daq=dev, subject='test').run(Oscilloscope(pipeline, **kwargs))


if __name__ == '__main__':
    functions = {
        'rainbow': rainbow,
        'bar': bar,
        'polar': polar,
        'keyboard': keyboard,
        'keystick': keystick,
        'emgsim': emgsim,
        'mouse': mouse,
        'trignoemg': trignoemg,
        'quattroemg': quattroemg,
        'trignoacc': trignoacc,
        'trignoimu': trignoimu,
        'quattroimu': quattroimu,
        'myoemg': myoemg,
        'myoimu': myoimu,
        'nidaq': nidaq,
        'arduino': arduino,
        'blackrock': blackrock,
        'cyberglove': cyberglove,
    }

    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument(
        'function',
        help='Function in the example script to run.')
    args = parser.parse_args()

    if args.function not in functions:
        print("{} isn't a function in the example.".format(args.function))
        sys.exit(-1)
    else:
        functions[args.function]()
