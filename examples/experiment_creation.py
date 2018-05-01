"""Demonstration of several ways to instantiate an experiment.

simple
    The most straightforward usage. You pass the hardware device to create the
    experiment, then run a task. Subject configuration is handled
    automatically.
customized
"""

from axopy.experiment import Experiment
from axopy.task import Oscilloscope
from axopy.stream import EmulatedDaq

daq = EmulatedDaq(rate=2000, num_channels=6, read_size=200)


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

    if config['group'] == 'A':
        print("group A!")

    # run list of tasks
    exp.run(Oscilloscope())


def debug():
    # subject is given, so no configure step is needed
    exp = Experiment(daq=daq, data='/tmp/data', subject='test').run(
        Oscilloscope())


if __name__ == '__main__':
    run()
