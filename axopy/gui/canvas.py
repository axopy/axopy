"""2D canvas style graphics functionality backed by Qt's QGraphicsView."""

from PyQt5 import QtCore, QtGui, QtWidgets


class Canvas(QtWidgets.QGraphicsView):
    """A 2D canvas interface implemented using a QGraphicsView.

    This view essentially just holds a QGraphicsScene that grows to fit the
    size of the view, keeping the aspect ratio square. The scene is displayed
    with a gray (by default) border.

    See Qt's documentation for more information about working with
    QGraphicsView (https://doc.qt.io/Qt-5/qgraphicsview.html).
    """

    scaler = 1
    border_width = 0.01

    default_border_color = '#444444'
    default_bg_color = '#dddddd'

    def __init__(self, draw_border=True, bg_color=None, border_color=None,
                 parent=None, invert_x=False, invert_y=False):
        super(Canvas, self).__init__(parent=parent)

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
        """Add an item to the canvas.

        Parameters
        ----------
        item : Item or QGraphicsItem
            The item to add to the canvas. This can be either one of AxoPy's
            built-in items (:class:`Circle`, :class:`Text`, etc.) or any
            QGraphicsItem.
        """
        if isinstance(item, Item):
            self.scene().addItem(item.qitem)
        else:
            self.scene().addItem(item)

    def resizeEvent(self, event):
        # override resize event to keep the scene rect intact (everything
        # scales with the window changing size, aspect ratio is preserved)
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), QtCore.Qt.KeepAspectRatio)


