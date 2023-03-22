import os
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm

from src.analysis.segmentation import DataGenerator


def main():
    root_path = Path(os.path.dirname(__file__))
    config_path = root_path.joinpath("monza/config.yaml")
    data_generator = DataGenerator(config_path)
    video_path = data_generator.output_path.joinpath("monza_audi_r8.avi")
    image_size = data_generator.image_size
    video_size = (2 * image_size[0], image_size[1])
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    frame_rate = 30 // data_generator._config["sample_every"]
    output = cv2.VideoWriter(str(video_path), fourcc, frame_rate, video_size)
    for record in tqdm(data_generator._get_subsample()):
        root_path = str(data_generator.recording_path.joinpath(record))
        mask = cv2.imread(root_path + "-colour.png")
        image = cv2.imread(root_path + ".jpeg")
        to_show = np.hstack([image, mask])
        output.write(to_show)
    output.release()


if __name__ == "__main__":
    main()
