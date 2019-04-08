---
title: 'AxoPy: A Python Library for Implementing Human-Computer Interface Experiments'
tags:
  - Python
  - electrophysiology
  - electromyography
  - human-computer interface
  - prosthetics
authors:
  - name: Kenneth R. Lyons
    orcid: 0000-0002-9143-8459
    affiliation: 1
  - name: Benjamin W. L. Margolis
    orcid: 0000-0001-5602-1888
    affiliation: 1
affiliations:
 - name: University of California, Davis
   index: 1
date: 11 January 2019
bibliography: references.bib
---

# Summary

AxoPy is a system for creating human-computer interface experiments involving
the use of electrophysiological signals, such as electromyography (EMG) or
electroencephalography (EEG). It is intended to provide an infrastructure for
rapidly developing common kinds of experiments while allowing for more complex,
customized designs.

In human-computer interface studies, experiment designs can often be organized
as a series of tasks. Each task in the experiment may need to record data from
a data acquisition system, log data, read data from previous tasks, and provide
a graphical user interface. AxoPy offers a framework for implementing these
tasks and their various input/output operations. While AxoPy doesn't include as
much built-in functionality as alternatives such as PsychoPy [@psychopy] or
Expyriment [@expyriment], the task-based design is convenient for implementing
complex experiment designs that require many inter-dependent tasks and
processing operations. It also emphasizes the use of Python code as the
experiment implementation, encouraging best practices in creating experiments
that are reproducible and extensible.

AxoPy provides the following core functionality:

- Graphical interface:

    Central to AxoPy is the graphical user interface providing visual feedback
    to the subject and controlling the flow of the experiment. The GUI is
    backed by PyQt5, and the researcher is free to implement customized
    graphical elements if those built in to AxoPy aren't sufficient.

- Data acquisition:

    AxoPy establishes an API for communicating with input hardware, so all
    that's usually needed is a bit of middleware to get going. A couple input
    devices are built in (keyboard, noise generator), so examples can be run
    without needing special hardware.

- Data storage:

    Data is stored in a file structure with common file formats (CSV and HDF5)
    so the researcher can a) start working with data as soon as an experiment
    session is over and b) standard tools (e.g. pandas, h5py) and even
    different programming languages can be used to work with datasets.
    A high-level interface to the storage structure is also provided to make
    traversing a dataset painless.

- Pipeline processing:

    Estimating intentions of a user from raw electrophysiological signals often
    involves a large number of processing operations. AxoPy facilitates
    flexible construction of pipelines that can be reused in different parts of
    an experiment and re-used for offline post-processing, and many processing
    operations are built in such as windowing, filtering, and feature extraction.

AxoPy has been used to implement research experiments involving the use of
surface electromyography for applications like prosthesis control
[@LyonsJoshi-EMBC2018] and communication devices [@OmearaEtAl-NER2019].

# References
