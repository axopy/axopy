"""Examples of input devices built into AxoPy for testing.

rainbow
    Basic use of an EmulatedDaq to show lots of colorful random data.
keyboard
    Basic use of a Keyboard to show roughly-timed keyboard inputs.
keystick
    Neat use of a filter to get joystick-like inputs from a keyboard.
mouse
    Basic use of a Mouse for velocity input.
"""

# TODO use the above as docstrings for each function and generate the help

import sys
import argparse
import numpy as np
from axopy.task import Oscilloscope
from axopy.experiment import Experiment
from axopy.stream import EmulatedDaq, Keyboard, Mouse
from axopy.pipeline import Pipeline, Callable, Windower, Filter


def rainbow():
    dev = EmulatedDaq(rate=2000, num_channels=16, read_size=200)
    run(dev)


def keyboard():
    dev = Keyboard()
    # need a windower to show something interesting in the oscilloscope
    pipeline = Pipeline([Windower(10)])
    run(dev, pipeline)


def keystick():
    dev = Keyboard(rate=20, keys=list('wasd'))
    pipeline = Pipeline([
        # window to average over
        Windower(10),
        # mean along rows
        Callable(lambda x: np.mean(x, axis=1, keepdims=True)),
        # window to show in the oscilloscope
        Windower(60)
    ])
    run(dev, pipeline)


def mouse():
    dev = Mouse(rate=20)
    pipeline = Pipeline([
        # just for scaling the input since it's in pixels
        Callable(lambda x: x/100),
        # window to show in the oscilloscope
        Windower(40)
    ])
    run(dev, pipeline)


def run(dev, pipeline=None):
    # run an experiment with just an oscilloscope task
    Experiment([Oscilloscope(pipeline)], device=dev).run()


if __name__ == '__main__':
    functions = {
        'rainbow': rainbow,
        'keyboard': keyboard,
        'keystick': keystick,
        'mouse': mouse,
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
