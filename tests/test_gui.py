import pytest
from PyQt5 import QtCore, QtWidgets
from axopy import util
from axopy.gui.main import MainWindow, Container, SessionInfo


def test_main_window(qtbot):
    win = MainWindow()

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
    w = SessionInfo()

    # if no subject ID is entered, make sure warning is shown and finished
    # signal isn't emitted
    with qtbot.assertNotEmitted(w.finished):
        qtbot.mouseClick(w._button, QtCore.Qt.LeftButton)

    qtbot.keyClicks(w._subject_line_edit, 'p0')

    def on_finish_simple(info):
        assert info == {'subject': 'p0'}

    w.finished.connect(on_finish_simple)
    qtbot.mouseClick(w._button, QtCore.Qt.LeftButton)

    # multi-configuration session
    w = SessionInfo(configurations=('a', 'b', 'c'))
    assert w._config_combo_box.count() == 3
    qtbot.keyClicks(w._subject_line_edit, 'p1')

    def on_finish(info):
        assert info == {'subject': 'p1', 'configuration': 'a'}

    w.finished.connect(on_finish)
    qtbot.mouseClick(w._button, QtCore.Qt.LeftButton)
