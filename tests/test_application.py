from axopy.application import NewParticipantDialog


def test_new_participant_dialog(qtbot):
    dialog = NewParticipantDialog()
    qtbot.addWidget(dialog)
    qtbot.keyClicks(dialog.line_edits['pid'], "p0")
    dialog.accept()

    assert dialog.get_data()['pid'] == 'p0'


class CustomParticipantDialog(NewParticipantDialog):
    extra_attributes = [('handedness', 'Handedness'),
                        ('gender', 'Gender')]


def test_custom_participant_dialog(qtbot):
    dialog = CustomParticipantDialog()
    qtbot.addWidget(dialog)
    qtbot.keyClicks(dialog.line_edits['pid'], "p0")
    qtbot.keyClicks(dialog.line_edits['handedness'], "right")
    qtbot.keyClicks(dialog.line_edits['gender'], "male")
    dialog.accept()

    data = dialog.get_data()
    assert data['pid'] == "p0"
    assert data['handedness'] == "right"
    assert data['gender'] == "male"
