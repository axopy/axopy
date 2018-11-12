.. _task_recipes:

=================
Some Task Recipes
=================

The following are just some recipes for tasks or pieces of tasks that are
somewhat common.

The Basics
==========

Storing Data
------------

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
