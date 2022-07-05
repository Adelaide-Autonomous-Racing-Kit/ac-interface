import pyautogui
import time

from controller import XBox360Controller
from shared_memory import AssettoCorsaData
from window_manager import WindowManager

def main():
    gamepad = XBox360Controller()
    acd = AssettoCorsaData()
    start_AC_from_CM()

    while True:
        if acd.has_AC_started():
            print("Simulation is running")
            start_race_in_AC()
            break
    
    time.sleep(12)
    print("Pressed")
    gamepad.shift_up()
    
    while True:
        gamepad.accelerate(0.5)


def start_AC_from_CM():
    cm_manager = WindowManager()
    cm_manager.find_window_wildcard("Content Manager")
    cm_manager.set_foreground()
    pyautogui.keyDown("ctrl")
    pyautogui.press("g")
    pyautogui.keyUp("ctrl")

def start_race_in_AC():
    ac_manager = WindowManager()
    ac_manager.find_window_wildcard("Assetto Corsa")
    ac_manager.set_foreground()
    x, y, _, _ = ac_manager.get_window_coordinates()
    pyautogui.click(x + 50, y + 175)

if __name__=='__main__':
    main()