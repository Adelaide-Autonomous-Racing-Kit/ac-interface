CONDA_ENV_PATH=./envs

build:
ifneq ($(wildcard $(CONDA_ENV_PATH)),)
	@echo "Environment $(CONDA_ENV_PATH) already exists, do you want to delete it and create a new one? [y/n]"
	@read ans; \
	if [ $$ans = 'y' ]; then \
		conda env remove -p $(CONDA_ENV_PATH); \
	fi
endif
	conda create -y -p $(CONDA_ENV_PATH) opencv numpy pytest -c conda-forge 

run:
	echo $(CONDA_ENV_PATH)
	source activate $(CONDA_ENV_PATH)
