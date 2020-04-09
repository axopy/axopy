from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import (QGridLayout, QPushButton, QComboBox)
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from axopy.messaging import Transmitter


class EnvelopeCalibrationWidget(QtGui.QWidget):
    """EMG envelope calibration widget.

    Consists of two sub-widgets, a ``PlotWidget`` and a ``BarWidget``. There
    are two pushbuttons and optionally a dropdown menu, all of which are
    connected to pyqtsignals emitting the widget's id and the selected value
    in the case of the dropdown menu.

    Parameters
    ----------
    id : object, optional (default=None)
        Widget identifier. This is emitted every time a button is pressed or
        a selection is made from the dropdown menu. If multiple widgets are
        used at the same time, their id's have to be unique so that they are
        distinguishable.
    task_channels : list of str, optional (default=None)
        The task channels that will be offered as options in the dropdown menu.
        If not provided, the dropdown menu will not show up.
    name : str, optional (default=None)
        Widget name that will be displayed.
    size : tuple, optional (default=None)
        Widget size.
    pos : tuple, optional (default=None)
        Widget position.
    autorange : boolean, optional (default=True)
        If ``False`` the autorange option will be disabled from the
        ``PlotWidget``.
    yrange : tuple, optional (default=(-1, 1))
        When ``autorange`` is ``False``, this is the yrange for the
        ``PlotWidget``. When ``autorange`` is ``True``, this will be ignored.

    Attributes
    ----------
    max : Transmitter
        Emits the widget ``id`` (or ``None`` when not provided) when the
        ``max`` button is pressed.
    min : Transmitter
        Emits the widget ``id`` (or ``None`` when not provided) when the
        ``min`` button is pressed.
    reset : Transmitter
        Emits the widget ``id`` (or ``None`` when not provided) when the
        ``reset`` button is pressed.
    active : Transmitter
        Emits the widget ``id`` (or ``None`` when not provided) when the
        widget is activated.
    selected : Transmitter
        Emits the widget ``id`` (or ``None`` when not provided) and the
        selected value from the dropdown menu.
    """

    max = Transmitter(object)
    min = Transmitter(object)
    reset = Transmitter(object)
    active = Transmitter(object)
    selected = Transmitter(object)

    def __init__(self, id=None, task_channels=None, name=None, size=None,
                 pos=None, autorange=True, yrange=(-1, 1)):
        super(EnvelopeCalibrationWidget, self).__init__()
        self.id = id
        self.task_channels = task_channels
        self.name = name
        self.size = size
        self.pos = pos
        self.autorange = autorange
        self.yrange = yrange

        self.init_widget()

    def init_widget(self):
        """Initializes the main widget and adds sub-widgets and menus. """
        if self.name is not None:
            self.setWindowTitle(self.name)

        layout = QGridLayout()
        layout.setSpacing(20)
        self.setLayout(layout)

        # Sub-widgets
        self.emgWidget = pg.PlotWidget(background=None)
        self.emgItem = self.emgWidget.plot(pen='b')
        self.emgWidget.hideAxis('left')
        self.emgWidget.hideAxis('bottom')
        if self.autorange is False:
            self.emgWidget.disableAutoRange(pg.ViewBox.YAxis)
            self.emgWidget.setYRange(*self.yrange)

        self.barWidget = pg.PlotWidget(background=None)
        self.barItem = pg.BarGraphItem(x=[1.], height=[0.], width=1, brush='b')
        self.barWidget.addItem(self.barItem)
        self.barWidget.setYRange(0, 1.3)
        self.barWidget.hideAxis('bottom')
        self.barWidget.showGrid(y=True, alpha=0.5)

        self.reset_button = QPushButton('Reset')
        self.reset_button.resize(self.reset_button.sizeHint())
        self.reset_button.clicked.connect(self.resetButtonClicked)

        self.max_button = QPushButton('max')
        self.max_button.resize(self.max_button.sizeHint())
        self.max_button.clicked.connect(self.maxButtonClicked)

        self.min_button = QPushButton('min')
        self.min_button.resize(self.min_button.sizeHint())
        self.min_button.clicked.connect(self.minButtonClicked)

        if self.task_channels is not None:
            self.select = QComboBox()
            self.select.addItem('Select')
            for task_channel in self.task_channels:
                self.select.addItem(task_channel)
            self.select.currentIndexChanged[str].connect(self.selectActivated)

        layout.addWidget(self.emgWidget, 0, 0, 4, 1)
        layout.addWidget(self.barWidget, 0, 1, 4, 1)
        layout.addWidget(self.reset_button, 1, 2)
        layout.addWidget(self.max_button, 2, 2)
        layout.addWidget(self.min_button, 3, 2)
        if self.task_channels is not None:
            layout.addWidget(self.select, 0, 2)

        # determine layout window
        layout.setColumnStretch(1, 10)
        layout.setColumnStretch(2, 2)
        layout.setColumnStretch(3, 2)

        if self.size is not None:
            self.resize(*self.size)

        if self.pos is not None:
            self.move(*self.pos)

        self.installEventFilter(self)

    def maxButtonClicked(self):
        self.max.emit(self.id)

    def minButtonClicked(self):
        self.min.emit(self.id)

    def resetButtonClicked(self):
        if self.task_channels is not None:
            self.select.setCurrentText('Select')

        self.reset.emit(self.id)

    def selectActivated(self, text):
        if text == 'Select':
            value = None
        else:
            value = text

        self.selected.emit((self.id, value))

    def eventFilter(self, obj, event):
        """Returns ``True`` if the widget is activated. """
        if event.type() == QEvent.WindowActivate:
            self.active.emit(self.id)
            return True
        else:
            return False

    def keyPressEvent(self, e):
        """Keyboard shortcuts.  """
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
        if e.key() == QtCore.Qt.Key_R:
            self.minButtonClicked()
        if e.key() == QtCore.Qt.Key_C:
            self.maxButtonClicked()

    def set_emg_color(self, color):
        """Sets the color for the raw EMG plot widget. """
        self.emgItem.setPen(color)
