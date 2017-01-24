"""
Cursor control interface based on QGraphicsView.
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class CursorInterface(QtWidgets.QGraphicsView):
    """
    A 2D cursor control interface implemented using a QGraphicsView.

    This view essentially just holds a QGraphicsScene that grows to fit the
    size of the view, keeping the aspect ratio square. The scene is displayed
    with a gray border.
    """

    initleft = -200
    initbottom = initleft
    initwidth = -initleft*2
    initheight = -initleft*2

    border_color = '#444444'

    def __init__(self, parent=None):
        super(CursorInterface, self).__init__(parent)

        self._init_scene()
        self._init_border()

    def _init_scene(self):
        scene = QtWidgets.QGraphicsScene()
        scene.setSceneRect(self.initleft, self.initbottom,
                           self.initwidth, self.initheight)
        scene.setItemIndexMethod(QtWidgets.QGraphicsScene.NoIndex)

        self.setScene(scene)
        self.setRenderHint(QtGui.QPainter.Antialiasing)

        self.setBackgroundBrush(QtCore.Qt.white)

    def _init_border(self):
        rect = self.scene().sceneRect()
        pen = QtGui.QPen(QtGui.QColor(self.border_color))
        lines = [
            QtCore.QLineF(rect.topLeft(), rect.topRight()),
            QtCore.QLineF(rect.topLeft(), rect.bottomLeft()),
            QtCore.QLineF(rect.topRight(), rect.bottomRight()),
            QtCore.QLineF(rect.bottomLeft(), rect.bottomRight())
        ]
        for line in lines:
            self.scene().addLine(line, pen)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def map_coords(self, nx, ny):
        return self.map_size(nx), -self.map_size(ny)

    def map_size(self, size):
        return size * (self.sceneRect().width()/2)


class CircleItem(QtWidgets.QGraphicsObject):
    """
    A position-controlled circular item, such as a cursor or target.
    """

    def __init__(self, radius, color='#333333'):
        super(CircleItem, self).__init__()

        self._radius = None
        self.radius = radius
        self._color = None
        self.color = color

        self._norm_x = 0
        self._norm_y = 0

        self._init_bounding_rect(self._radius)
        self._init_shape()

    def _init_bounding_rect(self, radius):
        self._bounding_rect = QtCore.QRectF(-radius, -radius,
                                            2*radius, 2*radius)

    def _init_shape(self):
        p = QtGui.QPainterPath()
        p.addEllipse(self.boundingRect())
        self._shape = p

    def boundingRect(self):
        return self._bounding_rect

    def shape(self):
        return self._shape

    def paint(self, painter, option, widget):
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(self._color)
        painter.drawEllipse(self._bounding_rect)

    @QtCore.pyqtProperty(QtCore.QPointF)
    def norm_pos(self):
        return QtCore.QPointF(self._norm_x, self._norm_y)

    @norm_pos.setter
    def norm_pos(self, pos):
        if type(pos) == tuple:
            self.norm_x, self.norm_y = pos
        else:
            self.norm_x = pos.x()
            self.norm_y = pos.y()

    @QtCore.pyqtProperty(float)
    def norm_x(self):
        return self._norm_x

    @norm_x.setter
    def norm_x(self, value):
        self._norm_x = value
        self.setX(self.scene().width()/2*self._norm_x)

    @QtCore.pyqtProperty(float)
    def norm_y(self):
        return self._norm_y

    @norm_y.setter
    def norm_y(self, value):
        self._norm_y = value
        self.setY(-self.scene().width()/2*self._norm_y)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = QtGui.QColor(value)
        self.update()

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._radius = value
        self._init_bounding_rect(self._radius)
        self.update()


class PositionAnimation(QtCore.QPropertyAnimation):

    def __init__(self, item, duration):
        super(PositionAnimation, self).__init__(
            item, "norm_pos".encode('latin-1'))
        self.setDuration(duration)

    def set_next_pos(self, x, y):
        self.setStartValue(self.targetObject().norm_pos)
        self.setEndValue(QtCore.QPointF(x, y))
        self.start()

    def running(self):
        return self.state() == QtCore.QAbstractAnimation.Running


"""
Some common widgets for prompting subject response.
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class ImagePrompt(QtWidgets.QLabel):
    """
    Displays an image (QPixmap), centered and fit to the containing widget.
    """

    def __init__(self, parent=None):
        super(ImagePrompt, self).__init__(parent)
        self._pixmap_src = None
        self._pixmap = None

    def set_image(self, path):
        """
        Convenience method for setting the image by path.

        Parameters
        ----------
        path : str
            Path to the image file.
        """
        self.setPixmap(QtGui.QPixmap(path))

    def setPixmap(self, pixmap):
        """
        Overrides the QLabel method. Can be called directly.

        Parameters
        ----------
        pixmap : QPixmap
            The image to fill the label.
        """
        self._pixmap_src = pixmap
        self._pixmap = pixmap
        self.repaint()

    def paintEvent(self, event):
        """
        Overrides the QLabel method. Shouldn't need to be called directly.
        """
        super().paintEvent(event)

        if self._pixmap_src is None:
            return

        self._pixmap = self._pixmap_src.scaled(
            self.size(), QtCore.Qt.KeepAspectRatio)

        x = (self.width() - self._pixmap.width())/2
        y = (self.height() - self._pixmap.height())/2

        painter = QtGui.QPainter(self)
        painter.drawPixmap(x, y, self._pixmap)


