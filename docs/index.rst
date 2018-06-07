=====
AxoPy
=====

AxoPy is a system for creating human-computer interface experiments involving
the use of electrophysiological signals, such as electromyography (EMG) or
electroencephalography (EEG). It is intended to provide an infrastructure for
rapidly developing simple experiments while allowing for more complex designs.


Features
--------

AxoPy aims to provide a framework for quickly and easily implementing ideas for
human-computer interface experiments. It covers the common facets of
human-computer interface experiments, including:

- data acquisition from one or more devices
- a graphical user interface for presenting visual feedback to subjects as well
  as controls for the experimenter
- simple built-in data visualization and recording
- data storage
- a processing pipeline infrastructure with some common processing
  implementations


Terminology
-----------

Some terminology is defined here to make the rest of the documentation clear.

- **Experiment**: The top-level implementation of all facets of an experiment
  you would run. This is a self-contained script or package (preferable),
  separate from AxoPy.
- **Session**: A single visit of a subject, encompassing all tasks performed.
  An experiment is essentially the implementation of the session(s) that all
  subjects will go through.
- **Task**: A distinct element in the experiment workflow. The interface for
  a task is implemented as a tab in the base UI.
- **Run**: A run through the entire implementation of a task, once.
- **Trial**: Runs typically involve repeated performance of individual trials,
  such as repeatedly moving a cursor to random target locations.


.. toctree::
   :maxdepth: 2

   installation
   user_guide
   tutorials
   api
   development
