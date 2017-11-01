.. _user_interface:

==============
User Interface
==============

.. currentmodule:: axopy.application

This is currently a sort of design document describing some musings on the
design of the "application" portion of AxoPy.


Overview
--------

The user interface is based on Qt_, implemented with PyQt5_. A base user
interface is provided, which is really just a QMainWindow_ with some default
functionality and a simple API added for easily building up a full experiment
workflow. Implementing an experiment involves instantiating this base UI,
adding tasks to it (which are represented as tabs in the UI), and running it.
A task is just a `QWidget`_, again with a small API on top to standardize how
the base UI interacts with it. Some common tasks are built into the library,
but a full experiment implementation will most likely involve one or more
custom task UI classes.


Task Lifecycle
--------------

All tasks should deal with the following events:

- instantiated (by the user)
- installed in base UI (by the user)
- made visible
- started
- paused
- complete

AxoPy should handle much of the lifecycle based on a user-designed task
inheriting from one of a few task base classes. The behavior can of course be
overridden.


Task Properties
---------------

These are some of the properties that define how the base UI should handle
switching to and away from a task.

- **locking**: tasks that can't be navigated away from once started. Examples
  include basically all tasks that collect data. Base UI should disable the tab
  bar until the task is paused or completed.
- **requires participant**: tasks that aren't useful without having
  a participant selected. Examples include experiment tasks, experiment data
  visualization tasks, data processing tasks. You can activate the task's tab,
  but the tab is disabled with a message saying it requires a participant to be
  selected.
- **requires data read access**: tasks that require a participant *and* data
  from a specific task for that participant. Examples include an experiment
  task that relies on data generated from another experiment task and/or
  processed data from another experiment task. You can activate this task's
  tab, but the tab should be disabled with a message saying that it requires
  data.
- **requires data write access**: tasks that require the ability to write to
  data storage. Examples include experiment tasks, processing tasks. Data
  writing tasks are (I think) always going to also be locking, require
  a participant. Most will also require data read access.
- **requires DAQ**: tasks that need to access data from a data acquisition
  device. Examples include oscilloscope-type tasks and experiment tasks. Not
  necessarily locking.


Task Types
----------

With the above properties taken into consideration, all tasks will fall into
one of the following categories:

`RealtimeVisualizationTask`
  Reads data from a data acquisition device and displays it. May perform some
  computation on the data but cannot write the processed data. Requires DAQ.
`DataVisualizationTask`
  Reads data from storage and displays it. May perform computation on the data
  but cannot write it to storage. Use a `ProcessorTask` for that. Requires
  participant, read access to storage.
`ProcessingTask`
  Similar to a `DataVisualizerTask`, but can write processed data. This means
  the task locks while processing and writing. Requires participant, read
  access to data storage, write access to data storage, locking.
`ExperimentTask`
  The most complex type of task, requiring implementation of all task
  properties. These are tasks that might include training on data from other
  tasks, reading data from a data acquisition device, and writing data to
  storage. Requires participant, DAQ, read access to data storage write access
  to data storage, locking.

Interface idea: these base task classes have class attributes corresponding to
the properties listed above, the base UI looks at these attributes to decide
what methods to call on them, what to show if a requirement isn't met, etc.


Task Creation Functions
-----------------------

Some experiments are probably simple enough that fully customized tasks aren't
really necessary, but built-in tasks won't cut it either. For these cases,
there should be some functions like ``create_processing_task`` that look
something like:

.. code:: python

   def create_processing_task(name, input_task, pipeline, widget):
       """Generates a ProcessingTask.

       Parameters
       ----------
       name : str
           Name of the task. Used as the location in storage for the output.
       input_task : str
           Name of the task for retrieving input data.
       pipeline : Pipeline
           Processing pipeline which accepts a trial of data from the
           `input_task` and outputs the processed trial data.
       widget : QWidget
           A widget for displaying the data from each output trial.
       """

This specific example probably needs some more thought, such as handling which
sessions/trials to process and what to display to the operator.


.. _Qt: https://www.qt.io/
.. _PyQt5: https://www.riverbankcomputing.com/software/pyqt/intro
.. _QMainWindow: https://doc.qt.io/qt-5/qmainwindow.html
.. _QWidget: https://doc.qt.io/qt-5/qwidget.html
