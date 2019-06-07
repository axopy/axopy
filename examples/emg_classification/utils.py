from threading import Thread, Event


class StoppableThread(Thread):
    """
    A Thread implementation with a stopping functionality.

    This special Thread class implements a stop() method. The thread itself
    has to check regularly for the stopped() condition.
    """

    def __init__(self, **kwargs):
        super(StoppableThread, self).__init__(**kwargs)
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
