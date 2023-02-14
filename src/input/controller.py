import time

import numpy as np
from src.input.constants import (
    ABS_MAX,
    DEVICE_NAME,
    PRODUCT_CODE,
    VENDOR_CODE,
    VERSION_CODE,
    VIRTUAL_BUTTONS,
)
import uinput


class VirtualGamepad:
    """
    Presents as an Xbox 360 controller to the OS acting as an interface
        for control algorithms with the simulator. Translates the agent
        action space from {0., 1.} for throttle and brake and {-1., 1.}
        for steering angle to the controller analog range of {ABS_MIN, ABS_MAX}.
    """

    def __init__(self):
        self.___setup_virtual_controller()
        self._action_events = {
            "steering": uinput.ABS_X,
            "brake": uinput.ABS_Z,
            "throttle": uinput.ABS_RZ,
        }

    def submit_action(self, action: np.array):
        """
        Accepts a numpy array representing the agent's actions to be relayed
        to the simulation. Translates and emits these actions as device events

        :action: An action as a np.array of [steering, brake, throttle]
        :type action: np.array
        """
        action = self._un_normalise_action(action)
        for event, action in zip(self._action_events.values(), action):
            self._device.emit(event, int(action))

    def _un_normalise_action(self, action: np.array) -> np.array:
        """
        Maps throttle and brake from {0.0, 1.0} to {ABS_MIN, ABS_MAX}
            and steering angle from {-1.0, 1.0} to {ABS_MIN, ABS_MAX}
        """
        action[1:] = (action[1:] - 0.5) * 2 * ABS_MAX
        action[0] = (action[0]) * ABS_MAX
        return action

    def ___setup_virtual_controller(self):
        # Virtual device details
        self._device = uinput.Device(
            VIRTUAL_BUTTONS,
            vendor=VENDOR_CODE,
            product=PRODUCT_CODE,
            version=VERSION_CODE,
            name=DEVICE_NAME,
        )
        # Time to allow steam to initialise the device
        time.sleep(2)


def main():
    vgamepad = VirtualGamepad()
    actions = [
        np.array([-1.0, 0.0, 0.0]),  # Full lock left
        np.array([0.0, 1.0, 0.0]),  # No Steer, Full brake
        np.array([0.0, 0.0, 0.0]),  # No Input
        np.array([0.0, 0.0, 1.0]),  # No Steer, Full throttle
        np.array([1.0, 0.0, 0.0]),  # Full lock right
    ]
    for action in actions:
        vgamepad.submit_action(action)
        time.sleep(5)


if __name__ == "__main__":
    main()
