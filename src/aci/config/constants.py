from collections import namedtuple
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

# Bottle filepaths
BOTTLE_C_DRIVE_PATH = Path(Path.home(), ".cxoffice/Assetto_Corsa/drive_c")
AC_STEAM_PATH = Path(
    BOTTLE_C_DRIVE_PATH, "Program Files (x86)/Steam/steamapps/common/assettocorsa"
)
AC_STEAM_APPID_FILE_PATH = Path(AC_STEAM_PATH, "steam_appid.txt")
AC_USER_PATH = Path(BOTTLE_C_DRIVE_PATH, "users/crossover/Documents/Assetto Corsa")

# Default AC config paths
DEFAULT_RACE_INI_PATH = Path(AC_STEAM_PATH, "cfg/race.ini")
DEFAULT_CAMERA_MANAGER_INI_PATH = Path(AC_STEAM_PATH, "cfg/camera_manager.ini")
# TODO: Load video.ini with proper defaults
DEFAULT_VIDEO_INI_PATH = Path(AC_STEAM_PATH, "cfg/camera_video.ini")
DEFAULT_ASSISTS_INI_PATH = Path(AC_STEAM_PATH, "cfg/assists.ini")
DEFAULT_GAMEPLAY_INI_PATH = Path(AC_STEAM_PATH, "cfg/gameplay.ini")
DEFAULT_CONTROLS_INI_PATH = Path(AC_STEAM_PATH, "cfg/controls.ini")

# User AC config paths
AC_USER_RACE_INI_PATH = Path(AC_USER_PATH, "cfg/race.ini")
AC_USER_CAMERA_MANAGER_INI_PATH = Path(AC_USER_PATH, "cfg/camera_manager.ini")
AC_USER_VIDEO_INI_PATH = Path(AC_USER_PATH, "cfg/video.ini")
AC_USER_ASSISTS_INI_PATH = Path(AC_USER_PATH, "cfg/assists.ini")
AC_USER_GAMEPLAY_INI_PATH = Path(AC_USER_PATH, "cfg/gameplay.ini")
AC_USER_CONTROLS_INI_PATH = Path(AC_USER_PATH, "cfg/controls.ini")

# AC ini Override yamls
AC_OVERRIDE_RACE_INI_YAML_PATH = Path(CONFIG_ROOT, "defaults/simulation/race.yaml")
AC_OVERRIDE_CAMERA_MANAGER_INI_YAML_PATH = Path(
    CONFIG_ROOT, "defaults/simulation/camera_manager.yaml"
)
AC_OVERRIDE_VIDEO_INI_YAML_PATH = Path(CONFIG_ROOT, "defaults/simulation/video.yaml")
AC_OVERRIDE_ASSISTS_INI_YAML_PATH = Path(
    CONFIG_ROOT, "defaults/simulation/assists.yaml"
)
AC_OVERRIDE_GAMEPLAY_INI_YAML_PATH = Path(
    CONFIG_ROOT, "defaults/simulation/gameplay.yaml"
)
AC_OVERRIDE_CONTROLS_INI_YAML_PATH = Path(
    CONFIG_ROOT, "defaults/simulation/controls.yaml"
)


# Collection of Default Overrides
OverridePaths = namedtuple("OverridePaths", "default user override")
CONFIG_OVERRIDE_PATHS = {
    "race.ini": OverridePaths(
        DEFAULT_RACE_INI_PATH,
        AC_USER_RACE_INI_PATH,
        AC_OVERRIDE_RACE_INI_YAML_PATH,
    ),
    "camera_manager.ini": OverridePaths(
        DEFAULT_CAMERA_MANAGER_INI_PATH,
        AC_USER_CAMERA_MANAGER_INI_PATH,
        AC_OVERRIDE_CAMERA_MANAGER_INI_YAML_PATH,
    ),
    "video.ini": OverridePaths(
        DEFAULT_VIDEO_INI_PATH,
        AC_USER_VIDEO_INI_PATH,
        AC_OVERRIDE_VIDEO_INI_YAML_PATH,
    ),
    "assists.ini": OverridePaths(
        DEFAULT_ASSISTS_INI_PATH,
        AC_USER_ASSISTS_INI_PATH,
        AC_OVERRIDE_ASSISTS_INI_YAML_PATH,
    ),
    "gameplay.ini": OverridePaths(
        DEFAULT_GAMEPLAY_INI_PATH,
        AC_USER_GAMEPLAY_INI_PATH,
        AC_OVERRIDE_GAMEPLAY_INI_YAML_PATH,
    ),
    "controls.ini": OverridePaths(
        DEFAULT_CONTROLS_INI_PATH,
        AC_USER_CONTROLS_INI_PATH,
        AC_OVERRIDE_CONTROLS_INI_YAML_PATH,
    ),
}
