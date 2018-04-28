from PyQt5 import QtCore, QtGui, QtWidgets


class Canvas(QtWidgets.QGraphicsView):
    """A 2D canvas interface implemented using a QGraphicsView.

    This view essentially just holds a QGraphicsScene that grows to fit the
    size of the view, keeping the aspect ratio square. The scene is displayed
    with a gray border.
    """

    scaler = 1
    border_width = 0.01

    default_border_color = '#444444'
    default_bg_color = '#dddddd'

    def __init__(self, draw_border=True, bg_color=None, border_color=None,
                 parent=None, invert_x=False, invert_y=False):
        super().__init__(parent=parent)

        if bg_color is None:
            bg_color = self.default_bg_color
        self.bg_color = bg_color

        if border_color is None:
            border_color = self.default_border_color
        self.border_color = border_color

        self.invert_x = invert_x
        self.invert_y = invert_y

        self._init_scene()
        if draw_border:
            self._init_border()

    def _init_scene(self):
        scene = QtWidgets.QGraphicsScene()
        # x, y, width, height
        scene.setSceneRect(-self.scaler, -self.scaler,
                           self.scaler*2, self.scaler*2)
        self.setScene(scene)

        if self.invert_x:
            self.scale(-1, 1)

        # Qt is positive downward, so invert logic for y inversion
        if not self.invert_y:
            self.scale(1, -1)

        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setBackgroundBrush(QtGui.QColor(self.bg_color))

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

    def add_item(self, item):
        self.scene().addItem(item)

    def resizeEvent(self, event):
        # override resize event to keep the scene rect intact (everything
        # scales with the window changing size, aspect ratio is preserved)
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), QtCore.Qt.KeepAspectRatio)


class Circle(QtWidgets.QGraphicsEllipseItem):

    def __init__(self, size, color='#333333'):
        self.size = size
        super().__init__(-size/2, -size/2, size, size)
        self.setBrush(QtGui.QColor(color))
        pen = QtGui.QPen(QtGui.QBrush(), 0)
        self.setPen(pen)

    def set_color(self, color):
        self.setBrush(QtGui.QColor(color))


class Cross(QtWidgets.QGraphicsItemGroup):

    default_size = 0.05
    default_linewidth = 0.01

    def __init__(self, size=None, linewidth=None, color='#333333'):
        super().__init__()
        if size is None:
            size = self.default_size
        self.size = size

        if linewidth is None:
            linewidth = self.default_linewidth
        self.linewidth = linewidth

        # horizontal line
        self.addToGroup(Line(-size/2, 0, size/2, 0, width=self.linewidth))
        # vertical line
        self.addToGroup(Line(0, -size/2, 0, size/2, width=self.linewidth))


class Line(QtWidgets.QGraphicsLineItem):

    default_width = 0.01

    def __init__(self, x1, y1, x2, y2, width=None, color='#333333'):
        super().__init__(x1, y1, x2, y2)
        if width is None:
            width = self.default_width
        self.width = width

        pen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(color)),
                         self.width,
                         cap=QtCore.Qt.FlatCap)
        self.setPen(pen)


class Text(QtWidgets.QGraphicsSimpleTextItem):

    def __init__(self, text, color='#333333'):
        super(Text, self).__init__(text)
        self.setBrush(QtGui.QColor(color))

        # invert because Canvas is inverted
        self.scale(0.01, -0.01)

        self._center()

    def _center(self):
        scene_bounds = self.sceneBoundingRect()
        self.setX(-scene_bounds.width()/2)
        self.setY(scene_bounds.height()/2)
