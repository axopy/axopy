"""
Experiment Setup Options
========================

Demonstration of several ways to instantiate an experiment.

simple
    The most straightforward usage. You pass the hardware device to create the
    experiment, then run a task. Subject configuration is handled
    automatically.
customized
    A customized experiment setup. A "config" step is used before
    ``Experiment.run()`` to allow the researcher to select the subject group
    for the current session ("A" or "B").
"""

import argparse
from axopy.experiment import Experiment
from axopy.task import Oscilloscope
from axopy.daq import NoiseGenerator

daq = NoiseGenerator(rate=2000, num_channels=6, read_size=200)


def run():
    """Main function of the example. Runs each demo and then exits."""
    customized()


def simple():
    # subject is not given, so it is configured in run
    exp = Experiment(daq=daq).run(Oscilloscope())


def customized():
    exp = Experiment(daq=daq)

    # optional config step, subject field is implied
    config = exp.configure(group=('A', 'B'))

    # here you can retrieve the selected group via `config['group']`

    # run list of tasks
    exp.run(Oscilloscope())


def debug():
    # subject is given, so no configure step is needed
    exp = Experiment(daq=daq, data='/tmp/data', subject='test').run(
        Oscilloscope())


if __name__ == '__main__':
    functions = {
        'simple': simple,
        'customized': customized,
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
