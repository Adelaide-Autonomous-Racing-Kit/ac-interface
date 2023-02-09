.ONESHELL:
SHELL = /bin/zsh
CONDA_ENV_PATH=./envs
CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate

build:
ifneq ($(wildcard $(CONDA_ENV_PATH)),)
	@echo "Environment $(CONDA_ENV_PATH) already exists, do you want to delete it and create a new one? [y/n]"
	@read ans; \
	if [ $$ans = 'y' ]; then \
		conda env remove -p $(CONDA_ENV_PATH); \
	fi
endif
	conda create -y -p $(CONDA_ENV_PATH) opencv numpy av pyyaml python-xlib matplotlib \
		black flake8-black flake8 isort loguru pytest pytest-benchmark pytest-parallel \
		coverage pyautogui -c conda-forge
	$(CONDA_ACTIVATE) $(CONDA_ENV_PATH)
	pip install -e .
	pip install git+https://github.com/wyatthuckaby/python-uinput.git
	pip install git+https://github.com/lilohuang/PyTurboJPEG.git

run:
	echo $(CONDA_ENV_PATH)
	source activate $(CONDA_ENV_PATH)
