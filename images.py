import pyautogui
import win32gui

import cv2
import numpy as np

# TODO: Fragile as the window can be occulded
def capture_frame() -> np.array:
    ac_gui = win32gui.FindWindow(None, 'Assetto Corsa')
    x, y, x1, y1 = win32gui.GetClientRect(ac_gui)
    x, y = win32gui.ClientToScreen(ac_gui, (x, y))
    x1, y1 = win32gui.ClientToScreen(ac_gui, (x1 - x, y1 - y))
    image = pyautogui.screenshot(region=(x, y, x1, y1))
    return np.array(image)


def main():
    image = capture_frame()
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    cv2.imshow('image',image)
    cv2.waitKey(0) 

if __name__=='__main__':
    main()