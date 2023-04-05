#!/bin/sh

pre-commit run --config .pre-push-config.yaml --all-files --hook-stage push
