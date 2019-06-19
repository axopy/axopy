"""
Built-In Devices
================

This example demonstrates some input devices built into AxoPy for testing as
well as other hardware devices. Pass the following options to try out different
devices:

rainbow
    Basic use of an NoiseGenerator to show lots of colorful random data.
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
myoemg
    Myo armband EMG channels. Requires ``myo-python``.
myoimu
    Myo armband IMU channels. Requires ``myo-python``.
cyberglove
    Cyberglove Systems data glove. Requires ``cyberglove``.
"""

import sys
import argparse
import numpy as np
from axopy.task import Oscilloscope
from axopy.experiment import Experiment
from axopy.daq import NoiseGenerator, Keyboard, Mouse
from axopy.pipeline import Pipeline, Callable, Windower, Filter, Ensure2D

from axopy.pipeline import Block


def rainbow():
    num_channels = 16
    dev = NoiseGenerator(rate=2000, num_channels=num_channels, read_size=200)
    channel_names = ['Ch ' + str(i) for i in range(1, num_channels+1)]
    run(dev, channel_names=channel_names)


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
    run(dev, pipeline, keys)


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
    run(dev, pipeline, keys)

def trignoemg():
    from pytrigno import TrignoEMG
    num_channels = 16
    dev = TrignoEMG(channels=range(num_channels), samples_per_read=200,
                    units='normalized')
    pipeline = Pipeline([Callable(lambda x: 5*x), Windower(20000)])
    channel_names = ['EMG ' + str(i) for i in range(1, num_channels+1)]
    run(dev, pipeline, channel_names)


def trignoacc():
    from pytrigno import TrignoACC
    n_channels = 16
    dev = TrignoACC(channels=range(n_channels), samples_per_read=12)
    pipeline = Pipeline([Windower(1200)])
    channel_names = ['Acc ' + str(i) + '_' + axis \
                     for i in range(1, n_channels+1) for axis in ['x','y','z']]
    run(dev, pipeline, channel_names)


def myoemg():
    import myo
    from myo import MyoDaqEMG
    myo.init(sdk_path=r'C:\Users\nak142\Coding\myo-python\myo-sdk-win-0.9.0')
    n_channels = 8
    dev = MyoDaqEMG(channels=range(n_channels), samples_per_read=20)
    pipeline = Pipeline([Callable(lambda x: 0.01*x), Windower(2000)])
    channel_names = ['EMG ' + str(i) for i in range(1, n_channels+1)]
    run(dev, pipeline, channel_names)


def myoimu():
    import myo
    from myo import MyoDaqIMU
    myo.init(sdk_path=r'C:\Users\nak142\Coding\myo-python\myo-sdk-win-0.9.0')
    dev = MyoDaqIMU(samples_per_read=5)
    pipeline = Pipeline([Windower(500)])
    channel_names = list('wxyz')
    run(dev, pipeline, channel_names)


def cyberglove():
    from cyberglove import CyberGlove
    n_df = 18
    dev = CyberGlove(n_df, 'COM3', samples_per_read=1,
                     cal_path=r"C:\Users\nak142\tmp\glove.cal")
    pipeline = Pipeline([Ensure2D('row'), Windower(1000)])
    channel_names = ['DOF ' + str(i) for i in range(1, n_df+1)]
    run(dev, pipeline, channel_names)

def mouse():
    dev = Mouse(rate=20)
    pipeline = Pipeline([
        # just for scaling the input since it's in pixels
        Callable(lambda x: x/100),
        # window to show in the oscilloscope
        Windower(40)
    ])
    channel_names = list('xy')
    run(dev, pipeline, channel_names)


def run(dev, pipeline=None, channel_names=None):
    # run an experiment with just an oscilloscope task
    Experiment(daq=dev, subject='test').run(Oscilloscope(
        pipeline, channel_names))


if __name__ == '__main__':
    functions = {
        'rainbow': rainbow,
        'keyboard': keyboard,
        'keystick': keystick,
        'emgsim': emgsim,
        'mouse': mouse,
        'trignoemg': trignoemg,
        'trignoacc': trignoacc,
        'myoemg': myoemg,
        'myoimu': myoimu,
        'cyberglove': cyberglove
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
