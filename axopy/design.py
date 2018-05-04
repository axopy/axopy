"""Task design containers."""
import numpy
import random
import pprint

__all__ = ['Design', 'Block', 'Trial', 'Array']


class Design(list):
    """Top-level task design container.

    The :class:`Design` is a list of :class:`Block` objects, which themselves
    are lists of :class:`Trial` objects.
    """

    def add_block(self):
        """Add a block to the design.

        Returns
        -------
        block : design.Block
            The created block.
        """
        block = Block(len(self))
        self.append(block)
        return block


class Block(list):
    """List of trials.

    Experiments often consist of a set of blocks, each containing the same set
    of trials in randomized order. You usually shouldn't need to create a block
    directly -- use :meth:`Design.add_block` instead.

    Parameters
    ----------
    index : int
        Index of the block in the design. This is required to pass along to
        each trial in the block, so that the trial knows which block it belongs
        to.
    """

    def __init__(self, index, *args, **kwargs):
        super(Block, self).__init__(*args, **kwargs)
        self.index = index

    def add_trial(self, attrs=None):
        """Add a trial to the block.

        A :class:`Trial` object is created and added to the block. You can
        optionally provide a dictionary of attribute name/value pairs to
        initialize the trial.

        Parameters
        ----------
        attrs : dict, optional
            Dictionary of attribute name/value pairs.

        Returns
        -------
        trial : Trial
            The trial object created. This can be used to add new attributes or
            arrays. See :class:`Trial`.
        """
        if attrs is None:
            attrs = {}

        attrs.update({'block': self.index, 'trial': len(self)})

        trial = Trial(attrs=attrs)
        self.append(trial)
        return trial

    def shuffle(self, reset_index=True):
        """Shuffle the block's trials in random order.

        Parameters
        ----------
        reset_index : bool, optional
            Whether or not to set the ``trial`` attribute of each trial such
            that they remain in sequential order after shuffling. This is the
            default.
        """
        random.shuffle(self)
        if reset_index:
            for i, trial in enumerate(self):
                trial.attrs['trial'] = i


class Trial(object):
    """Container of trial data.

    There are two kinds of data typically needed during a trial: attributes and
    arrays. Attributes are scalar quantities or primitives like integers,
    floating point numbers, booleans, strings, etc. Arrays are NumPy arrays,
    useful for holding things like cursor trajectories.

    There are two primary purposes for each of these two kinds of data. First,
    it's useful to design a task with pre-determined values, such as the target
    location or the cursor trajectory to follow. The other purpose is to
    temporarily hold runtime data using the same interface, such as the final
    cursor position or the time-to-target.

    You shouldn't normally need to create a trial directly -- instead, use
    :meth:`Block.add_trial`.

    Attributes
    ----------
    attrs : dict
        Dictionary mapping attribute names to their values.
    arrays : dict
        Dictionary mapping array names to :class:`Array` objects, which contain
        the array data.
    """

    def __init__(self, attrs):
        self.attrs = attrs
        self.arrays = {}

    def add_array(self, name, **kwargs):
        """Add an array to the trial.

        Parameters
        ----------
        name : str
            Name of the array.
        kwargs : dict
            Keyword arguments passed along to :class:`Array`.
        """
        self.arrays[name] = Array(**kwargs)

    def __str__(self):
        return pprint.pformat(self.attrs)


class Array(object):
    """Trial array.

    The array is not much more than a NumPy array with a :meth:`stack` method
    for conveniently adding new data to the array. This is useful in cases
    where you iteratively collect new segments of data and want to concatenate
    them. For example, you could use an :class:`Array` to collect the samples
    from a data acquisition device as they come in.

    You usually don't need to create an array manually -- instead, use
    :meth:`Trial.add_array`.

    Parameters
    ----------
    data : ndarray, optional
        Data to initialize the array with. If ``None``, the first array passed
        to :meth:`stack` is used for initialization.
    stack_axis : int, optional
        Axis to stack the data along.

    Attributes
    ----------
    data : ndarray, optional
        The NumPy array holding the data.
    """

    _stack_funcs = {0: numpy.vstack, 1: numpy.hstack, 2: numpy.dstack}

    def __init__(self, data=None, stack_axis=1):
        self.data = data
        self.stack_axis = stack_axis

    def stack(self, data):
        """Stack new data onto the array.

        Parameters
        ----------
        data : ndarray
            New data to add. The direction to stack along is specified in the
            array's constructor (stack_axis).
        """
        if self.data is None:
            self.data = data
        else:
            self.data = self._stack_funcs[self.stack_axis]([self.data, data])

    def clear(self):
        """Clears the buffer.

        Anything that was in the buffer is not retrievable.
        """
        self.data = None
