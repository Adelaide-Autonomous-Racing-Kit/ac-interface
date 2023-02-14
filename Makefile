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
	conda create -y -p $(CONDA_ENV_PATH) -c conda-forge opencv numpy av pyyaml matplotlib \
		black flake8-black flake8 isort loguru pytest pytest-parallel pytest-benchmark coverage \
		pyautogui python-xlib  
	$(CONDA_ACTIVATE) $(CONDA_ENV_PATH)
	pip install -e .
	pip install git+https://github.com/wyatthuckaby/python-uinput.git
	pip install git+https://github.com/lilohuang/PyTurboJPEG.git

run:
	@echo $(CONDA_ENV_PATH)
	@source activate $(CONDA_ENV_PATH)

test:
	@echo "Starting all non gpu related tests"
	# --benchmark-compare 
	@pytest --benchmark-sort --benchmark-autosave --workers 2 src/ -m "not benchmark and not gpu" 

lint:
	black src/
    isort src/ --settings-file=linters/isort.ini
    flake8 src/ --config=linters/flake8.ini