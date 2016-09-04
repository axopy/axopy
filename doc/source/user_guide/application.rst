.. _user_interface:

==============
User Interface
==============

.. currentmodule:: hcibench.application

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

Building on a Base
------------------

Some explanation of the :class:`BaseUI`.

.. _Qt: https://www.qt.io/
.. _PyQt5: https://www.riverbankcomputing.com/software/pyqt/intro
.. _QMainWindow: https://doc.qt.io/qt-5/qmainwindow.html
.. _QWidget: https://doc.qt.io/qt-5/qwidget.html
