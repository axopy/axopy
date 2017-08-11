import numpy
from axopy import util
from axopy.messaging import transmitter
from axopy.task.base import Task
from axopy.gui.main import MainWindow
from axopy.gui.canvas import Canvas, Circle
from axopy.gui.signals import Oscilloscope


class CanvasTask(Task):

    step = 1

    def __init__(self, text):
        super().__init__()
        self.text = text
        self.key_map = {
            util.key_w: (0, -self.step),
            util.key_a: (-self.step, 0),
            util.key_s: (0, self.step),
            util.key_d: (self.step, 0)
        }

    def prepare(self):
        self.ui = Canvas()
        self.cursor = Circle(10)
        self.ui.add_item(self.cursor)

    def run(self):
        pass

    def key_press(self, key):
        if key == util.key_space:
            self.finish()

        try:
            move = self.key_map[key]
        except KeyError:
            return

        self.cursor.moveBy(*move)


class OscilloscopeTask(Task):

    def prepare(self):
        self.ui = Oscilloscope()

    def run(self):
        self.plot()

    def plot(self):
        self.ui.plot(numpy.random.randn(4, 1000))

    def key_press(self, key):
        if key == util.key_space:
            self.finish()
        elif key == util.key_d:
            self.plot()


class TaskManager(object):

    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks
        self.task_iter = iter(tasks)

        self.receive_keys = False

        self.screen = MainWindow()
        self.screen.key_pressed.connect(self.key_press)

        self.confirm_task = Canvas(draw_border=False)
        self.confirm_task.scene().addText("Ready")

        self.task_finished()

    def run(self):
        self.screen.run()

    def next_task(self):
        self.receive_keys = False

        try:
            self.current_task = next(self.task_iter)
        except StopIteration:
            self.screen.quit()

        self.run_task()

    def run_task(self):
        self.current_task.finish.connect(self.task_finished)
        self.key_pressed.connect(self.current_task.key_press)
        self.current_task.prepare()
        self.screen.set_view(self.current_task.ui)
        self.current_task.run()

    def task_finished(self):
        try:
            self.current_task.finish.disconnect(self.task_finished)
            self.key_pressed.disconnect(self.current_task.key_press)
        except:
            pass
        self.screen.set_view(self.confirm_task)
        self.receive_keys = True

    def key_press(self, key):
        if self.receive_keys:
            if key == util.key_escape:
                self.screen.quit()
            elif key == util.key_return:
                self.next_task()
        else:
            self.key_pressed(key)

    @transmitter(('key', str))
    def key_pressed(self, key):
        return key


if __name__ == '__main__':
    tm = TaskManager([CanvasTask('hey'),
                      CanvasTask('there'),
                      OscilloscopeTask()])
    tm.run()
