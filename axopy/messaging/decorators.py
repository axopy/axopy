from axopy import settings


class emitter(object):
    def __init__(self, *data_format):
        self.data_format = data_format

    def __call__(self, function):
        return settings.messaging_backend(function, self.data_format)


class receiver(object):
    def __init__(self, function):
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
        return result

    def connect(self, emitter):
        emitter.connect(self)

    def disconnect(self, emitter):
        emitter.disconnect(self)
