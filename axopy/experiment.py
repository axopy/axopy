"""Experiment workflow and design."""

from axopy import util
from axopy.messaging import transmitter
from axopy.gui.main import MainWindow
from axopy.gui.canvas import Canvas


class Experiment(object):
    """Experiment workflow manager.

    Presents the researcher with a prompt for entering session details and then
    presents the appropriate tasks.
    """

    def __init__(self, tasks, device=None):
        self.tasks = tasks
        self.device = device

        self.task_iter = iter(tasks)

        self.receive_keys = False

        self.screen = MainWindow()
        self.screen.key_pressed.connect(self.key_press)

        self.confirm_screen = Canvas(draw_border=False)
        self.confirm_screen.scene().addText("Ready")

        self.task_finished()

    def run(self):
        """Start the experiment."""
        self.screen.run()

    def run_task(self):
        self.receive_keys = False

        # wait for task to finish
        self.current_task.finish.connect(self.task_finished)
        # forward key presses to the task
        self.key_pressed.connect(self.current_task.key_press)

        # add a task view
        con = self.screen.new_container()

        self.current_task.prepare_view(con)
        self.current_task.prepare_input_stream(self.device)
        self.current_task.run()

    def set_subject(self, subject):
        print(subject)

    def task_finished(self):
        try:
            self.current_task.finish.disconnect(self.task_finished)
            self.key_pressed.disconnect(self.current_task.key_press)
        except:
            # either there is no current task or it wasn't connected
            pass

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


class ExperimentDesign(object):

    def __init__(self):
        self.design_dict = {}

    def add_condition(self, condition):
        self.design_dict[condition.name] = condition

    def to_json(self):
        pass

    @classmethod
    def from_dict(self, d):
        pass

    @classmethod
    def from_json(self, s):
        pass


class Condition(object):

    def __init__(self):
        self.tasks = []

    @classmethod
    def from_list(self, l):
        pass

    def add_task(self, name, cls, params):
        self.tasks.append((name, cls, params))
