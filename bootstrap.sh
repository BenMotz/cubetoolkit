#!/usr/bin/env bash
# Trivial script to create virtualenv and do initial package install
# (Requires system pip to be available)
VENV_PATH=./venv
REQUIREMENTS_FILE=requirements.txt

virtualenv $VENV_PATH --system-site-packages
source $VENV_PATH/bin/activate
pip install --requirement $REQUIREMENTS_FILE
