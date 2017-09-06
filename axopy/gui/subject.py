from PyQt5 import QtCore, QtWidgets


class ParticipantSelector(QtWidgets.QWidget):
    """A composite QWidget for creating and selecting participants.

    The layout consists of a `QListWidget` with each item representing a
    participant (text is the participant ID) and a button to create a new
    participant with a modal dialog. The modal dialog is populated with
    customizable fields (see `extra_args`).

    When a participant is selected from the list, a dictionary is emitted
    via the `selected` signal. The dictionary always contains a 'pid' item and
    any other items added via the `extra_args` list.

    Parameters
    ----------
    extra_attrs : list, optional
        Additional participant attributes for the researcher to fill in. Each
        attribute should be a tuple `('id', 'label')`, where the id is used as
        a key in the returned data and the label is the text shown next to the
        attribute's input box in the dialog.
    parent : QObject, optional
        Qt parent object.

    Attributes
    ----------
    selected : pyqtSignal
        Signal emitted when a participant is selected from the list.
    """

    selected = QtCore.pyqtSignal(dict)

    def __init__(self, extra_attrs=None, parent=None):
        super(ParticipantSelector, self).__init__(parent=parent)
        self._setup_ui()

        self.participant_attrs = ['id']
        if extra_attrs is not None:
            self.participant_attrs.extend(extra_attrs)

        self.participants = {}

        self.current_selection = None

    def add_participant(self, participant):
        """Add a participant to the list.

        Parameters
        ----------
        participant : str or dict
            Participant data. If just a string is used, it is assumed to be the
            participant's ID. If a dictionary is used, it may include
            additional attributes (e.g. handedness, age, etc.), but it must
            include a 'pid' item.
        """
        if isinstance(participant, str):
            participant = {'id': participant}

        self.participants[participant['id']] = participant
        self.list_widget.addItem(participant['id'])

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self._select_participant()

    def _setup_ui(self):
        """User interface setup for __init__ cleanliness."""
        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel(self)
        self.main_layout.addWidget(self.label)

        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.setAlternatingRowColors(True)
        self.main_layout.addWidget(self.list_widget)

        self.new_button = QtWidgets.QPushButton("New Participant")
        self.new_button.clicked.connect(self._on_new_participant)
        self.main_layout.addWidget(self.new_button)

    def _on_new_participant(self):
        """Callback for when the "New Participant" button is pressed.

        Opens up a FormDialog to enter informaiton, then does some checking to
        make sure the entered information makes sense.
        """
        attrs = [(a, a) for a in self.participant_attrs]
        dialog = FormDialog(attrs)
        if not dialog.exec_():
            return

        data = dialog.get_data()
        pid = data['id']

        # make sure a participant ID was entered
        if pid == '':
            QtWidgets.QMessageBox().warning(
                self,
                "Warning",
                "Participant ID must not be empty.",
                QtWidgets.QMessageBox.Ok)
            return

        # make sure the participant ID doesn't already exist
        found = self.list_widget.findItems(pid, QtCore.Qt.MatchExactly)
        if found:
            # participant ID already in the list, select and show warning
            match = found[0]
            self.list_widget.setCurrentItem(match)
            QtWidgets.QMessageBox().warning(
                self,
                "Warning",
                "Participant '{}' already exists.".format(pid),
                QtWidgets.QMessageBox.Ok)
            return

        self.add_participant(data)

    def _select_participant(self):
        """Callback for when an item in the list is selected."""
        item = self.list_widget.currentItem()
        if item is None:
            return
        pid = item.text()
        participant = self.participants[pid]
        self.selected.emit(participant)


class FormDialog(QtWidgets.QDialog):
    """A simple form dialog for entering information.

    The dialog just contains a set of rows with a `QLabel` and a `QLineEdit`
    in each row. Ok and Cancel buttons are below to accept or cancel the input.

    In normal usage, the dialog is shown, the researcher enters the information
    and accepts it by clicking the Ok button, then the data can be retrieved
    with the `get_data` method.

    Parameters
    ----------
    attrs : list
        Form elements for the researcher to fill in. Each attribute should be a
        tuple `('id', 'label')`, where the id is used as a key in the returned
        data and the label is the text shown next to the attribute's input box
        in the dialog.
    parent : QWidget, optional
        Parent widget of the dialog.
    """

    def __init__(self, attrs, parent=None):
        super(FormDialog, self).__init__(parent=parent)
        self.attrs = attrs
        self._init_ui()

    def _init_ui(self):
        """Construct widgets in the form layout."""
        self.form_layout = QtWidgets.QFormLayout()
        self.line_edits = {}

        for attr, label in self.attrs:
            edit = QtWidgets.QLineEdit()
            self.line_edits[attr] = edit
            self.form_layout.addRow(label, edit)

        button_box = QtWidgets.QDialogButtonBox()
        button_box.setOrientation(QtCore.Qt.Horizontal)
        button_box.setStandardButtons(
            QtWidgets.QDialogButtonBox.Cancel |
            QtWidgets.QDialogButtonBox.Ok)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.form_layout)
        layout.addWidget(button_box)
        self.setLayout(layout)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def get_data(self):
        """Retrieves the data entered in the dialog's fields.

        Returns
        -------
        data : dict
            Dictionary of attributes with the attribute `id`s as keys and the
            entered text as values.
        """
        return {a: str(e.text()) for a, e in self.line_edits.items()}
