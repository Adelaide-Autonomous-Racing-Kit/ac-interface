import time

import uinput
import numpy as np

ABS_MAX, ABS_MIN = 32767, -32767


def setup_virtual_controller() -> uinput.Device:
    events = (
        uinput.BTN_A,  # Shift Up
        uinput.BTN_B,
        uinput.BTN_X,
        uinput.BTN_Y,
        uinput.BTN_TL,
        uinput.BTN_TR,
        uinput.BTN_THUMBL,
        uinput.BTN_THUMBR,
        uinput.ABS_X,  # Steering
        uinput.ABS_Y,
        uinput.ABS_Z,  # Brake
        uinput.ABS_RX,
        uinput.ABS_RY,
        uinput.ABS_RZ,  # Throttle
    )

    device = uinput.Device(
        events,
        vendor=0x045E,
        product=0x028E,
        version=0x110,
        name="Microsoft X-Box 360 pad",
    )
    time.sleep(2)  # Time to allow steam to initialise the device
    return device


class VirtualGamepad:
    def __init__(self):
        self._device = setup_virtual_controller()
        self._action_events = {
            "steering": uinput.ABS_X,
            "brake": uinput.ABS_Z,
            "throttle": uinput.ABS_RZ,
        }

    def submit_action(self, action: np.array):
        action = self._un_normalise_action(action)
        for event, action in zip(self._action_events.values(), action):
            self._device.emit(event, int(action))

    def _un_normalise_action(self, action: np.array) -> np.array:
        """
        Maps actions in {0.0, 1.0} to {ABS_MIN, ABS_MAX}
        """
        return (action - 0.5) * 2 * ABS_MAX


def main():
    vgamepad = VirtualGamepad()
    actions = [
        np.array([0.0, 0.0, 0.0]),  # Full lock left
        np.array([0.5, 1.0, 0.0]),  # No Steer, Full brake
        np.array([0.5, 0.0, 0.0]),  # No Input
        np.array([0.5, 0.0, 1.0]),  # No Steer, Full throttle
        np.array([1.0, 0.0, 0.0]),  # Full lock right
    ]
    for action in actions:
        vgamepad.submit_action(action)
        time.sleep(5)


if __name__ == "__main__":
    main()
