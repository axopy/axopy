import importlib


# default to Qt backend
gui_backend = 'qt'



class Experiment(object):

    def __init__(self):
        b = get_backend()
        mod = importlib.import_module('axopy.experiment.{}'.format(b))
        self.ui_backend = mod.ExperimentBackend()

    def run(self):
        self.ui_backend.run()


def set_backend(name):
    """Set the graphical backend of the Experiment.

    Parameters
    ----------
    name : str
        Name of the backend to use. Available values are 'qt'.
    """
    global _backend
    lname = name.lower()

    # add names to the tuple to support them
    # implement backends by adding a module with the same name
    if lname in ('qt'):
        _backend = lname
    else:
        raise ValueError("Experiment backend \'{}\' is not"
                         " supported".format(lname))


def get_backend():
    """Retrieve the graphical backend currently in use (or to be used)."""
    global _backend
    return _backend
