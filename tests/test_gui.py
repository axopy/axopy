import pytest
import os
from PyQt5 import QtCore, QtWidgets
from axopy import util
from axopy.gui.main import _MainWindow, Container, _SessionConfig


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


def test_session_info_widget(qtbot, mock):
    mock.patch.object(QtWidgets.QMessageBox, 'warning',
                      return_value=QtWidgets.QMessageBox.Ok)

    # single configuration session
    w = _SessionConfig({'subject': str, 'group': ('a', 'b')})

    # if no subject ID is entered, make sure warning is shown and finished
    # signal isn't emitted
    with qtbot.assertNotEmitted(w.finished):
        qtbot.keyPress(w, QtCore.Qt.Key_Return)

    qtbot.keyClicks(w.widgets['subject'], 'p0')
    qtbot.keyPress(w, QtCore.Qt.Key_Return)
    assert w.results == {'subject': 'p0', 'group': 'a'}
