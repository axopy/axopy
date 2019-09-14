"""
Multiple DAQs
=============

This example demonstrates how to use multiple data acquisition devices in an
experiment. Here a custom :class:`~axopy.task.Task` is created which shows two
counters that are driven independently by two DAQs with different update rates.
"""

from axopy.experiment import Experiment
from axopy.task import Task
from axopy.daq import NoiseGenerator, DaqStream
from axopy.timing import Counter
from axopy.gui.canvas import Canvas, Text
from axopy import util


class CountTask(Task):

    def prepare_graphics(self, container):
        canvas = Canvas()
        container.set_widget(canvas)

        # create a couple text items that tick with each daq update
        self.text1 = Text('0')
        self.text1.pos = -0.5, 0
        canvas.add_item(self.text1)

        self.text2 = Text('0')
        self.text2.pos = 0.5, 0
        canvas.add_item(self.text2)

        # counters keeping track of the updates
        self.counter1 = Counter(100, reset_on_timeout=False)
        self.counter2 = Counter(100, reset_on_timeout=False)

        # stop updating when the faster DAQ has updated 100 times
        self.counter1.timeout.connect(self.done)

    def prepare_daq(self, daqs):
        # DaqStream objects are provided in the same form as the DAQ objects
        # passed to the Experiment. In this case, they're in a dictionary with
        # names "fast" and "slow".
        self.daq_fast = daqs['fast']
        self.daq_slow = daqs['slow']

        self.daq_fast.updated.connect(self.update1)
        self.daq_slow.updated.connect(self.update2)

    def run(self):
        self.daq_fast.start()
        self.daq_slow.start()

    def update1(self, data):
        self.counter1.increment()
        self.text1.qitem.setText(str(self.counter1.count))

    def update2(self, data):
        self.counter2.increment()
        self.text2.qitem.setText(str(self.counter2.count))

    def done(self):
        self.daq_fast.updated.disconnect(self.update1)
        self.daq_slow.updated.disconnect(self.update2)

        # use wait=False so these don't hang up the final graphics update
        self.daq_fast.stop(wait=False)
        self.daq_slow.stop(wait=False)


if __name__ == '__main__':
    daq1 = NoiseGenerator(read_size=1, rate=25)
    daq2 = NoiseGenerator(read_size=1, rate=10)
    exp = Experiment(daq={'fast': daq1, 'slow': daq2})
    exp.run(CountTask())
