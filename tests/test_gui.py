import pytest
import os
from PyQt5 import QtCore, QtWidgets
import numpy as np
from axopy import util
from axopy.gui.main import _MainWindow, Container, _SessionConfig
from axopy.gui.graph import SignalWidget, BarWidget
from axopy.gui.canvas import Canvas, Circle, Cross, Line, Text, Rectangle


def exercise_item(item):
    """Put a canvas item through the motions."""
    assert hasattr(item, 'qitem')

    item.x = 0.5
    item.y = -0.5
    assert item.pos == (0.5, -0.5)

    item.pos = 1, 1
    assert item.x == 1
    assert item.y == 1

    item.visible = False
    item.opacity = 0.4

    item.hide()
    assert not item.visible

    item.show()
    assert item.visible


def test_main_window(qtbot):
    win = _MainWindow()

    # create and set container manually
    c2 = Container()
    win.set_container(c2)
    assert win._layout.currentWidget() == c2

    # implicitly create and set container
    c = win.new_container()
    assert win._layout.currentWidget() == c

    win.set_status("status message")

    def on_key_press(key):
        assert key == util.key_a

    win.key_pressed.connect(on_key_press)

    qtbot.keyClicks(c, 'a')


def test_container_widget():
    c = Container()
    c.set_widget(QtWidgets.QWidget())


def test_container_layout():
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(QtWidgets.QPushButton())
    layout.addWidget(Canvas())

    c = Container()
    c.set_layout(layout)


def test_session_info_bad_type():
    with pytest.raises(TypeError):
        _SessionConfig({'obj': object})


def test_session_info_no_subject(qtbot, mocker):
    mocker.patch.object(QtWidgets.QMessageBox, 'warning',
                        return_value=QtWidgets.QMessageBox.Ok)

    w = _SessionConfig({'subject': str})
    qtbot.add_widget(w)

    with qtbot.assertNotEmitted(w.finished):
        qtbot.keyPress(w, QtCore.Qt.Key_Return)


def test_session_info_types(qtbot):
    w = _SessionConfig({
        'subject': str,
        'group': ('a', 'b'),
        'age': int,
        'height': float,
    })
    qtbot.add_widget(w)

    qtbot.keyClicks(w.widgets['subject'], 'p0')
    qtbot.keyClicks(w.widgets['age'], '99')
    qtbot.keyClicks(w.widgets['height'], '46.2')
    qtbot.keyPress(w, QtCore.Qt.Key_Return)

    expected = {'subject': 'p0', 'group': 'a', 'age': 99, 'height': 46.2}
    assert w.results == expected


def test_container():
    c = Container()
    c.set_widget(QtWidgets.QWidget())


def test_signal_widget():
    w = SignalWidget()

    w.plot(np.random.randn(4, 100))
    assert w.n_channels == 4

    # adjusts to plotting data with different shape
    w.plot(np.random.randn(10, 1000))
    assert w.n_channels == 10


def test_bar_widget():
    w = BarWidget()

    w.plot(np.random.randn(4, 3))
    assert w.n_channels == 4
    assert w.groups == 3

    # adjusts to plotting data with different shape
    w.plot(np.random.randn(10, 5))
    assert w.n_channels == 10
    assert w.groups == 5


def test_canvas():
    c = Canvas()
    c.add_item(Circle(0.1))
    c.add_item(Circle(0.1).qitem)


@pytest.mark.parametrize('cls,args,kwargs', [
    (Circle, [0.05], dict()),
    (Cross, [], dict(size=0.08, linewidth=0.02)),
    (Line, [0, 0, 1, 1], dict()),
    (Text, ['hello'], dict()),
    (Rectangle, [0.5, 0.5], dict(x=0.5, y=0.5)),
])
def test_items(cls, args, kwargs):
    item = cls(*args, **kwargs)
    exercise_item(item)


def test_rectangle():
    it = Rectangle(0.1, 0.1)
    assert it.width == 0.1
