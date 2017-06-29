import expyriment


class SessionManager(object):

    def __init__(self, tasks):
        self.tasks = tasks
        self.subject_id = None

    def run(self):
        for task in self.tasks:
            expyriment.control.initialize(task.experiment)
            task.design()

            expyriment.control.start(subject_id=self.subject_id)
            self.subject_id = task.experiment.subject
            task.run()

        expyriment.control.end(fast_quit=True)