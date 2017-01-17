class TaskBase(type):
    pass

class Task(object, metaclass=TaskBase)