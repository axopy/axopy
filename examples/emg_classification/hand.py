import time

from can.interfaces.pcan.basic import PCAN_USBBUS1, PCAN_BAUD_1M, PCAN_TYPE_ISA
from robolimb import RoboLimbCAN

from utils import StoppableThread


class RoboLimbGrip(RoboLimbCAN):
    """
    A RoboLimb grip implementation.

    Grip execution is always implemented in a separate Thread. This is
    required so that the series of ``time.sleep()`` commands within grip
    execution do not block the main program. A StoppableThread is used so that
    it is possible to abort execution while a grip is being executed.

    The following state-machine control strategy is implemented:
    - When a grip is currently being executed, ignore all incomings grip
    commands except for ``open`` grip, which signals grip execution abortion.
    This does not apply to the special case where an ``open`` grip is being
    executed.
    - When no grip is currently being executed, allow an incoming grip to be
    executed unless it is the same as the most recently executed grip.
    """

    def __init__(self,
                 def_vel=297,
                 read_rate=0.02,
                 channel=PCAN_USBBUS1,
                 b_rate=PCAN_BAUD_1M,
                 hw_type=PCAN_TYPE_ISA,
                 io_port=0x3BC,
                 interrupt=3):
        super().__init__(
            def_vel,
            read_rate,
            channel,
            b_rate,
            hw_type,
            io_port,
            interrupt)

        self.grip = None
        self.executing = False

    def execute(self, grip, force=False):
        """Performs checks and issues a grip execution command."""
        allow_grip = False  # False by default, only allow in cases below

        # When force is False and a grip is currently being executed, only
        # allow ``open`` to interrupt current execution, unless an open grip is
        # currently being executed.
        if (force is False and self.executing is True):
            if grip == 'open':
                if self.executed_grip == 'open':
                    pass
                else:
                    self.abort_execution()
            else:
                pass
        # When force is True or no grip is being executed, allow grip execution
        # for any but the most recently executed grip.
        else:
            if (self.grip == grip):
                pass
            else:
                allow_grip = True

        if allow_grip:
            self._thread = StoppableThread(target=self._execute, args=(grip,))
            self._thread.start()

    def _execute(self, grip):
        """Performs grip execution. To be called only within a ``Thread``."""
        velocity = 297
        self.executing = True
        self.executed_grip = grip
        self.stop_all()
        if grip == 'open':
            self.open_fingers(velocity=velocity)
            time.sleep(1)
        elif grip == 'power':
            # Preparation
            [self.open_finger(i, velocity=velocity) for i in range(1, 6)]
            time.sleep(0.2)
            self.close_finger(6, velocity=velocity)
            time.sleep(1.3)
            # Execution
            self.stop_all()
            self.close_fingers(velocity=velocity, force=True)
            time.sleep(1)
        elif grip == 'lateral':
            # Preparation
            [self.open_finger(i, velocity=velocity) for i in range(1, 4)]
            time.sleep(0.2)
            self.open_finger(6, velocity=velocity, force=True)
            time.sleep(0.1)
            [self.stop_finger(i) for i in range(2, 4)]
            [self.close_finger(i, velocity=velocity) for i in range(2, 6)]
            time.sleep(1.2)
            # Execution
            self.stop_all()
            self.close_finger(1, velocity=velocity, force=True)
            time.sleep(1)
        elif grip == 'tripod':
            # Preparation
            [self.open_finger(i, velocity=velocity) for i in range(1, 4)]
            time.sleep(0.1)
            [self.stop_finger(i) for i in range(1, 4)]
            [self.close_finger(i, velocity=velocity) for i in range(4, 7)]
            time.sleep(1.4)
            # Execution
            self.stop_all()
            [self.close_finger(i, velocity=velocity, force=True)
             for i in range(1, 4)]
            time.sleep(1)
        elif grip == 'pointer':
            # Preparation
            [self.open_finger(i, velocity=velocity) for i in range(1, 3)]
            time.sleep(0.1)
            self.open_finger(6, velocity=velocity)
            time.sleep(1.4)
            # Execution
            self.stop_all()
            [self.close_finger(i, velocity=velocity, force=True)
             for i in [1, 3, 4, 5]]
            time.sleep(1)

        self.grip = grip
        self.executing = False
        self.executed_grip = None

    def stop(self):
        """Tidy up hand and then call ``stop`` method from parent class."""
        self.abort_execution()
        self.open_all()
        time.sleep(1.5)
        self.close_finger(1)
        time.sleep(1)
        super().stop()

    def abort_execution(self):
        """Aborts current grip execution."""
        self._thread.stop()
        self.stop_all()
