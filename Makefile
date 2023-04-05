.ONESHELL:
SHELL = /bin/zsh
CONDA_ENV_PATH=./envs
CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate

build: setup-conda setup-pre-push
	@echo "Finished building environment"

setup-conda:
ifneq ($(wildcard $(CONDA_ENV_PATH)),)
	@echo "Environment $(CONDA_ENV_PATH) already exists, do you want to delete it and create a new one? [y/n]"
	@read ans; \
	if [ $$ans = 'y' ]; then \
		conda env remove -p $(CONDA_ENV_PATH); \
	fi
endif
	# Ensure docker compose is installed
	docker compose version || { echo "Please install docker compose first: https://docs.docker.com/desktop/install/ubuntu/"; exit 1; }

	# Create conda environment and install packages
	conda create -y -p $(CONDA_ENV_PATH) -c conda-forge opencv numpy av pyyaml matplotlib pillow python=3.9 \
		black flake8-black flake8 isort loguru pytest pytest-parallel py pytest-benchmark coverage \
		pyautogui python-xlib loguru yaml tqdm halo
	$(CONDA_ACTIVATE) $(CONDA_ENV_PATH)

	# Install packages using pip
	pip3 install -e .
	pip3 install \
		git+https://github.com/wyatthuckaby/python-uinput.git \
		git+https://github.com/lilohuang/PyTurboJPEG.git \
		python-uinput \
		"psycopg[binary]" \
		pre-commit

	# Install PyTorch and optional packages if desired
	@echo "Do you want to install PyTorch and optional packages? [y/n]"
	@read ans; \
	if [ $$ans = 'y' ]; then \
		conda install -y pytorch torchvision torchaudio pytorch-cuda=11.7 -c pytorch -c nvidia; \
		git clone http://github.com/XDynames/modular-encoder-decoders-segmentation.git segmentors && \
			pip3 install -e segmentors; \
		pip3 install embree==2.17.7 pyembree prettytable; \
	fi

	# Start the database
	docker compose up -d

setup-pre-push:
	@echo "Setting up pre-push hook..."
	@cp pre_push.sh .git/hooks/pre-push
	@chmod +x .git/hooks/pre-push
	@echo "Done!"

run:
	@echo $(CONDA_ENV_PATH)
	@source activate $(CONDA_ENV_PATH)

test:
	@echo "Starting all non gpu related tests"
	@pytest --workers 4 src/ -m "not benchmark and not gpu" 

lint:
	@black "src/" 
	@isort --settings-file=linters/isort.ini "src/"
	@flake8 --config=linters/flake8.ini "src/"
	@echo "all done"

jupyter:
	@bash python3 -m jupyterlab --ip 0.0.0.0 --port 8889
