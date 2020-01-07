"""
Widgets for plotting multi-channel signals.
"""
import numpy as np
import pyqtgraph as pg
from PyQt5.QtGui import QFont

class SignalWidget(pg.GraphicsLayoutWidget):
    """
    Scrolling oscilloscope-like widget for displaying real-time signals.

    Intended for multi-channel viewing, each channel gets its own row in the
    widget, and all channels share y-axis zoom.

    Parameters
    ----------
    channel_names : list, optional
        List of channel names.
    bg_color : pyqtgraph color, optional
        Background color. Default is None (i.e., default background color).
    y_range : tuple, optional
        Y-axis range. Default is (-1, 1).
    show_bottom : boolean or str
        Whether to show x-axis in plots. If set to ``last``, x-axis will only
        be visible in the last row.
    """

    def __init__(self, channel_names=None, bg_color=None, yrange=(-1,1),
                 show_bottom=False, xlabel=None):
        super(SignalWidget, self).__init__()

        self.plot_items = []
        self.plot_data_items = []

        self.n_channels = 0
        self.channel_names = channel_names
        self.bg_color = bg_color
        self.yrange = yrange
        self.show_bottom = show_bottom
        self.xlabel = xlabel

        self.setBackground(self.bg_color)

    def plot(self, y, x=None):
        """
        Adds a window of data to the widget.

        Previous windows are scrolled to the left, and the new data is added to
        the end.

        Parameters
        ----------
        y : ndarray, shape = (n_channels, n_samples)
            Window of data to add to the end of the currently-shown data.
        x : array, shape = (n_samples,), optional (default: None)
            Independent variable values that will be displayed on x axis.
        """
        nch, nsamp = y.shape
        if nch != self.n_channels:
            self.n_channels = nch

            if self.channel_names is None:
                self.channel_names = range(self.n_channels)

            self._update_num_channels()

        for i, pdi in enumerate(self.plot_data_items):
            if x is not None:
                pdi.setData(x, y[i])
            else:
                pdi.setData(y[i])

    def _update_num_channels(self):
        self.clear()

        self.plot_items = []
        self.plot_data_items = []
        pen = _MultiPen(self.n_channels)
        for i, name in zip(range(self.n_channels), self.channel_names):
            plot_item = self.addPlot(row=i, col=0)
            plot_data_item = plot_item.plot(pen=pen.get_pen(i), antialias=True)

            if self.show_bottom is not True:
                plot_item.showAxis('bottom', False)
            plot_item.showGrid(y=True, alpha=0.5)
            plot_item.setMouseEnabled(x=False)
            plot_item.setMenuEnabled(False)

            if self.n_channels > 1:
                label = "{}".format(name)
                plot_item.setLabels(left=label)

            if i > 0:
                plot_item.setYLink(self.plot_items[0])

            self.plot_items.append(plot_item)
            self.plot_data_items.append(plot_data_item)

        self.plot_items[0].disableAutoRange(pg.ViewBox.YAxis)
        self.plot_items[0].setYRange(*self.yrange)
        if self.show_bottom == 'last':
            self.plot_items[-1].showAxis('bottom', True)

        if self.xlabel is not None:
            self.plot_items[-1].setLabels(bottom=self.xlabel)


class BarWidget(pg.PlotWidget):
    """
    Bar graph widget for displaying real-time signals.

    Intended for multi-group viewing, each group can optionally use a
    different color.

    Parameters
    ----------
    channel_names : list, optional
        List of channel names.
    group_colors : list, optional
        List of pyqtgraph colors. One for each group.
    bg_color : pyqtgraph color, optional
        Background color. Default is None (i.e., default background color).
    y_range : tuple, optional
        Y-axis range. Default is (-1, 1).
    font_size : int, optional
        Axes font size. Default is 12.
    """

    def __init__(self, channel_names=None, group_colors=None, bg_color=None,
                 yrange=(-1,1), font_size=12):
        super(BarWidget, self).__init__()

        self.channel_names = channel_names
        self.group_colors = group_colors
        self.bg_color = bg_color
        self.yrange = yrange
        self.font_size = font_size

        self.plot_items = None
        self.plot_data_items = None

        self.n_channels = 0
        self.n_groups = 0

        self.showGrid(y=True, alpha=0.5)
        self.setBackground(self.bg_color)
        self.setMouseEnabled(x=False)
        self.setMenuEnabled(False)

        font = QFont()
        font.setPixelSize(self.font_size)
        self.getAxis('bottom').tickFont = font
        self.getAxis('left').tickFont = font

    def plot(self, data):
        """
        Plots a data sample.

        Parameters
        ----------
        data : ndarray, shape = (n_channels, n_groups) or (n_channels,)
            Data sample to show on the graph.
        """
        # Handle both cases: (n_channels, n_groups) and (n_channels,)
        data = np.reshape(data, (data.shape[0], -1))
        nch, ngr = data.shape

        if nch != self.n_channels or ngr != self.n_groups:
            self.n_channels = nch
            self.n_groups = ngr

            if self.channel_names is None:
                self.channel_names = range(self.n_channels)

            if self.group_colors is None:
                self.group_colors = [0.5] * self.n_groups  # default gray

            self._update_num_channels()

        for i, pdi in enumerate(self.plot_items):
            pdi.setOpts(height=data[:, i])

    def _update_num_channels(self):
        self.clear()

        self.plot_items = []
        self.plot_data_items = []
        for i, color in zip(range(self.n_groups), self.group_colors):
            width = 1./(self.n_groups+1)
            x = np.arange(self.n_channels) + (i - self.n_groups/2 + 0.5)*width
            plot_item = pg.BarGraphItem(x=x, height=0, width=width,
                                        brush=color, pen='k')

            self.plot_items.append(plot_item)
            self.addItem(plot_item)

        self.disableAutoRange(pg.ViewBox.YAxis)
        self.setYRange(*self.yrange)

        ax = self.getAxis('bottom')
        x_ticks = [(i, name) for i, name in enumerate(self.channel_names)]
        ax.setTicks([x_ticks])


