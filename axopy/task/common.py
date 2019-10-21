"""Some generic task implementations."""

from axopy.task import Task
from axopy import util
from axopy.gui.graph import SignalWidget, BarWidget, PolarWidget


class _Visualizer(Task):
    """
    Abstract class for data visalization. Not intended to be used directly. Use
    derived classes instead.
    """

    def __init__(self, pipeline=None):
        super(_Visualizer, self).__init__()
        self.pipeline = pipeline
        self.scope = None

    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.connect(daqstream.updated, self.update)

    def run(self):
        self.daqstream.start()

    def update(self, data):
        if self.pipeline is not None:
            data = self.pipeline.process(data)
        self.scope.plot(data)

    def key_press(self, key):
        if key == util.key_return:
            self.daqstream.stop()
            self.finish()


class Oscilloscope(_Visualizer):
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
    kwargs : key, value mappings
        Other keyword arguments are passed through to SignalWidget.
    """

    def __init__(self, pipeline=None, **kwargs):
        super(Oscilloscope, self).__init__(pipeline=pipeline)
        self.kwargs = kwargs

    def prepare_graphics(self, container):
        self.scope = SignalWidget(**self.kwargs)
        container.set_widget(self.scope)


class BarPlotter(_Visualizer):
    """A bar plot visualizer.

    This task connects to the experiment input DAQ and displays the different
    channels as a bar plot. You can optionally pass a :class:`Pipeline` object
    to preprocess the input data before displaying it.

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
    kwargs : key, value mappings
        Other keyword arguments are passed through to BarWidget.
    """

    def __init__(self, pipeline=None, **kwargs):
        super(BarPlotter, self).__init__(pipeline=pipeline)
        self.kwargs = kwargs

    def prepare_graphics(self, container):
        self.scope = BarWidget(**self.kwargs)
        container.set_widget(self.scope)


class PolarPlotter(_Visualizer):
    """ A polar plot visualizer.

    This task connects to the experiment input DAQ and displays the different
    channels as a polar plot. You can optionally pass a :class:`Pipeline` object
    to preprocess the input data before displaying it.

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
    kwargs : key, value mappings
        Other keyword arguments are passed through to PolarWidget.
    """

    def __init__(self, pipeline=None, **kwargs):
        super(PolarPlotter, self).__init__(pipeline=pipeline)
        self.kwargs = kwargs

    def prepare_graphics(self, container):
        self.scope = PolarWidget(**self.kwargs)
        container.set_widget(self.scope)
