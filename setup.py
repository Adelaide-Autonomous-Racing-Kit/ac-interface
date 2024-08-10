from setuptools import setup, find_packages

setup(
    name="assetto-corsa-interface",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "opencv-python",
        "numpy",
        "av",
        "pyyaml",
        "pillow",
        "loguru",
        "pyautogui",
        "python-xlib",
        "loguru",
        "tqdm",
        "halo",
        "git+https://github.com/wyatthuckaby/python-uinput.git",
        "git+https://github.com/lilohuang/PyTurboJPEG.git",
        "python-uinput",
        "psycopg[binary]",
        "PyWinCtl",
    ],
)
