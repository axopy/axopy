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
        self.scene().addItem(item.qitem)

    def resizeEvent(self, event):
        # override resize event to keep the scene rect intact (everything
        # scales with the window changing size, aspect ratio is preserved)
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), QtCore.Qt.KeepAspectRatio)


class Item(object):
    """Canvas item.

    This is simply a wrapper around any kind of ``QGraphicsItem``, adding the
    ability to set some properties of the underlying item with a more Pythonic
    API. You can always access the ``QGraphicsItem`` with the ``qitem``
    attribute.
    """

    def __init__(self, qitem):
        self.qitem = qitem

    @property
    def x(self):
        """X coordinate of the item in the canvas."""
        return self.qitem.x()

    @x.setter
    def x(self, x):
        self.qitem.setX(x)

    @property
    def y(self):
        """Y coordinate of the item in the canvas."""
        return self.qitem.y()

    @y.setter
    def y(self, y):
        self.qitem.setY(y)

    @property
    def pos(self):
        """X and Y coordinates of the item in the canvas."""
        return self.x(), self.y()

    @pos.setter
    def pos(self, pos):
        self.qitem.setPos(*pos)

    @property
    def visible(self):
        return self.qitem.visible()

    @visible.setter
    def visible(self, visible):
        self.qitem.setVisible(visible)

    @property
    def opacity(self):
        self.qitem.opacity()

    @opacity.setter
    def opacity(self, opacity):
        self.qitem.setOpacity(opacity)

    def show(self):
        self.qitem.show()

    def hide(self):
        self.qitem.hide()

    def set(self, **kwargs):
        """Set any properties of the underlying QGraphicsItem."""
        for prop, val in kwargs.items():
            self._qmeth(prop)(val)

    def get(self, prop, *args, **kwargs):
        self._qmeth(prop)(*args, **kwargs)

    def collides_with(self, item):
        """Determine if the item intersects with another item."""
        return self.qitem.collidesWithItem(item.qitem)

    def _qmeth(self, prop):
        return getattr(self.qitem, _to_camel_case(prop))


def _to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class ColorableMixin(object):

    @property
    def color(self):
        return self.qitem.brush().color().getRgb()

    @color.setter
    def color(self, color):
        self.qitem.setBrush(QtGui.QColor(color))


class Circle(Item, ColorableMixin):

    def __init__(self, size, color='#333333'):
        qitem = QtWidgets.QGraphicsEllipseItem(-size/2, -size/2, size, size)
        qitem.setPen(QtGui.QPen(QtGui.QBrush(), 0))
        super(Circle, self).__init__(qitem)
        self.color = color


class Cross(Item, ColorableMixin):

    def __init__(self, size=0.05, linewidth=0.01, color='#333333'):
        qitem = QtWidgets.QGraphicsItemGroup()
        lh = Line(-size/2, 0, size/2, 0, width=linewidth)
        lv = Line(0, -size/2, 0, size/2, width=linewidth)
        qitem.addToGroup(lh.qitem)
        qitem.addToGroup(lv.qitem)
        super(Cross, self).__init__(qitem)


class Line(Item):

    def __init__(self, x1, y1, x2, y2, width=0.01, color='#333333'):
        qitem = QtWidgets.QGraphicsLineItem(x1, y1, x2, y2)
        pen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(color)),
                         width,
                         cap=QtCore.Qt.FlatCap)
        qitem.setPen(pen)
        super(Line, self).__init__(qitem)


class Text(Item, ColorableMixin):

    def __init__(self, text, color='#333333'):
        qitem = QtWidgets.QGraphicsSimpleTextItem(text)
        super(Text, self).__init__(qitem)

        self.color = color

        # invert because Canvas is inverted
        self.qitem.scale(0.01, -0.01)

        self._center()

    def _center(self):
        scene_bounds = self.qitem.sceneBoundingRect()
        self.pos = -scene_bounds.width() / 2, scene_bounds.height() / 2
