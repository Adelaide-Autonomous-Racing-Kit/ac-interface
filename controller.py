import vgamepad as vg



class XBox360Controller:
    def __init__(self):
        self.gamepad = vg.VX360Gamepad()
        self.gamepad.reset()
    
    def accelerate(self, value):
        self.gamepad.right_trigger_float(value_float=value)
        self.gamepad.update()
    
    def brake(self, value):
        self.gamepad.left_trigger_float(value_float=value)
        self.gamepad.update()

    def shift_up(self):
        self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.gamepad.update()
        self.gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.gamepad.update()
    
    def shift_down(self):
        self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
        self.gamepad.update()
        self.gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
        self.gamepad.update()

