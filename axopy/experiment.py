"""Experiment workflow and design."""

from axopy import util
from axopy.storage import Storage
from axopy.stream import InputStream
from axopy.messaging import Transmitter, TransmitterBase
from axopy.gui.main import _MainWindow, _SessionConfig
from axopy.gui.canvas import Canvas, Text


class Experiment(TransmitterBase):
    """Experiment workflow manager.

    Presents the researcher with a prompt for entering session details and then
    presents the appropriate tasks.

    Parameters
    ----------
    daq : object, optional
        A data acquisition device that follows the AxoPy DAQ protocol. See
        :mod:`axopy.stream`.
    data : str, optional
        Path to the data. The directory is created for you if it doesn't exist.
    subject : str, optional
        The subject ID to use. If not specified, a configuration screen is
        shown before running the tasks so you can enter it there. This is
        mostly for experiment writing (to avoid the extra configuration step).
    allow_overwrite : bool, optional
        If ``True``, overwrite protection in :class:`Storage` is disabled. This
        is mostly for experiment writing purposes.
    """

    key_pressed = Transmitter(str)

    def __init__(self, daq=None, data='data', subject=None,
                 allow_overwrite=False):
        super(Experiment, self).__init__()
        self.daq = daq
        self.input_stream = InputStream(daq)
        self.storage = Storage(data, allow_overwrite=allow_overwrite)

        self._receive_keys = False

        self.subject = subject

    def configure(self, **options):
        """Configure the experiment with custom options.

        This method allows you to specify a number of options that you want to
        configure with a graphical interface prior to running the tasks. Use
        keyword arguments to specify which options you want to configure. The
        options selected/specified in the graphical interface are then returned
        by this method so that you can alter setup before running the
        experiment.

        Each keyword argument should list the data type to configure, such as
        ``float``, ``str``, or ``int``. You can also provide a list or tuple of
        available choices for that option.

        You *do not* need to add an option for the subject name/ID -- that is
        added automatically if the subject ID was not specified when creating
        the experiment.
        """
        options['subject'] = str
        config = _SessionConfig(options).run()
        self.subject = config['subject']
        return config

    def run(self, *tasks):
        """Run the experimental tasks."""
        if self.subject is None:
            self.configure()

        # main screen
        self.screen = _MainWindow()
        self.screen.key_pressed.connect(self.key_press)

        # screen to show "Ready" between tasks
        self.confirm_screen = Canvas(draw_border=False)
        self.confirm_screen.add_item(Text("Ready"))

        self.storage.subject_id = self.subject
        self.tasks = tasks

        self.current_task = None
        self.task_iter = iter(self.tasks)
        self._task_finished()

        self.screen.run()

    @property
    def status(self):
        return "subject: {} | task: {}".format(
            self.subject, self.current_task.__class__.__name__)

    def _run_task(self):
        self._receive_keys = False

        # wait for task to finish
        self.current_task.finished.connect(self._task_finished)
        # forward key presses to the task
        self.key_pressed.connect(self.current_task.key_press)

        self.screen.set_status(self.status)

        # add a task view
        con = self.screen.new_container()

        self.current_task.prepare_graphics(con)
        self.current_task.prepare_input_stream(self.input_stream)
        self.current_task.prepare_storage(self.storage)
        self.current_task.run()

    def _task_finished(self):
        if self.current_task is not None:
            self.current_task.disconnect_all()
            self.current_task.finished.disconnect(self._task_finished)
            self.key_pressed.disconnect(self.current_task.key_press)

        try:
            self.current_task = next(self.task_iter)
        except StopIteration:
            self.screen.quit()

        self.screen.set_container(self.confirm_screen)
        self._receive_keys = True

    def key_press(self, key):
        if self._receive_keys:
            if key == util.key_escape:
                self.screen.quit()
            elif key == util.key_return:
                self._run_task()
        else:
            self.key_pressed.emit(key)
