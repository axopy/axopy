import pytest
from axopy.experiment.qt import FormDialog


def test_form_dialog(qtbot):
    attrs = [('pid', 'Participant ID'),
             ('handedness', 'Handedness')]
    dialog = FormDialog(attrs)
    qtbot.addWidget(dialog)

    # enter an ID
    qtbot.keyClicks(dialog.line_edits['pid'], "p0")
    qtbot.keyClicks(dialog.line_edits['handedness'], "right")
    dialog.accept()

    data = dialog.get_data()
    assert data['pid'] == "p0"
    assert data['handedness'] == "right"
