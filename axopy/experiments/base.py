class ExperimentBase(type):
	def __new__(cls, name, bases, attrs):
        new_class = super(ModelBase, cls).__new__(cls, name, bases, {})

        for obj_name, obj in attrs.items():
            new_class.add_to_class(obj_name, obj)

    def add_to_class(cls, name, value):
        setattr(cls, name, value)

class Experiment(object, metaclass=ExperimentBase):
    def __init__(self, *args, **kwargs):
        for stream in self.__class__.streams:
            stream_val = kwargs.pop(stream)