from axopy.blocks.base import Block


class WidgetBlock(Block):
    """Qt widget block.

    Wraps any `QWidget` for use as a task's UI. Not sure if this is necessary
    at the moment. The widget blocks will probably just have to conform to an
    interface rather than having things taken care of in a base class.
    """
    pass
