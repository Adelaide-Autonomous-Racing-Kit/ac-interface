import cv2
import numpy as np


def image(image: np.array):
    cv2.imshow("OpenCV capture", image)
    cv2.waitKey(1)
