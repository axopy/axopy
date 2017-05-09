import axopy.settings

backend = axopy.settings.messaging_backend


class emitter(object):
    def __init__(self, **data_format):
        self.data_format = data_format

    def __call__(self, function):
        cls = backend.emitter(*self.data_format.values())
        return cls(function, self.data_format)


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
        # I think connect and disconnect can be generic like this because
        # emitter is our emitter object, not necessarily a pyqtSignal, and we
        # know emitters have this interface
        emitter.connect(self)

    def disconnect(self, emitter):
        emitter.disconnect(self)
