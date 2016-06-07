from PyQt5 import QtCore, QtWidgets
from hcibench import daq
from hcibench import pipeline
from hcibench.templates.baseui import Ui_BaseUI


class Plugin(QtWidgets.QWidget):
    """
    Base plugin that does nothing.
    """

    def __init__(self, name=None, parent=None):
        super(Plugin, self).__init__(parent)

        if name is None:
            self._name = self.__class__.__name__
        else:
            self._name = name

    @property
    def name(self):
        return self._name

    def set_recorder(self, recorder):
        self.recorder = recorder

    def setup_recorder(self):
        """
        Register recorder callbacks.
        """
        pass

    def dispose_recorder(self):
        """
        Un-register recorder callbacks.
        """
        pass

    def showEvent(self, event):
        self.setup_recorder()

    def hideEvent(self, event):
        self.dispose_recorder()


class BaseUI(QtWidgets.QMainWindow):
    """
    The base user interface for running experiments.

    Plugins are installed and can be instantiated through the base UI. When a
    plugin becomes visible, it has access to the data acquisition thread and
    receives callbacks when new data becomes available. When the plugin is
    hidden or closed, the data acquisition events go back to the base UI.

    There are two types of plugins that can be added. There are "experiment"
    plugins, which typically read from the DAQ, do some processing, possibly
    interact with an external program, and record data. Experiment plugins
    tend to be complex and you usually don't want to navigate away from them
    once they start running.

    There are also "utility" plugins, which tend to be simpler. An example is
    an oscilloscope for viewing raw DAQ signals. You usually keep these open
    as tabs in the base UI and switch to them as needed.

    Parameters
    ----------
    daq : Daq
        Data acquisition device.
    """

    def __init__(self, daq, parent=None):
        super(BaseUI, self).__init__(parent)

        self.ui = Ui_BaseUI()
        self.ui.setupUi(self)

        self.setWindowTitle("hey")

        self.utilities = {}
        self.ui.menuUtilities.triggered[QtWidgets.QAction].connect(
            self.on_utility_clicked)

        self.daq = daq
        self.record_thread = RecordThread(daq)

    def install_utility(self, plugin, show=False):
        """
        Add a plugin to the UI.

        Parameters
        ----------
        plugin : Plugin
            Any plugin extending the base Plugin class.
        show: bool, optional
            Specifies whether or not the plugin should be added as a tab
            automatically. If True, the plugin is added as a tab in the UI,
            otherwise it can be shown through the Utilities menu.
        """
        name = plugin.name
        plugin.set_recorder(self.record_thread)
        self.utilities[name] = plugin
        action = self.ui.menuUtilities.addAction(name)
        action.setCheckable(True)
        if show:
            action.trigger()

    def install_session(self, plugin):
        """
        Add a session to the UI.

        The session is registered with the BaseUI, so that when the File->New
        action is triggered, the session is a choice in the resulting "new
        session dialog".

        Parameters
        ----------
        session : Plugin
            Any plugin extending the base Plugin class.
        """
        pass

    def on_utility_clicked(self, action):
        name = action.text()
        if action.isChecked():
            self.ui.tabWidget.addTab(self.utilities[name], name)
            self.ui.tabWidget.setCurrentIndex(
                self.ui.tabWidget.indexOf(self.utilities[name]))
        else:
            self.ui.tabWidget.removeTab(
                self.ui.tabWidget.indexOf(self.utilities[name]))

    def showEvent(self, event):
        if not self.record_thread.running:
            self.record_thread.start()

    def closeEvent(self, event):
        if self.record_thread is not None:
            self.record_thread.kill()


class RecordThread(QtCore.QThread):
    """
    Retrieves data from a data acquisition device in a separate thread.

    Signals
    -------
    updated :
        Emits the latest data from the data acquisition unit as processed by
        the pipeline.
    disconnected :
        Emitted when there is a problem with the data acquisition unit.
    """

    updated = QtCore.pyqtSignal(object)
    disconnected = QtCore.pyqtSignal()

    def __init__(self, daq, pipeline=None, parent=None):
        super(RecordThread, self).__init__(parent=parent)
        self.daq = daq

        self._running = False

        if pipeline is None:
            self.pipeline = self._default_pipeline()
        else:
            self.pipeline = pipeline

    @property
    def pipeline(self):
        return self._pipeline

    @pipeline.setter
    def pipeline(self, pipeline):
        was_running = False
        if self._running:
            was_running = True
            self.kill()

        self._pipeline = pipeline

        if was_running:
            self.start()

    def remove_pipeline(self):
        self.pipeline = self._default_pipeline()

    @property
    def running(self):
        return self._running

    def run(self):
        self._running = True

        if self._pipeline is not None:
            self._pipeline.clear()

        self.daq.start()

        while True:
            if not self._running:
                break

            try:
                d = self.daq.read()
            except daq.DisconnectException:
                self.disconnected.emit()
                return

            if self._pipeline is not None:
                self.updated.emit(self._pipeline.process(d))
            else:
                self.updated.emit(d)

        self.daq.stop()

    def kill(self):
        self._running = False
        self.wait()

    def _default_pipeline(self):
        return pipeline.Pipeline(pipeline.PipelineBlock())
