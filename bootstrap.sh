#!/usr/bin/env bash
# Trivial script to create virtualenv and do initial package install for dev
# or deployment
# (Requires system pip to be available)
set -e

VENV_PATH=./venv
VIRTUALENV_OPTIONS="--system-site-packages"
# Requirements to run the django app:
REQUIREMENTS_FILE=requirements_python_only.txt
# Requirements to develop/test/deploy:
REQUIREMENTS_DEV=requirements_development.txt

virtualenv $VENV_PATH $VIRTUALENV_OPTIONS

source $VENV_PATH/bin/activate

pip install --upgrade pip
pip install --requirement $REQUIREMENTS_FILE
pip install --requirement $REQUIREMENTS_DEV
