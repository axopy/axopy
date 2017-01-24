class MessangerHandler(object):
    # not sure if this i needed
    pass


class BlockBase(type):
    def __new__(cls, name, bases, attrs):
        new_class = super(ModelBase, cls).__new__(cls, name, bases, {})

        for obj_name, obj in attrs.items():
            new_class.add_to_class(obj_name, obj)

    def add_to_class(cls, name, value):
        setattr(cls, name, value)

class Block(object, metaclass=BlockBase):
    """
    How to have the  
    """
    def __int__(self,*args, **kwargs):
        pass

    def prepare_task(self,):
        # connect signals, slots? or is that just in __init__?
        pass

    def prepare_trial(self,*args,**kwargs):
        for attr in self.__class__.attrs:

    def cleanup_trial(self,):

