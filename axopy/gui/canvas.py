from PyQt5 import QtCore, QtGui, QtWidgets


class Canvas(QtWidgets.QGraphicsView):
    """A 2D canvas interface implemented using a QGraphicsView.

    This view essentially just holds a QGraphicsScene that grows to fit the
    size of the view, keeping the aspect ratio square. The scene is displayed
    with a gray border.
    """

    rect = (-100, -100, 200, 200) # x, y, w, h
    border_color = '#444444'
    border_width = 1

    def __init__(self, draw_border=True, parent=None):
        super().__init__(parent=parent)

        self._init_scene()
        if draw_border:
            self._init_border()

    def _init_scene(self):
        scene = QtWidgets.QGraphicsScene()
        scene.setSceneRect(*self.rect)

        self.setScene(scene)
        self.setRenderHint(QtGui.QPainter.Antialiasing)

        self.setBackgroundBrush(QtCore.Qt.white)

    def _init_border(self):
        rect = self.scene().sceneRect()
        pen = QtGui.QPen(QtGui.QColor(self.border_color), self.border_width)
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
