from axopy.messaging import transmitter


class TaskIter(object):
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
            design = [[]]

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
    """

    def __init__(self, design=None):
        self.iter = TaskIter(design)

    def prepare(self):
        """Initialize graphical elements and messaging connections.

        This method should be overridden if the task uses any graphics (which
        most do). It is important to defer initializing any graphical elements
        until this method is called so that the graphical backend has a chance
        to start. This method is called automatically if the task is added to
        a :class:`TaskManager`.
        """
        pass

    def run(self):
        """Starts running the task.

        Simply calls `next_block` to start running trials in the first block.
        This method is called automatically if the task is added to a
        :class:`TaskManager`. You shouldn't normally need to override this
        method.
        """
        self.next_block()

    def next_block(self):
        """Gets the next block of trials and starts running them.

        Before starting the block, a prompt is shown to verify that the user is
        ready to proceed. If there are no more blocks to run, the `finish`
        method is called. You usually do not need to override this method.
        """
        # wait for confirmation between blocks
        block = self.iter.next_block()
        if block is None:
            self.finish()
            return

        # TODO: (optionally) wait for confirmation to start

        self.block = block
        self.next_trial()

    def next_trial(self):
        """Gets the next trial in the block and starts running it.

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
        """Initiates a trial.

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
        self.next_block()

    @transmitter()
    def finish(self):
        """Called after the last trial of the last block has run.

        This method simply transmits an event. Override to do cleanup if
        needed, but make sure to keep it as a transmitter.
        """
        return


class CustomTask(Task):

    def __init__(self, design):
        super().__init__(design)

    def run_trial(self, trial):
        print('running trial with data {}'.format(trial))
        import time
        time.sleep(1)
        self.finish_trial()

    def finish_trial(self):
        print('finishing trial')
        self.next_trial()


if __name__ == '__main__':
    design = [
        [{'attr': 32}, {'attr': 24}],
        [{'attr': 20}, {'attr': 21}],
        [{'attr': 10}, {'attr': 88}]
    ]

    task = CustomTask(design)
    task.run()
