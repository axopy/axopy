.. _task_recipes:

=================
Some Task Recipes
=================

The following are just some recipes for tasks or pieces of tasks that are
somewhat common. Note that these are for illustration purposes and won't always
run as-is.

The Basics
==========

.. _recipe_storage_basic:

Storing Data
------------

Storing data within a task is typically a two-step process. First, you
implement :meth:`~axopy.task.Task.prepare_design` to set up the attributes and
arrays (with initial values) for each trial and the trial/block structure. Then
you implement :meth:`~axopy.task.Task.prepare_storage` to get access to a new
:class:`~axopy.storage.TaskWriter`. When your trial is finished, you can use
the task's ``trial`` attribute to write the trial data to disk using the task
writer.

.. code-block:: python

    class CustomTask(Task):

        def prepare_design(self, design):
            block = design.add_block()
            for pos in [0, 0.2, 0.4]:
                block.add_trial(attrs={'pos': pos})
            block.shuffle()

        def prepare_storage(self, storage):
            self.writer = storage.create_task('custom_task')

        # ... task implementation here

        def finish_trial(self):
            self.writer.write(self.trial)

            # call next_trial() to start the next trial
            # could instead start a timer if you want a timeout between trials
            self.next_trial()

.. _recipe_daq_basic:

Using Input Hardware
--------------------

To make use of an input device (DAQ), implement :meth:`~axopy.task.prepare_daq`
to gain access to the stream interface, get it running, then connect its
updated transmitter to a callback that you define.

.. code-block:: python

    class CustomTask(Task):

        def prepare_daq(self, daqstream):
            self.daqstream = daqstream
            self.daqstream.start()

        def run_trial(self, trial):
            self.daqstream.updated.connect(self.update)

        def update(self, data):
            # do something with the data from the daqstream here

You may instead want to connect the stream in ``prepare_daq`` and start and
stop the stream (as opposed to letting it run and making/breaking the
connection to your update callback). The main disadvantage to this approach is
some devices may take a couple seconds to start. The downside of the other
approach though is the time from making the connection to the first call of the
``update`` callback is variable depending on when exactly the connection is
made with respect to the most recent update from the hardware.

.. code-block:: python

    class CustomTask(Task):

        def prepare_daq(self, daqstream):
            self.daqstream = daqstream
            self.daqstream.updated.connect(self.update)

        def run_trial(self, trial):
            self.daqstream.start()

        def update(self, data):
            # do something with the data from the daqstream here

