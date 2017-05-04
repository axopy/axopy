"""Proof of concept for Qt-backed signal/slot messaging.

The base `Block` class shouldn't care about the fact that `pyqtSignal`s only
work with classes inheriting from `QObject`. Use a metaclass callable to hook
in and inject `QObject` as a base class. Note that a metaclass inheriting from
`type` and doing the same thing as `block_meta` in `__new__` doesn't seem to
work. It results in::

    TypeError: metaclass conflict: the metaclass of a derived class must be a
    (non-strict) subclass of the metaclasses of all its bases

I think it is because `QObject` doesn't derive from `type` but `sip.wrapper`,
but I don't fully understand the error nor SIP itself.
"""

from PyQt5.QtCore import pyqtSignal, QObject

# Just make an alias for Qt-backed signal/slot messaging for simplicity. In
# the real implementation, this would be change depending on backend and could
# have a different syntax for connecting things up.
signal = pyqtSignal
backend = 'qt'


def block_meta(name, bases, attrs):
    global backend
    if backend == 'qt':
        # swap out the base class (`object`) with `QObject`
        bases = (QObject,)
    return type(name, bases, attrs)


class Block(metaclass=block_meta):
    pass


# user code, implementing a custom block
class CustomBlock(Block):

    some_signal = signal(str)

    def trigger(self, data):
        print("emitting: {}".format(data))
        self.some_signal.emit(data)


# more user code, here using a function as a slot
def receiver(data):
    print("recieved: {}".format(data))


if __name__ == '__main__':
    block = CustomBlock()
    block.some_signal.connect(receiver)
    block.trigger('hey')
