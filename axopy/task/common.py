"""Some generic task implementations."""

from axopy.task import Task
from axopy import util
from axopy.messaging import Transmitter
from axopy.gui.graph import SignalWidget


class Oscilloscope(Task):
    """A visualizer for data acquisition devices.

    This task connects to the experiment input DAQ and displays each of its
    channels on a separate plot. You can optionally pass a :class:`Pipeline`
    object to preprocess the input data before displaying it.

    Parameters
    ----------
    pipeline : Pipeline, optional
        Pipeline to run the input data through before displaying it. Often this
        is some preprocessing like filtering. It is often useful to use a
        :class:`Windower` in the pipeline to display a larger chunk of data
        than is given on each input update of the DAQ. This gives a "scrolling"
        view of the input data, which can be helpful for experiment setup (e.g.
        placing electrodes, making sure the device is recording properly,
        etc.).
    """

    def __init__(self, pipeline=None):
        super(Oscilloscope, self).__init__()
        self.pipeline = pipeline

    def prepare_graphics(self, container):
        self.scope = SignalWidget()
        container.set_widget(self.scope)

    def prepare_input_stream(self, input_stream):
        self.input_stream = input_stream
        self.connect(input_stream.updated, self.update)

    def run(self):
        self.input_stream.start()

    def update(self, data):
        if self.pipeline is not None:
            data = self.pipeline.process(data)
        self.scope.plot(data)

    def key_press(self, key):
        if key == util.key_return:
            self.input_stream.kill()
            self.finish()
