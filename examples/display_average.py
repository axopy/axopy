"""
Display scaled average of MAV across channels.

This is a minimal example demonstrating how Tasks should be designed and
which methods they should implement.
"""

import numpy as np
from scipy.signal import butter

from axopy import pipeline
from axopy.experiment import Experiment
from axopy.task import Task
from axopy.timing import Counter
from axopy.gui.canvas import Canvas, Text
from axopy.features import mean_absolute_value
from axopy import util

class FeatureAverage(pipeline.Block):
    """ Compute the average of some feature across channels.
    """

    def __init__(self):
        super(FeatureAverage, self).__init__()

    def process(self, data):
        return data.mean()

class Scaler(pipeline.Block):
    """Multiply by constant value.
    """

    def __init__(self, factor):
        super(Scaler, self).__init__()
        self.factor = factor

    def process(self, data):
        return self.factor * data

class ValuePrint(Task):

    def __init__(self, pipeline):
        """The only thing we need to include in the constructor is the
        pipeline.
        """
        super(ValuePrint, self).__init__()
        self.pipeline = pipeline

    def prepare_design(self, design):
        """Prepare experimental design. Here is where we define the number of
        blocks and trials within each block.
        """
        block = design.add_block()
        block.add_trial(attrs={})

    def prepare_graphics(self, container):
        """Define the GUI by using Items etc.
        """
        self.canvas = Canvas()
        self.text = Text(text='', color='red')
        self.canvas.add_item(self.text)
        container.set_widget(self.canvas)

    def prepare_daq(self, daqstream):
        """Initialize input stream and define how many updates (i.e., cycles)
        take place within each trial (optional).
        """
        self.daqstream = daqstream
        self.daqstream.start()
        # The following two lines define how many cycles will take place within
        # each trial. The length of the trial is n_cycles * (read_size) / rate.
        # When the counter reaches the maximum count value it will send a
        # a signal to start the new trial.
        self.timer = Counter(50)
        self.timer.timeout.connect(self.finish_trial)

    def run_trial(self, trial):
        self.pipeline.clear()
        self.connect(self.daqstream.updated, self.update)

    def update(self, data):
        """Define what happens at each update operation (e.g. )
        """
        data_proc = self.pipeline.process(data)
        self.text.qitem.setText("{:4.4f}".format(data_proc))

        # The following lines tells the timer that an update has happened
        # so as to keep track of the cycles and end the program after n_cycles
        # have happened.
        self.timer.increment()

    def finish_trial(self):
        self.disconnect(self.daqstream.updated, self.update)
        self.next_trial()

    def finish(self):
        self.daqstream.stop()
        self.finished.emit()

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)

if __name__ == '__main__':
    from axopy.daq import NoiseGenerator
    dev = NoiseGenerator(rate=1000, num_channels=4, read_size=100)

    b, a = butter(4, (10/2000./2., 450/2000./2.), 'bandpass')
    pipeline = pipeline.Pipeline([
        pipeline.Windower(200), # 200 ms windows
        pipeline.Filter(b, a=a, overlap=100), #
        pipeline.Callable(mean_absolute_value,
                          func_kwargs={'axis' : 1, 'keepdims' : False}),
        Scaler(factor=5.),
        FeatureAverage()
    ])

    exp = Experiment(daq=dev, subject='test')
    exp.run(ValuePrint(pipeline))
