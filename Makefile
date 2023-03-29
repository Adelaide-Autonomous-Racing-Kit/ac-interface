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
	# docker compose needed for deephaven
	docker compose version || { echo "Please install docker compose first: https://docs.docker.com/desktop/install/ubuntu/"; exit 1; }
	conda create -y -p $(CONDA_ENV_PATH) -c conda-forge opencv numpy av pyyaml matplotlib pillow \
		black flake8-black flake8 isort loguru pytest pytest-parallel pytest-benchmark coverage \
		pyautogui python-xlib loguru yaml tqdm halo
	$(CONDA_ACTIVATE) $(CONDA_ENV_PATH)
	pip3 install -e .
	pip3 install git+https://github.com/wyatthuckaby/python-uinput.git
	pip3 install git+https://github.com/lilohuang/PyTurboJPEG.git
	pip3 install python-uinput
	git clone https://github.com/jmao-denver/deephaven-core.git deephaven-clone && \
		cd deephaven-clone/py/client && \
		git checkout 3580-pyclient-inputtable && \
		pip3 install -r requirements-dev.txt && \
		python3 setup.py bdist_wheel && \
		pip3 install dist/pydeephaven-0.23.0-py3-none-any.whl && \
		cd ../../../ && rm -rf deephaven-clone 
	# start deephaven server
	docker compose up -d

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
