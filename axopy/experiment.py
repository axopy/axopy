"""Experiment workflow and design."""

from axopy import util
from axopy.storage import Storage
from axopy.stream import InputStream
from axopy.messaging import transmitter
from axopy.gui.main import MainWindow, SessionInfo
from axopy.gui.canvas import Canvas


class Experiment(object):
    """Experiment workflow manager.

    Presents the researcher with a prompt for entering session details and then
    presents the appropriate tasks.

    Parameters
    ----------
    tasks : list or dict
        List of tasks in the experiment or a dictionary mapping experiment
        confgurations to task lists. The configurations are shown in a dropdown
        list so the researcher can select which configuration to use at
        run-time.
    device : object
        Any object that implements the device protocol.
    """

    status_format = "subject: {subject}, config: {configuration}"

    def __init__(self, tasks, device=None, data_root='data'):
        if isinstance(tasks, dict):
            configs = list(tasks)
        else:
            tasks = {'default': tasks}
            configs = ['default']
        self.tasks = tasks

        self.device = device
        self.input_stream = InputStream(device)

        self.storage = Storage(data_root)

        self.receive_keys = False

        # main screen
        self.screen = MainWindow()
        self.screen.key_pressed.connect(self.key_press)

        # screen to show "Ready" between tasks
        self.confirm_screen = Canvas(draw_border=False)
        self.confirm_screen.scene().addText("Ready")

        # initial screen to enter subject ID
        session_info_screen = SessionInfo(configs)
        session_info_screen.finished.connect(self._setup_session)
        self.screen.set_container(session_info_screen)

    @property
    def status(self):
        return self.status_format.format(**self.__dict__)

    def _setup_session(self, session):
        self.subject = session['subject']
        self.configuration = session['configuration']

        self.screen.set_status(self.status)

        self.storage.subject_id = self.subject

        self.current_task = None
        self.task_iter = iter(self.tasks[self.configuration])
        self.task_finished()

    def run(self):
        """Start the experiment."""
        self.screen.run()

    def run_task(self):
        self.receive_keys = False

        # wait for task to finish
        self.current_task.finished.connect(self.task_finished)
        # forward key presses to the task
        self.key_pressed.connect(self.current_task.key_press)

        # add a task view
        con = self.screen.new_container()

        self.current_task.prepare_view(con)
        self.current_task.prepare_input_stream(self.input_stream)
        self.current_task.prepare_storage(self.storage)
        self.current_task.run()

    def task_finished(self):
        if self.current_task is not None:
            self.current_task.finished.disconnect(self.task_finished)
            self.key_pressed.disconnect(self.current_task.key_press)

        try:
            self.current_task = next(self.task_iter)
        except StopIteration:
            self.screen.quit()

        self.screen.set_container(self.confirm_screen)
        self.receive_keys = True

    def key_press(self, key):
        if self.receive_keys:
            if key == util.key_escape:
                self.screen.quit()
            elif key == util.key_return:
                self.run_task()
        else:
            self.key_pressed(key)

    @transmitter(('key', str))
    def key_pressed(self, key):
        return key
