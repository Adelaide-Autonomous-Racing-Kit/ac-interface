import os
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm

ROOT = Path.home().joinpath("Documents")
SOURCE_1_PATH = ROOT.joinpath("generated/monza/audi_r8_lms_2016/test/")
SOURCE_2_PATH = ROOT.joinpath("generated/monza/audi_r8_lms_2016/test/")
OUTPUT_VIDEO_PATH = ROOT.joinpath(
    "generated/monza/audi_r8_lms_2016/test-overlay.avi"
)
IMAGE_SIZE = (1920, 1080)


def main():
    frames = sorted(
        [
            frame[:-5]
            for frame in os.listdir(SOURCE_1_PATH)
            if frame[-4:] == "jpeg"
        ],
        key=lambda x: int(x),
    )
    video_size = (IMAGE_SIZE[0], IMAGE_SIZE[1])
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    output = cv2.VideoWriter(str(OUTPUT_VIDEO_PATH), fourcc, 30, video_size)
    for record in tqdm(frames):
        mask_path = SOURCE_2_PATH.joinpath(record + "-vis").with_suffix(".png")
        image_path = SOURCE_1_PATH.joinpath(record).with_suffix(".jpeg")
        mask = cv2.imread(str(mask_path))
        # image = cv2.imread(str(image_path))
        # image = cv2.resize(image, dsize=(IMAGE_SIZE[0], IMAGE_SIZE[1]))
        # to_show = np.hstack([image, mask])
        to_show = mask
        output.write(to_show)
    output.release()


if __name__ == "__main__":
    main()
