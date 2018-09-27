.. _graphics:

========
Graphics
========

.. currentmodule:: axopy.gui.main

Each task in an AxoPy experiment is given a :class:`Container`. The container
is effectively an empty ``QWidget`` from Qt_, so you can set up its contents
quite flexibly. That is, any valid ``QWidget`` or ``QLayout`` can be used as
the container's contents, so you can create arbitrarily complex graphics for
a task.

To set up graphics for a task, override the :meth:`Task.prepare_graphics
<axopy.task.Task.prepare_graphics>` method, which takes the :class:`Container`
as an input argument, then use :meth:`Container.set_widget` to establish the
main widget for the task.

.. code-block:: python

    from axopy.task import Task

    class CanvasTask(Task):

        def prepare_graphics(self, container):
            # set up graphical widget/layout here
            widget = ...
            container.set_widget(widget)

While you can always set up completely custom graphics using PyQt5_ classes
directly, AxoPy includes some graphical elements commonly used in
human-computer interface experiments, making it possible to write experiments
without knowing how to use Qt.

.. note::

    In the examples below, :func:`get_qtapp` will be used to demonstrate
    different graphical widgets and layouts. This function creates or retrieves
    a ``QApplication`` instance. We can then use ``app.exec_()`` to run the Qt
    event loop and test out the graphics code.

.. _Qt: https://www.qt.io/
.. _PyQt5: https://www.riverbankcomputing.com/software/pyqt/intro


Built-In Graphics Widgets
=========================

.. _canvas:

Canvas Graphics
---------------

.. currentmodule:: axopy.gui.canvas

The :mod:`axopy.gui.canvas` module contains a :class:`Canvas` class which can
be directly inserted into a container. You can then add items like
a :class:`Circle` or :class:`Text` to the canvas. In the context of a task, you
can create a canvas as follows:

.. code-block:: python

    from axopy.gui.main import get_qtapp
    from axopy.gui.canvas import Canvas, Circle

    app = get_qtapp()

    canvas = Canvas()
    canvas.add_item(Circle(0.1, color='red'))

    canvas.show()
    app.exec_()

All of the built-in items inherit from the :class:`Item` class, which means
they all have a number of properties that can be set, such as the position and
visibility.

.. code-block:: python

    canvas = Canvas()
    circle = Circle(0.1)
    canvas.add_item(circle)

    # set the x coordinate
    circle.x = 0.5
    # read the y coordinate
    y = circle.y
    # hide the circle
    circle.hide()

All of the :class:`Item` classes are actually just wrappers around
QGraphicsItem_ classes. In general, the various subclasses of ``QGraphicsItem``
(e.g. ``QGraphicsEllipseItem``) have a large number of methods that may not be
exposed by AxoPy, so all items have a ``qitem`` attribute pointing to
the underlying ``QGraphicsItem``. For example, the :class:`Line` item wraps
a QGraphicsLineItem_. In AxoPy, a line is just a solid line with a specific cap
style. If you need to customize this behavior, you can use the ``qitem``
attribute and dig into the Qt API:

.. code-block:: python

    from axopy.gui.canvas import Line

    # horizontal line 0.4 units long
    line = Line(-0.2, 0, 0.2, 0)


.. _QGraphicsItem: http://doc.qt.io/qt-5/qgraphicsitem.html
.. _QGraphicsLineItem: http://doc.qt.io/qt-5/qgraphicslineitem.html

Custom Items
^^^^^^^^^^^^
