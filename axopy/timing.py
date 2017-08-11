from axopy.messaging import transmitter, receiver


class IncrementalTimer(object):
    """Counts to a given number then transmits a timeout event.

    Parameters
    ----------
    max_count : int
        Number of iterations to go through before transmitting the `timeout`
        event. Must be greater than 1.
    """

    def __init__(self, max_count=1):
        max_count = int(max_count)
        if max_count < 1:
            raise ValueError('max_count must be > 1')

        self.max_count = max_count
        self.count = 0

    @receiver
    def increment(self):
        """Increment the counter `timeout` if `max_count` is reached."""
        self.count += 1

        if self.count == self.max_count:
            self.timeout()

    @transmitter()
    def timeout(self):
        """Transmitted when `max_count` is reached."""
        return

    def reset(self):
        """Resets the count to 0 to start over."""
        self.count = 0

