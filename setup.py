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
        "git+https://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@github.com/Adelaide-Autonomous-Racing-Challenge/ac-extras.git"
    ],
    package_data={"aci": ["**/*.yaml"]},
)
