import os
from pathlib import Path


GAME_NAME_TO_WINDOW_NAME = {
    "linux": {
        "ACC": {"ac2-win64-shipping.exe"},
        "AC": {"acs.exe", "steam_app_244210"},
    },
    "windows": {},
    "darwin": {},
}

CAMERA_POSITION_TO_MODE = {
    # "position": (MODE, DRIVABLE_MODE)
    "driver_pov": (0, 0),
    "chase": (2, 0),
    "chase_far": (2, 1),
    "bonnet": (2, 2),
    "road": (2, 3),
    "behind_steering_wheel": (2, 4),
}

STEAM_APPID = "244210"
CONFIG_ROOT = os.path.dirname(__file__)
# Capture configuration files
CAPTURE_CONFIG_FILE = Path(CONFIG_ROOT, "defaults/capture.yaml")

# ACI default configuration path
ACI_DEFAULT_CONFIG_PATH = Path(CONFIG_ROOT, "defaults/simulation")

CONFIG_FILES = [
    "race.ini",
    "camera_manager.ini",
    "video.ini",
    "assists.ini",
    "gameplay.ini",
    "controls.ini",
]

# Proton filepaths
PROTON_STEAM_ROOT_PATH = Path(Path.home(), ".local/share/Steam/steamapps")
PROTON_C_DRIVE_PATH = Path(PROTON_STEAM_ROOT_PATH, "compatdata/244210/pfx/drive_c")
PROTON_AC_STEAM_PATH = Path(PROTON_STEAM_ROOT_PATH, "common/assettocorsa")
PROTON_AC_USER_PATH = Path(
    PROTON_C_DRIVE_PATH, "users/steamuser/Documents/Assetto Corsa"
)
PROTON_AC_APPID_FILE_PATH = Path(PROTON_AC_STEAM_PATH, "steam_appid.txt")


# Bottle filepaths
CROSSOVER_C_DRIVE_PATH = Path(Path.home(), ".cxoffice/Assetto_Corsa/drive_c")
CROSSOVER_AC_STEAM_PATH = Path(
    CROSSOVER_C_DRIVE_PATH, "Program Files (x86)/Steam/steamapps/common/assettocorsa"
)
CROSSOVER_AC_STEAM_APPID_FILE_PATH = Path(CROSSOVER_AC_STEAM_PATH, "steam_appid.txt")
CROSSOVER_AC_USER_PATH = Path(
    CROSSOVER_C_DRIVE_PATH, "users/crossover/Documents/Assetto Corsa"
)

CONFIG_PATHS = {
    "crossover": {
        "steam": Path(CROSSOVER_AC_STEAM_PATH, "cfg"),
        "user": Path(CROSSOVER_AC_USER_PATH, "cfg"),
    },
    "proton": {
        "steam": Path(PROTON_AC_STEAM_PATH, "cfg"),
        "user": Path(PROTON_AC_USER_PATH, "cfg"),
    },
}