class Item(object):
    """Canvas item base class.

    This is simply a wrapper around any kind of ``QGraphicsItem``, adding the
    ability to set some properties of the underlying item with a more Pythonic
    API. You can always access the ``QGraphicsItem`` with the ``qitem``
    attribute. Once you know what kind of ``QGraphicsItem`` is being wrapped,
    you can use the corresponding Qt documentation to make use of more complete
    functionality.

    Attributes
    ----------
    qitem : QGraphicsItem
        The QGraphicsItem being wrapped. You can use this attribute to access
        methods and properties of the item not exposed by the wrapper class. If
        you find yourself routinely using a method of the QGraphicsItem,
        consider recommending it for addition to AxoPy.
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
        """Both X and Y coordinates of the item in the canvas."""
        return self.x, self.y

    @pos.setter
    def pos(self, pos):
        self.qitem.setPos(*pos)

    @property
    def visible(self):
        """Visibility of the item."""
        return self.qitem.isVisible()

    @visible.setter
    def visible(self, visible):
        self.qitem.setVisible(visible)

    @property
    def opacity(self):
        """Opacity of the item (between 0 and 1)."""
        self.qitem.opacity()

    @opacity.setter
    def opacity(self, opacity):
        self.qitem.setOpacity(opacity)

    @property
    def color(self):
        """Color of the item."""
        return self.qitem.brush().color().getRgb()

    @color.setter
    def color(self, color):
        self.qitem.setBrush(QtGui.QColor(color))

    def show(self):
        """Set the item to visible."""
        self.qitem.show()

    def hide(self):
        """Set the item to invisible."""
        self.qitem.hide()

    def set(self, **kwargs):
        """Set any properties of the underlying QGraphicsItem."""
        for prop, val in kwargs.items():
            self._qmeth(prop)(val)

    def get(self, prop, *args, **kwargs):
        """Get any property of the underlying QGraphicsItem."""
        self._qmeth(prop)(*args, **kwargs)

    def collides_with(self, item):
        """Determine if the item intersects with another item."""
        return self.qitem.collidesWithItem(item.qitem)

    def _qmeth(self, prop):
        return getattr(self.qitem, _to_camel_case(prop))


def _to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class Circle(Item):
    """Circular item.

    The coordinates of this item correspond to the center of the circle.

    Parameters
    ----------
    dia : float
        Diameter of the circle with respect to the scene coordinate system.
    color : str
        Hex string to set the color of the circle. You can use the underlying
        ``qitem`` attribute to get the underlying QGraphicsEllipseItem to set
        stroke color vs. fill color, etc. if needed.
    """

    def __init__(self, diameter, color='#333333'):
        qitem = QtWidgets.QGraphicsEllipseItem(-diameter/2, -diameter/2,
                                               diameter, diameter)
        qitem.setPen(QtGui.QPen(QtGui.QBrush(), 0))
        super(Circle, self).__init__(qitem)
        self.color = color


class Cross(Item):
    """Collection of two lines oriented as a "plus sign".

    The coordinates of this item correspond to the center of the cross. This
    item's ``qitem`` attribute is a ``QGraphicsItemGroup`` (a group of two
    lines).

    Parameters
    ----------
    size : float
        The size is the length of each line making up the cross.
    linewidth : float
        Thickness of each line making up the cross.
    color : str
        Color of the lines making up the cross.
    """

    def __init__(self, size=0.05, linewidth=0.01, color='#333333'):
        qitem = QtWidgets.QGraphicsItemGroup()
        self._lh = Line(-size/2, 0, size/2, 0, width=linewidth, color=color)
        self._lv = Line(0, -size/2, 0, size/2, width=linewidth, color=color)
        qitem.addToGroup(self._lh.qitem)
        qitem.addToGroup(self._lv.qitem)
        super(Cross, self).__init__(qitem)

    @property
    def color(self):
        """Color of the lines in the cross."""
        return self._lv.color

    @color.setter
    def color(self, color):
        self._lh.color = color
        self._lv.color = color


class Line(Item):
    """Line item."""

    def __init__(self, x1, y1, x2, y2, width=0.01, color='#333333'):
        self.width = width
        qitem = QtWidgets.QGraphicsLineItem(x1, y1, x2, y2)
        super(Line, self).__init__(qitem)
        self.color = color

    @property
    def color(self):
        return self.qitem.pen().color().getRgb()

    @color.setter
    def color(self, color):
        self.qitem.setPen(QtGui.QPen(QtGui.QBrush(QtGui.QColor(color)),
                                     self.width, cap=QtCore.Qt.FlatCap))


class Text(Item):
    """Text item."""

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


class Rectangle(Item):
    """Rectangular item.

    This is a filled retangle that allows you to set the size, color, position,
    etc. By default, the item's position is its *center*.
    """

    def __init__(self, width, height, x=0, y=0, color='#333333',
                 penwidth=0.01):
        self.penwidth = penwidth

        qitem = QtWidgets.QGraphicsRectItem(x, y, width, height)
        qitem.setTransformOriginPoint(width/2, height/2)
        qitem.setTransform(QtGui.QTransform().translate(-width/2, -height/2))
        super(Rectangle, self).__init__(qitem)

        self.pos = x, y
        self.color = color

    @property
    def color(self):
        """Color of the rectangle."""
        return self.qitem.pen().color().getRgb()

    @color.setter
    def color(self, color):
        """Color of the rectangle."""
        br = QtGui.QBrush(QtGui.QColor(color))
        self.qitem.setBrush(br)
        self.qitem.setPen(QtGui.QPen(br, self.penwidth,
                                     cap=QtCore.Qt.FlatCap))

    @property
    def width(self):
        return self.qitem.rect().width()

    @width.setter
    def width(self, width):
        p = self.pos
        rect = self.qitem.rect()
        rect.setWidth(width)
        self.qitem.setRect(rect)
        self.pos = p


class Basket(Item):
    """Collection of two lines oriented as a "V sign".

    Parameters
    ----------
    xy_origin : tuple
        Coordinates of bottom basket.
    xy_rotate : float, optional (default = 45)
        Basket rotation (in degrees).
    size : float, optional (default = 0.2)
        The size is the length of each line making up the basket.
    linewidth : float, optional (default = 0.01)
        Thickness of each line making up the basket.
    color : str or QColor, optional (default = 'white')
        Color of the lines making up the basket.
    """

    def __init__(self, xy_origin, xy_rotate=45, size=0.2,
                 linewidth=0.01, color='white'):
        path = QtGui.QPainterPath()
        path.moveTo(0., 0.)
        path.arcTo(-size, size, 2*size, -2*size, 0, 90)
        path.closeSubpath()
        qitem = QtWidgets.QGraphicsPathItem(path)
        self.br = QtGui.QBrush(QtGui.QColor(color))
        qitem.setPen(QtGui.QPen(self.br, linewidth))
        qitem.rotate(xy_rotate)
        qitem.setPos(xy_origin[0], xy_origin[1])
        super(Basket, self).__init__(qitem)

        self.xy_origin = xy_origin
        self.xy_rotate = xy_rotate
        self.size = size
        self.linewidth = linewidth


class Target(Item):
    """Collection of lines and arches that form a target in the V-shaped task.
    Defined with respect to a specified origin (e.g. a basket).

    Parameters
    ----------
    xy_origin : tuple
        Coordinates of origin.
    theta_target : float
        Target width (in degrees).
    r1 : float
        Small radius.
    r2 : float
        Large radius.
    rotation : float
        Target rotation (in degrees).
    linewidth : float
        Thickness of each line that makes up the target
    color = str
        Color of the lines making up the target
    """

    def __init__(self, xy_origin, theta_target, r1=0.5, r2=0.8, rotation=90,
                 linewidth=0.01, color='white'):
        path = QtGui.QPainterPath()
        path.moveTo(r1, 0)
        path.arcTo(-r1, r1, 2*r1, -2*r1, 0, theta_target)
        path.arcTo(-r2, r2, 2*r2, -2*r2, theta_target, -theta_target)
        path.closeSubpath()
        qitem = QtWidgets.QGraphicsPathItem(path)
        self.br = QtGui.QBrush(QtGui.QColor(color))
        qitem.setPen(QtGui.QPen(self.br, linewidth))
        qitem.rotate(rotation)
        qitem.setPos(xy_origin[0], xy_origin[1])
        super(Target, self).__init__(qitem)

        self.xy_origin = xy_origin
        self.theta_target = theta_target
        self.r1 = r1
        self.r2 = r2
        self.rotation = rotation
        self.linewidth = linewidth

    @property
    def color(self):
        return self.br.color().getRgb()

    @color.setter
    def color(self, color):
        self.br = QtGui.QBrush(QtGui.QColor(color))
        self.qitem.setPen(QtGui.QPen(self.br, self.linewidth))
