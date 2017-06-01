class BaseTaskMeta(type):
    def __new__(cls, name, bases, attrs):
        return super.__new__(cls,name,bases,attrs)

class BaseTask(object, metaclass=BaseTaskMeta):
    connections = ()
    trial_iter = None

    # potentially thse are all class methods?
    def make_conections(self):
        pass 

    def prepare_task(self):
        pass

    def prepare_trial(self):
        # possibly make and break connections per trial
        pass

    def do_trial(self):
        pass

    def cleanup_trial(self):
        # save trial-level (summary) data
        pass

    def cleanup_task(cls):
        # save task-level data? 
        
        pass

    def run(cls):
        prepare_task()
        for trial in trial_iter:
            prepare_trial(trial)
            do_trial()
            cleanup_trial()
        cleanup_task()