class ImageDeck(ImagePrompt):
    """

    Parameters
    ----------
    image_paths : dict
        Dictionary mapping image names to their paths.
    """

    def __init__(self, image_paths, parent=None):
        super(ImageDeck, self).__init__(parent=parent)
        self.image_paths = image_paths
        self.pixmaps = {k: QtGui.QPixmap(v) for k, v in image_paths.items()}

    def set_image(self, name):
        self.setPixmap(self.pixmaps[name])


class LabelDeck(QtWidgets.QLabel):
    """
    Parameters
    ----------
    labels : dict
        Dictionary mapping label names to the text to show.
    """

    def __init__(self, labels, parent=None):
        super(LabelDeck, self).__init__(parent)
        self.labels = labels
        self.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.clear()

    def set_image(self, name):
        self.setText(self.labels[name])

    def clear(self):
        if 'clear' in self.labels:
            self.set_image('clear')
        else:
            self.setText('')


class AnnotatedProgressBar(QtWidgets.QProgressBar):
    """
    A custom QProgressBar which paints tick marks and a highlight bar over the
    base bar. The ticks can be used, for instance, for indicating the number
    of seconds in a trial. The highlight bar can be used to indicate the
    boundaries of some event during the trial.

    Examples
    --------
    >>> from axopy.widgets import AnnotatedProgressBar
    >>> ui = AnnotatedProgressBar()
    >>> ui.ticks = 5
    >>> ui.transitions = (2, 4)
    """

    def __init__(self, parent=None):
        super(AnnotatedProgressBar, self).__init__(parent)

        self.value = 0
        self._ticks = 1
        self._update_tick_labels()
        self._transitions = (0, 1)

        self.setMinimumHeight(40)
        self.setMinimumWidth(300)

        self.palette = QtGui.QPalette()

    @property
    def ticks(self):
        return self._ticks

    @ticks.setter
    def ticks(self, value):
        self._ticks = value
        self._update_tick_labels()
        self.repaint()

    @property
    def transitions(self):
        return self._transitions

    @transitions.setter
    def transitions(self, value):
        self._transitions = value
        self.repaint()

    def _update_tick_labels(self):
        self.tick_labels = [str(i) for i in range(1, int(self._ticks))]

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter()
        painter.begin(self)
        self.draw_ticks(painter)
        painter.end()

    def reset(self):
        self.setValue(0)

    def draw_ticks(self, painter):
        w = self.width()
        h = self.height()

        tick_step = int(round(w / self._ticks))

        f1 = int(((w / float(self._ticks*1000)) * self._transitions[0]*1000))
        f2 = int(((w / float(self._ticks*1000)) * self._transitions[1]*1000))

        # the contract indicator window
        painter.setPen(QtGui.QColor(0, 0, 0, 0))
        painter.setBrush(QtGui.QColor(180, 80, 80, 140))
        painter.drawRect(f1, 0, f2-f1, h)

        painter.setPen(self.palette.color(QtGui.QPalette.Text))
        painter.setFont(self.font())

        # draw the "contact" and "rest" text
        for t, l in zip(self._transitions, ['contract', 'rest']):
            x = int(((w / float(self._ticks*1000)) * (t*1000.)))
            metrics = painter.fontMetrics()
            fw = metrics.width(l)
            painter.drawText(x-fw/2, h/2, l)

        # draw the ticks marking each second
        j = 0
        for i in range(tick_step, self._ticks*tick_step, tick_step):
            painter.drawLine(i, h-5, i, h)
            metrics = painter.fontMetrics()
            fw = metrics.width(self.tick_labels[j])
            painter.drawText(i-fw/2, h-7, self.tick_labels[j])
            j += 1
