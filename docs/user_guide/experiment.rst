.. _experiment:

================
Experiment Setup
================

.. currentmodule:: axopy.experiment

The overall structure of an AxoPy application is handled by the
:class:`Experiment`. You can think of the :class:`Experiment` as a manager of
a number of tasks that, when run in succession, form an actual experimental
protocol. Let's get started with AxoPy by immediately writing a bit of code to
produce a running experiment. We can then re-run the application after making
a number of changes to get a feel for how to set up an :class:`Experiment`.


Hello, Experiment
=================

AxoPy is written for experiments that involve collecting data from a hardware
input device and producing visual [#f1]_ feedback to the subject. For most of
our examples, we'll make use of the built-in :class:`~axopy.task.Oscilloscope`
task and a built-in device that works without requiring special hardware, like
the :class:`~axopy.daq.NoiseGenerator`. So here's how we use those two items
to put together a simple but functioning experiment:

.. code-block:: python

    import axopy

    daq = axopy.daq.NoiseGenerator()
    exp = axopy.experiment.Experiment(daq=daq)
    exp.run(axopy.task.Oscilloscope())

We create the :class:`Experiment` object with
a :class:`~axopy.daq.NoiseGenerator` as the input device (or DAQ, short for
data acquisition), then run the experiment with
:class:`~axopy.task.Oscilloscope` as the sole task to run.

It's worth noting here that AxoPy's submodules (e.g. experiment, daq, etc.) are
useful for organizing the package into logical parts, but it can be annoying to
type the module names repeatedly. You can write the above example with more
verbose imports like the following so the code itself is a little more
succinct:

.. code-block:: python

   from axopy.daq import NoiseGenerator
   from axopy.experiment import Experiment
   from axopy.task import Oscilloscope

   daq = NoiseGenerator()
   exp = Experiment(daq=daq)
   exp.run(Oscilloscope())

When you run this example, you'll notice the first thing that happens is
a dialog window pops up prompting you to enter a subject ID. The
:class:`Experiment` needs a subject ID so that it can set up :ref:`data storage
<storage>`. Once the subject ID is entered and accepted, you'll see a screen
that says "Ready". This screen is shown in between all tasks in the
experiment---hit the ``Enter`` or ``Return`` key to accept the prompt and start
the task. You should then see an oscilloscope widget displaying a randomly
generated signal in real time. You can press ``Enter`` again to finish the task
(this is specific to :class:`Oscilloscope` which is a "free-running" task).
When the task finishes, the :class:`Experiment` looks for the next task to run.
Since there aren't any more, the application exits.

.. [#f1] At least visual. For now, AxoPy doesn't have a standardized way to
   talk to other kinds of feedback-producing devices (an audio output module
   would be cool, PRs welcome). That said, AxoPy doesn't do anything to
   *prevent* you from working with them either.


Experiment Configuration
========================

Human-computer interface study designs often include one or more of the
following complications:

- subjects are split into groups
- subjects are tested over multiple sessions
- subjects fall into categories that require different configuration (e.g.
  mirror the screen contents for left-hand dominant subjects)

For these cases, :class:`Experiment` provides the option to run a configuration
step between creation of the experiment object and running the tasks. The
options are entered in the same dialog window where you entered the subject ID
in the example above. This allows you to set options on your tasks before
running them or even run an entirely different list of tasks. It also means the
person running an experiment (which isn't necessarily the person who wrote the
experiment code) doesn't need to know how to write some configuration file or
anything --- they just run the experiment application and can enter the details
in a graphical widget.

The :meth:`Experiment.configure()` method accepts as many configuration options
as you want. You specify each one by providing a keyword argument with the
option's type (e.g. ``str``, ``int``, ``float``) as the value, and it returns
a dictionary with the values entered.

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
for you. It's up to you to handle the configuration options and modify how the
experiment runs based on them.

Aside from primitive types like ``int``, ``str``, or ``float``, you can
enumerate all possible values for a configuration option, and these will be
available to select in a combo box (drop-down menu). This way, the researcher
running the experiment can't enter an invalid value:

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
    from axopy.daq import NoiseGenerator

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

This setup is pretty handy when developing an experiment, just remember to
switch it off! One way to make this a little more robust is to add a flag to
your application so you have to explicitly enable this "debugging mode".


How It Works
============

*Skippable unless you want to dig into working on AxoPy itself*

The :class:`Experiment` manages a PyQt5_ application and is responsible for
giving each task a graphical container within the Qt_ application, access to
hardware inputs, and data storage. The task implementation is responsible for
making use of these experiment-wide resources and then handing control back to
the experiment so it can run the next task.

.. _Qt: https://www.qt.io/
.. _PyQt5: https://www.riverbankcomputing.com/software/pyqt/intro


Next Up
=======

Now that we have an experiment running and the ability to set up some
configuration options if needed, let's look at :ref:`how to write tasks
<task>`.
