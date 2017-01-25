from axopy.application import application, Task
from PyQt5 import QtWidgets


class CustomTask(Task):

    def setup_ui(self):
        return QtWidgets.QLabel("hey")


with application(None, None) as app:
    app.install_task(CustomTask())
