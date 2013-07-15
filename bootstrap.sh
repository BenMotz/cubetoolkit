#!/usr/bin/env bash
# Trivial script to create virtualenv and do initial package install for dev
# ore deployment
# (Requires system pip to be available)
VENV_PATH=./venv
# Requirements to run the django app:
REQUIREMENTS_FILE=requirements_python_only.txt
# Requirements to develop/test/deploy:
REQUIREMENTS_DEV=requirements_development.txt

set -e

virtualenv $VENV_PATH --system-site-packages
source $VENV_PATH/bin/activate
pip install --requirement $REQUIREMENTS_FILE
pip install --requirement $REQUIREMENTS_DEV
