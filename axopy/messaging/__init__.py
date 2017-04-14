

class emitter(object):
    def __init__(self, **data_format):
        self.data_format = data_format

    def __call__(self, function):
        self.function = function

        if backend == 'qt':
            # does emitter need to change inheritance based on backend?
            # or do we need to contribute the signal object to the class  
            # that has the emitter??
            self.signal = (**self.data_format)
            def qt_function(*args, **kwargs):
                self.signal.emit(self.function(*args,**kwargs))

            return qt_function
        else:
            raise ValueError("Current backend not supported")

    def connect(self,receiver):
        if backend == 'qt':
            self.signal.connect(receiver)


class receiver(object):
    def __init__(self, function):
        print("init reciever")
        print(function.__dir__())
        print(function.__module__,function.__qualname__)
        self.function = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def connect(self, emitter):
        if backend == 'qt':
            emitter.connect(self)




