import os
import math

import cv2
import numpy as np
from tqdm import tqdm

from src.analysis.segmentation import RECORDED_DATA_PATH
from src.utils.load import load_game_state


def main():
    records = sorted(
        [
            record[:-4]
            for record in os.listdir(RECORDED_DATA_PATH)
            if record[-3:] == "bin"
        ],
        key=lambda x: int(x),
    )
    video_path = os.path.join(RECORDED_DATA_PATH, "monza_audi_r8.avi")
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    output = cv2.VideoWriter(video_path, fourcc, 30, (2 * 1920, 1080))
    for record in tqdm(records):
        root_path = os.path.join(RECORDED_DATA_PATH, record)
        mask = cv2.imread(root_path + "-colour.png")
        image = cv2.imread(root_path + ".jpeg")
        state = load_game_state(root_path + ".bin")
        to_show = np.hstack([image, mask])
        angles = [state["pitch"], state["heading"], state["roll"]]
        angles[1] = angles[1] + math.pi
        center = [
            state["ego_location_x"],
            state["ego_location_y"] + state["centre_of_gravity_height"],
            state["ego_location_z"],
        ]
        text = f"(X,Y,Z): {center} (pitch, yaw, roll): {angles}"
        to_show = cv2.putText(
            to_show,
            text,
            (800, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3,
        )
        cv2.imshow("hi", to_show)
        cv2.waitKey(1)
        output.write(to_show)
    output.release()


if __name__ == "__main__":
    main()
