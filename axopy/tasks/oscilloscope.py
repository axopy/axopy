from axopy.application import RealtimeVisualizationTask
from axopy.widgets import OscilloscopeWidget


class Oscilloscope(RealtimeVisualizationTask):
    """
    Simple oscilloscope-like plugin for viewing signals in real-time.

    Parameters
    ----------
    pipeline : Pipeline, optional
        Processing pipeline to use before displaying data from the data
        acquisition device. If None, the raw data is not processed and is
        displayed as-is.
    name : str, optional
        Name of the plugin. If None, uses the class name.
    """

    def __init__(self, pipeline=None):
        super(Oscilloscope, self).__init__()
        self.pipeline = pipeline

        self._setup_ui()

    def _setup_ui(self):
        self._oscope_widget = OscilloscopeWidget()
        self.set_central_widget(self._oscope_widget)

    def on_daq_update(self, data):
        self._oscope_widget.add_window(data)
