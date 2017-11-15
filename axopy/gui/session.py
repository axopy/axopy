from PyQt5 import QtCore, QtWidgets


class SessionInfoWidget(QtWidgets.QWidget):
    """Widget for setting up a session.

    Shows a combo box for selecting the experiment configuration (if there are
    multiple) and a text box for entering the subject ID. Connect to the
    ``finished`` signal to receive a dictionary containing the subject ID and
    the configuration (if applicable).

    Parameters
    ----------
    configurations : sequence, optional
        Sequence of strings representing possible session configurations. These
        are displayed in a combo box. If `None`, the combo box isn't displayed.

    Attributes
    ----------
    finished : pyqtSignal
        Signal emitted when the session info has been entered. The info is a
        dictionary ``{'subject': '<subject_id>', 'configuration':
        '<config_id>'}``. The ``configuration`` item is not included if there
        are not multiple configurations to choose from.
    """

    finished = QtCore.pyqtSignal(dict)

    def __init__(self, configurations=None, parent=None):
        super(SessionInfoWidget, self).__init__(parent=parent)

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        form_layout = QtWidgets.QFormLayout()
        form_layout.setFormAlignment(QtCore.Qt.AlignVCenter)
        main_layout.addLayout(form_layout)

        if configurations is not None:
            self._config_combo_box = QtWidgets.QComboBox()
            form_layout.addRow("Configuration", self._config_combo_box)

            for config in configurations:
                self._config_combo_box.addItem(config)

        self._subject_line_edit = QtWidgets.QLineEdit()
        form_layout.addRow("Subject", self._subject_line_edit)

        self._button = QtWidgets.QPushButton("Start")
        main_layout.addWidget(self._button)

        self._button.clicked.connect(self._on_button_click)

    def _on_button_click(self):
        info = {}

        subject = str(self._subject_line_edit.text())
        info['subject'] = subject

        if hasattr(self, '_config_combo_box'):
            config = str(self._config_combo_box.currentText())
            info['configuration'] = config

        if subject == '':
            QtWidgets.QMessageBox.warning(
                self,
                "Warning",
                "Subject ID must not be empty.",
                QtWidgets.QMessageBox.Ok)
            return

        self.finished.emit(info)