class PolarWidget(pg.GraphicsLayoutWidget):
    """
    Polar graph widget for displaying real-time polar data.

    Parameters
    ----------
    max_value : float, optional
        Expected maximum value of the data. Default is 1.
    fill : boolean, optional
        If True, fill the space between the origin and the plot. Default is
        True.
    color : pyqtgraph color, optional
        Line color. Default is 'k'.
    width : float, optional
        Line width. Default is 3.
    circle_color : pyqtgraph color, optional
        Circe color. Default is 'k'.
    circle_width : float, optional
        Circle width. Default is 0.2.
    n_circles : int, optional
        Number of circles to draw. Default is 30.
    bg_color : pyqtgraph color, optional
        Background color. Default is None (i.e., default background color).
    """

    def __init__(self, max_value=1., fill=True, color='k', width=3.,
                 circle_color='k', circle_width=0.2, n_circles=30,
                 bg_color=None):
        super(PolarWidget, self).__init__()

        self.max_value = max_value
        self.fill = fill
        self.color = color
        self.width = width
        self.circle_color = circle_color
        self.circle_width = circle_width
        self.n_circles = n_circles
        self.bg_color = bg_color

        self.n_channels = 0

        self.plot_item = None
        self.plot_data_item = None

        self.setBackground(self.bg_color)

    def plot(self, data, color=None):
        """
        Plots a data sample.

        Parameters
        ----------
        data : ndarray, shape = (n_channels,) or (n_channels, 1)
            Data sample to show on the graph.
        """
        # Handle both cases: (n_channels,) and (n_channels, 1)
        data = np.reshape(data, (-1,))
        nch = data.size

        if nch != self.n_channels:
            self.n_channels = nch

            self._update_num_channels()

        if color is not None:
            self.plot_data_item.setPen(
                pg.mkPen(pg.mkColor(color), width=self.width))
            self.plot_data_item.setBrush(pg.mkBrush(pg.mkColor(color)))

        x, y = self._transform_data(data)
        self.plot_data_item.setData(x, y)


    def _update_num_channels(self):
        self.clear()

        self.plot_item = self.addPlot(row=0, col=0)
        self.plot_data_item = pg.PlotCurveItem(
            pen=pg.mkPen(self.color, width=self.width), antialias=True)
        if self.fill:
            self.plot_data_item.setFillLevel(1)
            fill_color = self.color
            self.plot_data_item.setBrush(pg.mkBrush(pg.mkColor(fill_color)))

        self.plot_item.addItem(self.plot_data_item)

        # Add polar grid lines
        self.plot_item.addLine(x=0, pen=pg.mkPen(
            color=self.circle_color, width=self.circle_width))
        self.plot_item.addLine(y=0, pen=pg.mkPen(
            color=self.circle_color, width=self.circle_width))

        for r in np.linspace(0., 3 * self.max_value, self.n_circles):
            circle = pg.QtGui.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
            circle.setPen(pg.mkPen(
                color=self.circle_color, width=self.circle_width))
            self.plot_item.addItem(circle)

        self.theta = np.linspace(0, 2 * np.pi, self.n_channels + 1)

        self.plot_item.showAxis('bottom', False)
        self.plot_item.showAxis('left', False)
        self.plot_item.showGrid(y=False, x=False)
        self.plot_item.setMouseEnabled(x=False)
        self.plot_item.setMenuEnabled(False)

        self.plot_item.setYRange(-self.max_value / 2, self.max_value / 2)
        self.plot_item.setXRange(-self.max_value / 2, self.max_value / 2)
        self.plot_item.setAspectLocked()

    def _transform_data(self, data):
        "Performs polar transformation. "
        # Connect end to start to make a continuous plot
        data = np.hstack((data, data[0]))

        x = data * np.cos(self.theta)
        y = data * np.sin(self.theta)

        return (x, y)


class _MultiPen(object):

    MIN_HUE = 160
    HUE_INC = 20
    VAL = 200

    def __init__(self, n_colors):
        self.n_colors = n_colors
        self.max_hue = self.MIN_HUE + n_colors*self.HUE_INC

    def get_pen(self, index):
        return pg.intColor(
            index, hues=self.n_colors,
            minHue=self.MIN_HUE, maxHue=self.max_hue,
            minValue=self.VAL, maxValue=self.VAL)
