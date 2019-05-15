"""
Simple task with data storage
=============================

Generate random data and process them using a pipeline. Display processed data
on Oscilloscope and store in disk along with the raw data. The task design
includes two experimental conditions, each with a different gain value, which
is used in the final processing step of the pipeline.

Cycle length (in seconds): int(read_size / rate)

Trial length (in seconds): int(read_size / rate) * n_cycles

Size of output data within trial:
    raw : (n_channels, int(read_size / rate) * n_cycles * rate)
    processed : (n_channels, n_cycles)
"""

import numpy as np
from scipy.signal import butter

from axopy.experiment import Experiment
from axopy.task import Task
from axopy import util
from axopy.gui.graph import SignalWidget
from axopy.timing import Counter, Timer
from axopy.pipeline import Windower, Filter, Callable, Pipeline
from axopy.design import Array

class MyTask(Task):
    def __init__(self):
        super(MyTask, self).__init__()
        self.make_display_pipeline()

    def prepare_design(self, design):
        n_trials = 2
        # Two conditions with different set of parameters
        for gain in [1, 3]:
            block = design.add_block()
            for trial in range(n_trials):
                block.add_trial(attrs={
                    'gain': gain
                })
            block.shuffle()

    def prepare_graphics(self, container):
        self.scope = SignalWidget()
        container.set_widget(self.scope)

    def prepare_storage(self, storage):  # TODO
        self.writer = storage.create_task('my_task')

    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()

        # If we want every trial to have specified length we need to use
        # something like this. This is reset at the start of every new trial.
        self.timer = Counter(50)  # number of daq read cycles
        self.timer.timeout.connect(self.finish_trial)

    def make_pipeline(self, gain):
        b, a = butter(4, (10/2000./2., 900/2000./2.), 'bandpass')
        pipeline = Pipeline([
            Windower(250),
            Filter(b, a=a, overlap=150), # overlap = winsize - read_rate
            Callable(lambda x: x[:, 0].reshape(-1, 1)), # Downsampling
            Callable(lambda x: gain * x)
        ])

        return pipeline

    def make_display_pipeline(self):
        # Windower to display something meaningful on Oscilloscope
        self.display_pipeline = Pipeline([
            Windower(30)
        ])

    def run_trial(self, trial):
        # Display trial details in console
        print("Block {}, trial {}, gain {}.".format(
            trial.attrs['block'],
            trial.attrs['trial'],
            trial.attrs['gain']
        ))
        self.reset()
        trial.add_array('data_raw', stack_axis=1)
        trial.add_array('data_proc', stack_axis=1)

        # The processing pipeline is created in each trial because it depends
        # upon the gain defined by the trial
        self.pipeline = self.make_pipeline(trial.attrs['gain'])

        # This is where the magic happens. Every time the a read operation is
        # performed a signal is emitted to process the data and do something
        self.connect(self.daqstream.updated, self.update)

    def reset(self):
        self.timer.reset()
        # Clear data from window used for Oscilloscope. The processing pipeline
        # does not need to be reset because it is overwritten in every trial
        self.display_pipeline.clear()

    def update(self, data):
        # This is the main loop within the trial
        data_proc = self.pipeline.process(data)
        data_display = self.display_pipeline.process(data_proc)
        self.scope.plot(data_display)

        # Update Arrays
        self.trial.arrays['data_raw'].stack(data)
        self.trial.arrays['data_proc'].stack(data_proc)

        self.timer.increment()

    def finish_trial(self):
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.update)

        # Wait 1 second before the new trial
        self.wait_timer = Timer(1)
        self.wait_timer.timeout.connect(self.next_trial)
        self.wait_timer.start()

    def key_press(self, key):
        super(MyTask, self).key_press(key)
        if key == util.key_escape:
            self.finish()

    def finish(self):
        self.daqstream.stop()
        self.finished.emit()


if __name__ == '__main__':
    from axopy.daq import NoiseGenerator
    dev = NoiseGenerator(rate=2000, num_channels=4, amplitude=1.0,
                         read_size=100)

    exp = Experiment(daq=dev, subject='test', allow_overwrite=True)
    exp.run(MyTask())
