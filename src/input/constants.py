import uinput

ABS_MAX, ABS_MIN = 32767, -32767
VIRTUAL_BUTTONS = (
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
VENDOR_CODE = 0x045E
PRODUCT_CODE = 0x028E
VERSION_CODE = 0x110
DEVICE_NAME = "Microsoft X-Box 360 pad"
