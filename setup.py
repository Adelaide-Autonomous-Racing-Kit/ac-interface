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
        "python-uinput",
        "PyTurboJPEG",
        "python-uinput",
        "psycopg",
        "PyWinCtl",
    ],
    package_data={"aci": ["**/*.yaml", "**/*.sh"]},
)
