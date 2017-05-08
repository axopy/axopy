import axopy.settings

backend = axopy.settings.messaging_backend
if backend == 'qt':
    from PyQt5.QtCore import pyqtSignal, QObject
    parent_class = QObject
else:
    parent_class = object


class emitter(object):
    def __init__(self, **data_format):
        self.data_format = data_format

    def __call__(self, function):
        class emitter_class(parent_class):
            if backend == 'qt':
                signal = pyqtSignal(*self.data_format.values())

            def __init__(self,function,data_format):
                super().__init__()
                self.data_format = data_format
                self.function = function

            def __get__(self, inst, cls):
                # perhaps this should be done somewhere else?
                self.inst = inst
                self.cls = cls
                return self

            def __call__(self,*args,**kwargs):
                result = self.function(self.inst,*args,**kwargs)
                self.signal.emit(result)
                return result

            def connect(self,receiver):
                if backend == 'qt':
                    self.signal.connect(receiver)

        return emitter_class(function, self.data_format)
        


class receiver(object):
    def __init__(self, function):
        self.function = function

    def __get__(self, inst, cls):
        # perhaps this should be done somewhere else?
        self.inst = inst
        self.cls = cls
        return self

    def __call__(self, *args, **kwargs):
        return self.function(self.inst,*args, **kwargs)

    def connect(self, emitter):
        if backend == 'qt':
            emitter.connect(self)




