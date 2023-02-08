import os
from pathlib import Path

GAME_NAME_TO_WINDOW_NAME = {
    "linux": {
        "ACC": "ac2-win64-shipping.exe",
        "AC": "acs.exe",
    },
    "windows": {},
    "darwin": {},
}


CONFIG_ROOT = os.path.dirname(__file__)
# Capture configuration files
GAME_CAPTURE_CONFIG_FILE = Path(CONFIG_ROOT, "capture/game_capture.yaml")
FFMPEG_CONFIG_FILE = Path(CONFIG_ROOT, "capture/ffmpeg.yaml")
RECORD_CONFIG_FILE = Path(CONFIG_ROOT, "capture/record.yaml")

# Bottle filepaths
BOTTLE_C_DRIVE_PATH = Path(Path.home(), ".cxoffice/Assetto_Corsa/drive_c")
AC_STEAM_PATH = Path(
    BOTTLE_C_DRIVE_PATH, "Program Files (x86)/Steam/steamapps/common/assettocorsa"
)
AC_USER_PATH = Path(BOTTLE_C_DRIVE_PATH, "users/crossover/Documents/Assetto Corsa")

# Default AC config paths
DEFAULT_RACE_INI_PATH = Path(AC_STEAM_PATH, "cfg/race.ini")


# User AC config paths
AC_USER_RACE_INI_PATH = Path(AC_USER_PATH, "cfg/race.ini")


# AC ini Override yamls
AC_OVERRIDE_RACE_INI_YAML_PATH = Path(CONFIG_ROOT, "simulation/defaults/race.yaml")
