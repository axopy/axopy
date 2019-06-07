"""
Async daqs
==========

This examples demonstrates the use of multiple daq devices in an asyncrhonised
fashion. Daqs do not need to have sampling rates that are integer multiples of
one another, yet, it makes sense to set their read_sizes such that it takes
"roughly" the same time to perform a read operation from the various devices.
A DumbDaq is used as a master daq to control the main program update rate.
We might want to set the properties of the master daq to be equal to that of
the "faster" of the real daqs. This is however not strict; we could also set
the read time of the master daq to be even faster (but not slower). In that
case, we would end up with correlated samples as we sample faster than the daqs
are providing data.

The example demonstrates how to store the raw data from the multiple devices
and also how to combine (through concatenation) and store their processed data.
The various devices may provide series of different lengths but interpolation
is not required as the final step of the processing pipeline includes a
feature computation that is performed along the time axis.

If ``rate_m``, ``read_size_m`` and ``counter_m`` are the sampling rate, read
size and the counter limit, respectively, of the master daq, and ``rate`` and
``read_size`` are the rate and read size of a real daq, then the output raw
data array for this device is expected to have shape:
(n_channels, rate * int(counter_m * read_size_m / rate_m)).

The concatenated processed data array will have shape:
(n_total_channels, counter_m), where ``n_total_channels`` is the sum of the
number of channels of the various devices.
"""

import numpy as np
from scipy.signal import butter

from axopy.experiment import Experiment
from axopy.task import Task
from axopy.timing import Counter
from axopy.gui.canvas import Canvas, Text
from axopy.features import mean_absolute_value
from axopy.pipeline import Pipeline, Windower, Callable, Filter


class CountTask(Task):
    def __init__(self, rate, readsize):
        super().__init__()
        self.rate = rate
        self.readsize = readsize
        self.pipeline = {
            'daq_1': self.make_pipeline(rate=self.rate['daq_1'],
                                        readsize=self.readsize['daq_1'],
                                        winsize=250,
                                        lowpass=100,
                                        highpass=500),
            'daq_2': self.make_pipeline(rate=self.rate['daq_2'],
                                        readsize=self.readsize['daq_2'],
                                        winsize=15,
                                        lowpass=5,
                                        highpass=15)
        }
        # This is where the data from the multiple streams will be stored
        # after they have been processed.
        self.cur_data = {'daq_1': None, 'daq_2': None}

    def make_pipeline(self, rate, readsize, winsize, lowpass, highpass):
        b, a = butter(4, (lowpass/rate/2., highpass/rate/2.), 'bandpass')
        pipeline = Pipeline([
            Windower(winsize),
            # overlap = winsize - read_rate
            Filter(b, a=a, overlap=winsize-readsize),
            Callable(mean_absolute_value,
                     func_kwargs={'axis': 1, 'keepdims': True})
        ])

        return pipeline

    def prepare_design(self, design):
        block = design.add_block()
        block.add_trial()

    def prepare_graphics(self, container):
        self.text0 = Text('Master: 0')
        self.text0.pos = -0.2, 0.5

        self.text1 = Text('Daq 1: 0')
        self.text1.pos = -0.2, 0

        self.text2 = Text('Daq 2: 0')
        self.text2.pos = -0.2, -0.5

        canvas = Canvas()
        canvas.add_item(self.text0)
        canvas.add_item(self.text1)
        canvas.add_item(self.text2)
        container.set_widget(canvas)

    def prepare_daq(self, daqstream):
        # The master counter will determine trial time, i.e.
        # trial_time = counter_limit * read_daq / rate_daq
        self.counter0 = Counter(100, reset_on_timeout=False)
        self.counter1 = Counter(1000)
        self.counter2 = Counter(1000)

        self.counter0.timeout.connect(self.finish_trial)

        self.daqstream = daqstream

    def prepare_storage(self, storage):
        self.writer = storage.create_task('async_daqs')

    def run_trial(self, trial):
        trial.add_array('dev_1_raw', stack_axis=1)
        trial.add_array('dev_2_raw', stack_axis=1)
        trial.add_array('dev_12_processed', stack_axis=1)

        self.daqstream['daq_0'].start()
        self.daqstream['daq_1'].start()
        self.daqstream['daq_2'].start()

        self.daqstream['daq_0'].updated.connect(self.update_daq0)
        self.daqstream['daq_1'].updated.connect(self.update_daq1)
        self.daqstream['daq_2'].updated.connect(self.update_daq2)

    def update_daq0(self):
        # Daq 0 is the "master" Daq, i.e. an update happens when daq 0 is
        # updated. The check is used to ensure that updates start only after
        # the two streams have started providing data.
        if not any(elem is None for elem in self.cur_data.values()):
            daq1data = self.cur_data['daq_1'].copy()
            daq2data = self.cur_data['daq_2'].copy()
            data_c = np.concatenate((daq1data, daq2data), axis=0)

            self.trial.arrays['dev_12_processed'].stack(data_c)

            self.counter0.increment()
            self.text0.qitem.setText("Master: " + str(self.counter0.count))

    def update_daq1(self, data):
        self.counter1.increment()
        self.text1.qitem.setText("Daq 1: " + str(self.counter1.count))

        data_proc = self.pipeline['daq_1'].process(data)
        self.cur_data['daq_1'] = data_proc
        self.trial.arrays['dev_1_raw'].stack(data)

    def update_daq2(self, data):
        self.counter2.increment()
        self.text2.qitem.setText("Daq 2: " + str(self.counter2.count))

        data_proc = self.pipeline['daq_2'].process(data)
        self.cur_data['daq_2'] = data_proc
        self.trial.arrays['dev_2_raw'].stack(data)

    def finish_trial(self):
        self.writer.write(self.trial)

        self.daqstream['daq_0'].updated.disconnect(self.update_daq0)
        self.daqstream['daq_1'].updated.disconnect(self.update_daq1)
        self.daqstream['daq_2'].updated.disconnect(self.update_daq2)

        # use wait=False so these don't hang up the final graphics update
        self.daqstream['daq_0'].stop(wait=False)
        self.daqstream['daq_1'].stop(wait=False)
        self.daqstream['daq_2'].stop(wait=False)

        self.next_trial()


if __name__ == '__main__':
    from axopy.daq import NoiseGenerator, DumbDaq
    rate = {'daq_0': 1000, 'daq_1': 2000, 'daq_2': 42}
    readsize = {'daq_0': 100, 'daq_1': 200, 'daq_2': 4}

    daq0 = DumbDaq(rate=rate['daq_0'], read_size=readsize['daq_0'])
    daq1 = NoiseGenerator(num_channels=4, rate=rate['daq_1'],
                          read_size=readsize['daq_1'])
    daq2 = NoiseGenerator(num_channels=2, rate=rate['daq_2'],
                          read_size=readsize['daq_2'])

    exp = Experiment(daq={'daq_0': daq0, 'daq_1': daq1, 'daq_2': daq2},
                     subject='test', allow_overwrite=True)
    exp.run(CountTask(rate, readsize))
