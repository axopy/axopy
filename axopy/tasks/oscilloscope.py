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

        self._oscope_widget = OscilloscopeWidget()
        self.set_central_widget(self._oscope_widget)

    def setup_daq(self):
        self._daq_thread = self.base_ui.daq_thread
        if self.pipeline is None:
            self._daq_thread.remove_pipeline()
        else:
            self._daq_thread.pipeline = self.pipeline
        self._daq_thread.updated.connect(self._on_daq_update)
        self._daq_thread.start()

    def shutdown_daq(self):
        self._daq_thread.updated.disconnect(self._on_daq_update)
        self._daq_thread.kill()

    def _on_daq_update(self, data):
        self._oscope_widget.add_window(data)
