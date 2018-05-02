import numpy
import random


class Design(list):

    def add_block(self):
        b = Block(len(self))
        self.append(b)
        return b


class Block(list):

    def __init__(self, index, *args, **kwargs):
        super(Block, self).__init__(*args, **kwargs)
        self.index = index

    def add_trial(self, attrs=None):
        if attrs is None:
            attrs = {}

        attrs.update({'block': self.index, 'trial': len(self)})

        t = Trial(attrs=attrs)
        self.append(t)
        return t

    def shuffle(self):
        random.shuffle(self)


class Trial(object):

    def __init__(self, attrs):
        self.attrs = attrs
        self.arrays = {}

    def add_array(self, name, data=None, orientation='horizontal'):
        self.arrays[name] = Array(data=data, orientation=orientation)

    def __repr__(self):
        return str(self.attrs) + '\n' + str(self.arrays)


class Array(object):

    def __init__(self, data=None, orientation='horizontal'):
        self.orientation = orientation
        self.data = data

    def stack(self, data):
        if self.data is None:
            self.data = data
        else:
            if self.orientation == 'vertical':
                self.data = numpy.vstack([self.data, data])
            else:
                self.data = numpy.hstack([self.data, data])

    def clear(self):
        self.data = None
