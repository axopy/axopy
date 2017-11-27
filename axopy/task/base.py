"""Base task implementation."""

from axopy import util
from axopy.messaging import transmitter, receiver


class _TaskIter(object):
    """Cleanly retrieves blocks of a task design and the trials within them.

    A task design is a sequence of sequences: a sequence of blocks which are
    themselves sequences of trials. The `TaskIter` iterates over blocks,
    returning the block data when a new block is available. Nested in the
    blocks are trials, which the `TaskIter` further iterates over, returning
    them when available.

    Here is more graphical depiction of the flow through a design::

        design: [
            next_block -> block: [
                next_trial -> trial,
                next_trial -> trial,
                ...
                next_trial -> None
            ],
            next_block -> block: [
                next_trial -> trial,
                next_trial -> trial,
                ...
                next_trial -> None
            ],
            ...
            next_block -> None
        ]

    Parameters
    ----------
    design : list
        The task `design` must be an iterable of iterables, such as a list of
        lists. The elements of the outer iterable are termed "blocks" and the
        elements of the inner iterable are termed "trials." The trials have any
        structure you want, but a typical choice would be a dictionary with
        attributes that specify all parameters of the trial.
    """

    def __init__(self, design=None):
        if design is None:
            design = [[{}]]

        self.design = design
        self.block_iter = iter(design)

    def next_block(self):
        """Get the next block in the task if available.

        If no more blocks are available, `None` is returned. Once this occurs,
        the task is complete and should be finished.
        """
        try:
            block = next(self.block_iter)
        except StopIteration:
            return None

        self.trial_iter = iter(block)
        return block

    def next_trial(self):
        """Get the next trial in the current block, if available.

        If there are no more trials in the block, `None` is returned. Once
        this occurs, you should call `next_block` to get the next block of
        trials.
        """
        try:
            trial = next(self.trial_iter)
        except StopIteration:
            return None

        return trial


class Task(object):
    """Base class for tasks.

    This base class handles iteration through the trials of the task in blocks.

    Most task implementations will want to override the `prepare` and
    `run_trial` methods, while the rest can be left to default behavior.

    Attributes
    ----------
    advance_block_key : str
        Key for the user to press in order to advance to the next block. Can
        set to ``None`` to disable the feature (next block starts immediately
        after one finishes).
    """

    advance_block_key = util.key_return

    def design(self, trials):
        self.iter = _TaskIter(trials)

    def prepare_view(self, view):
        """Initialize graphical elements and messaging connections.

        This method should be overridden if the task uses any graphics (which
        most do). It is important to defer initializing any graphical elements
        until this method is called so that the graphical backend has a chance
        to start. This method is called automatically if the task is added to
        a :class:`TaskManager`.

        Parameters
        ----------
        view : Container
            The graphical container you can add objects to.
        """
        pass

    def prepare_input_stream(self, input_stream):
        pass

    def prepare_storage(self, storage):
        """Initialize data storage.

        Override to read or write task data. A :class:`axopy.storage.Storage`
        object is given, which can be used to create a new
        :class:`axopy.storage.TaskWriter` for storing new data or
        a :class:`axopy.storage.TaskReader` for reading in existing data. Note
        that the subject ID has already been set.

        Parameters
        ----------
        storage : axopy.storage.Storage
            The top-level storage object with which new storage can be
            allocated and existing data can be read.
        """
        pass

    def run(self):
        """Start running the task.

        Simply calls `next_block` to start running trials in the first block.
        This method is called automatically if the task is added to a
        :class:`TaskManager`. Tasks that have a block design shouldn't normally
        need to override this method. Tasks that are "free-running" for
        experimenter interaction (e.g. a plot visualization task that the
        experimenter controls) should override and do nothing.
        """
        self.next_block()

    def next_block(self):
        """Get the next block of trials and starts running them.

        Before starting the block, a prompt is shown to verify that the user is
        ready to proceed. If there are no more blocks to run, the `finish`
        method is called. You usually do not need to override this method.
        """
        block = self.iter.next_block()
        if block is None:
            self.finish()
            return

        self.block = block

        # wait for confirmation between blocks
        if self.advance_block_key is None:
            self.next_trial()
        else:
            self._awaiting_key = True

    def next_trial(self):
        """Get the next trial in the block and starts running it.

        If there are no more trials in the block, the `finish_block` method is
        called.
        """
        trial = self.iter.next_trial()
        if trial is None:
            self.finish_block()
            return

        self.trial = trial
        self.run_trial(trial)

    def run_trial(self, trial):
        """Initiate a trial.

        By default, this method does nothing. Override to implement what
        happens in a trial. When a trial is complete, use `next_trial` to
        start the next.

        Parameters
        ----------
        trial : object
            Trial data. This is whatever data is put into the `design` passed
            in.
        """
        pass

    def finish_block(self):
        """Finishes the block and starts the next one.

        Override if you need to do some cleanup between blocks.
        """
        pass

    @transmitter()
    def finish(self):
        """Signal that the last trial of the last block has run.

        This method simply transmits an event. Override to do cleanup if
        needed, but make sure to keep it as a transmitter.
        """
        return

    @receiver
    def key_press(self, key):
        """Handle key press events.

        Override this method to receive key press events. Available keys can be
        found in :mod:`axopy.util` (named `key_<keyname>`, e.g. `key_k`).

        Important note: if relying on the ``advance_block_key`` to advance the
        task, make sure to call this super implementaiton.
        """
        if getattr(self, '_awaiting_key', False) and \
                key == self.advance_block_key:
            self._awaiting_key = False
            self.next_trial()
