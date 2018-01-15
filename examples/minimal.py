from axopy.task import Oscilloscope
from axopy.experiment import Experiment
from axopy.stream import EmulatedDaq

if __name__ == '__main__':
    dev = EmulatedDaq(rate=2000, num_channels=4, read_size=200)
    Experiment([Oscilloscope()], device=dev).run()
