class TrialManager(object):
    # abstract this so that future trial specificaions can respond to previous 
    # performance as in JND
    # should this inherit from iter or something? mainly it needs to define
    # a next / __next__ function

    def from_list_of_dicts(cls,list_of_dicts, randomize=True):
        # create a TrialManager from al ist of dicts
        # should this be a sub-class instead of a class method?

    def from_cycler(cls,cycler,randomize=True):
        # create a TrialManager using the  cycler package
        # should this be a sub-class instead of a class method?



class TaskBase(type):
    pass

class Task(object, metaclass=TaskBase):
    def __init__(self, trials=[], *args, **kwargs):
        self.trials = trials # TrialMangaer

    def do_task(self,):
        # this method gets called 
        self.prepare_task()
        for trial in self.trials:
            self.prepare_trial(trial)
            self.do_trial(trial) # ???
            self.cleanup_trial(trial)
        self.cleanup_task()

    def prepare_task(self,):
        for block in self.__class__.blocks:
            self.block.prepare_task()

    def prepare_trial(self,):
        for block in self.__class__.blocks:
            self.block.prepare_trial()

    def cleanup_trial(self,):

    def cleanup_task(self,):
