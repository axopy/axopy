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

.. code-block:: python

    class CustomTask(Task):

        def prepare_input_stream(self, input_stream):
            self.input_stream = input_stream
            self.input_stream.start()

        def run_trial(self, trial):
            self.input_stream.updated.connect(self.update)

        def update(self, data):
            # do something with the data from the input_stream here
