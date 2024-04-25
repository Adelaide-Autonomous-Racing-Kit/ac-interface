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
	conda create -y -p $(CONDA_ENV_PATH) -c conda-forge python=3.9 
	$(CONDA_ACTIVATE) $(CONDA_ENV_PATH)

	# Install packages using pip
	pip3 install -r requirements.txt
	pip3 install -r requirements-dev.txt
	pip3 install -e .
	
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
	@pytest --workers 4 src/aci/ -m "not benchmark and not gpu" 

lint:
	@black "src/aci/" 
	@isort --settings-file=linters/isort.ini "src/aci/"
	@flake8 --config=linters/flake8.ini "src/aci/"
	@echo "all done"

jupyter:
	@bash python3 -m jupyterlab --ip 0.0.0.0 --port 8889
