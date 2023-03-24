import cv2
import os
from pathlib import Path
from PIL import Image

import numpy as np
import torch
from tqdm import tqdm
from torchvision import transforms
from torchvision.transforms import InterpolationMode

from segmentors.models import resnet, deeplabv3plus

ROOT = Path.home().joinpath("Documents")
WEIGHTS_PATH = ROOT.joinpath("deeplab-resnet18-OS8-monza-road-1.ckpt")
DATA_PATH = ROOT.joinpath("recordings/monza_audi_r8_lms_1")
OUTPUT_PATH = ROOT.joinpath("visualised")
ID_TO_COLOUR = np.array(
    [
        [84, 84, 84],
        [0, 0, 0],
        [255, 255, 255],
    ],
    dtype=np.uint8,
)
IMAGE_SIZE = (720, 1280)


def convert_from_lightning():
    state_dict = torch.load(WEIGHTS_PATH)["state_dict"]
    old_names = [x for x in state_dict.keys()]
    for parameter_name in old_names:
        new_name = parameter_name[7:]
        state_dict[new_name] = state_dict[parameter_name]
        del state_dict[parameter_name]

    torch.save(
        state_dict,
        Path.home().joinpath(
            "Documents/deeplab-resnet18-OS8-monza-road-1.ckpt"
        ),
    )


def main():
    encoder = resnet.ResnetEncoder(resnet.build("18", False), 8)
    decoder = deeplabv3plus.DeepLabV3plus(encoder, 3)

    decoder.load_state_dict(torch.load(WEIGHTS_PATH))
    decoder.eval()
    decoder = decoder.cuda()

    image_list = [
        filename
        for filename in os.listdir(DATA_PATH)
        if filename[-4:] == "jpeg"
    ]

    pytorch_transforms = [
        transforms.Resize(
            IMAGE_SIZE,
            InterpolationMode.NEAREST,
        ),
        transforms.ToTensor(),
    ]
    transform = transforms.Compose(pytorch_transforms)

    for image_name in tqdm(image_list):
        image = Image.open(DATA_PATH.joinpath(image_name))
        image = transform(image).unsqueeze(0).cuda()
        with torch.no_grad():
            mask = torch.argmax(decoder(image), dim=1).squeeze(0)
        visualised = ID_TO_COLOUR[mask.cpu()]
        save_path = OUTPUT_PATH.joinpath(image_name).with_suffix(".png")
        cv2.imwrite(str(save_path), visualised)


if __name__ == "__main__":
    main()
