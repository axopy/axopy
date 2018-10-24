.. _task:

==================
Implementing Tasks
==================

.. currentmodule:: axopy.task

In AxoPy, the individual components of an experiment are tasks. In essence,
a task does any or all of the following:

- Takes in data from previous tasks (read)
- Streams data from a data acquisition device (daq)
- Processes the streaming or task data (proc)
- Draws things to the screen (ui)
- Outputs data of its own (write)

One example of a task is :class:`Oscilloscope`. It is responsible for streaming
data from a data acquisition device (daq) and displaying it in a dynamic plot
(ui). The purpose of this task is usually just to allow the researcher to
visually verify the integrity of the data coming in from the device before
proceeding with the rest of the experiment.

Another example of a task is a cursor control task (subject produces input in
attempt to hit targets on the screen). This kind of task reads in and processes
data from an input device (daq), displays some information on screen to give
feedback to the subject (ui), and records some data for post-experiment analysis
(write). It may also require some calibration parameters from a previous task
(read).

There isn't really a strict definition of what a single task is or what it
should or shouldn't do, but it's a good idea to make tasks as simple as
possible -- any given task should do just a couple things and do them well.
This encourages modularity so you can re-use task implementations in different
experiments, etc.

In terms of the AxoPy API, a task looks like the following:

.. image:: images/task_diagram.png
   :align: center

In this part of the user guide, we'll go through how to make each of the four
connections in the diagram and refer to separate documents for the details of
working with those four components.


The Task Lifecycle
==================

Overview
--------

Tasks in an experiment all go through the same lifecycle. First, one or more
instances of a :class:`Task` are created (by you). Then, they are passed to the
:class:`Experiment <axopy.experiment.Experiment>`. This looks something like
the following:

.. code-block:: python

   exp = Experiment(...)
   exp.run(MyTask1(), MyTask2(param=3))

Once you call :meth:`Experiment.run <axopy.experiment.Experiment.run>`, the
Experiment collects the task objects passed in, prepares the shared resources
(data storage, data acquisition, graphical backend), then proceeds to prepare
and run each task in sequence.

Before running a task, the Experiment calls a set of ``prepare`` methods on the
task. This is the mechanism by which you optionally connect a given
:class:`Task` implementation to the shared resources. Say you're writing a task
that makes use of data storage only. A common example of this is processing
some data to make it available for other tasks later on in the experiment. To
interact with the :mod:`axopy.storage` functionality set up by the Experiment,
your class implementation should override the :meth:`Task.prepare_storage`
method. If you click on the link to the API documentation for that method,
you'll see that a :class:`axopy.storage.Storage` object is passed into this
method, which is provided by the Experiment. We'll see later on more details
about setting up storage specifically, but for the sake of the example, it's
sufficient to point out that the storage object lets you create reader and/or
writer objects that you can save for use later on in your task:

.. code-block:: python

   from axopy.task import Task

   class MyTask1(Task):

      def prepare_storage(self, storage):
         self.reader = storage.require_task('other_task')

There is one additional method, :meth:`Task.prepare_design`, which is a bit
special in that it isn't a shared resource provided by the experiment.
Implementing the :meth:`Task.prepare_design` method for the progression of each task and is not a shared
resource between tasks. Building a :class:`Design <axopy.design.Design>` for
a task is useful in situations where it makes sense to break a task down into
repeated parts. These are referred to as trials and blocks (of trials).

After the rest of the ``prepare`` methods are called, the :meth:`Task.run`
method is called. This is a point of divergence for different kinds of tasks.
In "experiment tasks" with trials, blocks of trials, etc. the flow of the task
proceeds through it's :class:`Design` by calling :class:`Task.next_trial``.

The Prepare Methods
-------------------



Recipes
=======

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
