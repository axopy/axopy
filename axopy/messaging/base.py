class BaseEmitter(object):

    def __init__(self, function, data_format):
        super(BaseEmitter, self).__init__()
        self.data_format = data_format
        self.function = function

    def __get__(self, inst, cls):
        self.inst = inst
        self.cls = cls
        return self

    def __call__(self, *args, **kwargs):
        if hasattr(self, 'inst'):
            result = self.function(self.inst, *args, **kwargs)
        else:
            result = self.function(*args, **kwargs)
        self.emit(result)
        return result
