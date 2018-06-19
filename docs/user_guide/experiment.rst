.. _experiment:

================
Experiment Setup
================

.. currentmodule:: axopy.experiment

Before getting started writing experiments, it may be useful to see how AxoPy
is put together. The overall structure of an AxoPy application is handled by
the :class:`Experiment`. You can think of the experiment as a manager of
a number of tasks that, run in succession, form an actual experimental
protocol.

The :class:`Experiment` manages a PyQt5_ application and is responsible for
giving each task a graphical container within the Qt_ application, access to
hardware inputs, and data storage. The task implementation is responsible for
making use of these experiment-wide resources and then handing control back to
the experiment so it can run the next task. When you work on implementing an
experimental protocol, you'll spend most of your time implementing the task.
For now, though, we'll just talk about getting the :class:`Experiment` running
and some different ways it can be configured.

.. _Qt: https://www.qt.io/
.. _PyQt5: https://www.riverbankcomputing.com/software/pyqt/intro


Hello, Experiment
=================

Pretty much all AxoPy experiments have in common that they need to collect data
from a hardware input device and then produce feedback to the experiment
participant. For most of our examples, we'll make use of the built-in
:class:`~axopy.task.Oscilloscope` task and a built-in device, like the
:class:`~axopy.stream.NoiseGenerator`. In this example, we'll do just that: run
an experiment that consists of showing some random noise in an
oscilloscope-like signal viewer.

.. code-block:: python

    from axopy.experiment import Experiment
    from axopy.task import Oscilloscope
    from axopy.stream import NoiseGenerator

    exp = Experiment(daq=NoiseGenerator())
    exp.run(Oscilloscope())

In terms of lines of code, this is about the most straightforward experiment
you can write that actually does something. We create the :class:`Experiment`
object with a :class:`~axopy.stream.NoiseGenerator` as the input device, then
run the experiment with :class:`~axopy.task.Oscilloscope` as the sole task to
run.

When you run this code, you'll notice the first thing that happens is a dialog
window pops up prompting you to enter a subject ID. The :class:`Experiment`
needs a subject ID so that it can set up :ref:`data storage <storage>`. Once
the subject ID is entered and accepted, you'll see a screen that says "Ready".
This screen is shown in between all tasks in the experiment---hit the ``Enter``
or ``Return`` key to accept the prompt and start the task. You should then see
an oscilloscope widget displaying a randomly generated signal in real time. You
can press ``Enter`` again to finish the task (this is specific to
:class:`Oscilloscope` which is a "free-running" task). When the task finishes,
the :class:`Experiment` looks for the next task to run. Since there aren't any
more, the application exits.


Experiment Configuration
========================

It is very common in human-computer interface studies to need to do one or more
of the following:

- split subjects into groups
- re-test a subject on one or more follow-up sessions
- handle subjects of a specific class differently (e.g. mirror the screen
  contents for left-hand dominant subjects)

For these cases, :class:`Experiment` provides the option to run a configuration
step between creation of the experiment object and running the tasks. This
allows you to set options on your tasks before running them or even run an
entirely different list of tasks.

The :meth:`Experiment.configure()` method accepts as many configuration options
as you want. You specify each one by providing a keyword argument with the
option's type as the value.

For example, say we want to input the subject's age. We can do that with an
``int`` option called ``age``:

.. code-block:: python

    from axopy.experiment import Experiment

    exp = Experiment()
    config = exp.configure(age=int)

    print(config['age'])

If you run the code above, a dialog box will pop up just like it did for the
first example, but now a text box for the subject ID *and* the age is shown.
Note that you do not have to specify ``subject`` as an option---this is done
for you. :meth:`Experiment.configure()` returns a dictionary mapping the
option names to their values once the dialog is accepted. It's then up to you
to handle these options and modify how the experiment runs based on them.

Aside from primitive types like ``int``, ``str``, or ``float``, you can specify
a number of possible values for a configuration option, and these will be
available to select in a combo box (drop-down menu):

.. code-block:: python

    exp.configure(hand=('right', 'left'))


Tips for Experiment Writing
===========================

The :class:`Experiment` class accepts a couple other keyword arguments that can
be useful when debugging and/or developing an experiment application. You can
specify a ``subject`` argument so that the configuration dialog isn't shown
when the :class:`Experiment` is run:

.. code-block:: python

    from axopy.experiment import Experiment
    from axopy.task import Oscilloscope
    from axopy.stream import NoiseGenerator

    exp = Experiment(daq=NoiseGenerator(), subject='test')
    exp.run(Oscilloscope())

By default, if you run any tasks that write data to storage, AxoPy will
complain and exit if you attempt to overwrite any data that exists. This will
happen if you repeatedly run the :class:`Experiment` with the same subject ID,
so it can be useful (in conjunction with the ``subject`` keyword argument) to
set ``allow_overwrite=True`` as well, quelling the error regarding overwriting
data:

.. code-block:: python

    exp = Experiment(subject='test', allow_overwrite=True)
