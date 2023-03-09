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
	conda create -y -p $(CONDA_ENV_PATH) -c conda-forge opencv numpy av pyyaml matplotlib pillow \
		black flake8-black flake8 isort loguru pytest pytest-parallel pytest-benchmark coverage \
		pyautogui python-xlib loguru yaml
	$(CONDA_ACTIVATE) $(CONDA_ENV_PATH)
	pip install -e .
	pip install git+https://github.com/wyatthuckaby/python-uinput.git
	pip install git+https://github.com/lilohuang/PyTurboJPEG.git
	pip install python-uinput

run:
	@echo $(CONDA_ENV_PATH)
	@source activate $(CONDA_ENV_PATH)

test:
	@echo "Starting all non gpu related tests"
	# --benchmark-compare 
	@pytest --benchmark-sort --benchmark-autosave --workers 2 src/ -m "not benchmark and not gpu" 

lint:
	@black "src/" 
	@isort --settings-file=linters/isort.ini "src/"
	@flake8 --config=linters/flake8.ini "src/"
	@echo "all done"

jupyter:
	@bash python3 -m jupyterlab --ip 0.0.0.0 --port 8889