#!/usr/bin/env bash
# Trivial script to create virtualenv and do initial package install for dev
# or deployment
# (Requires system pip to be available)
set -e

VENV_PATH=./venv
VIRTUALENV_OPTIONS="--system-site-packages"
# Requirements to run the django app:
REQUIREMENTS_FILE=requirements.txt
# Requirements to develop/test/deploy:
REQUIREMENTS_DEV=requirements_development.txt
# Default to python 2:
PYTHON_INTERPRETER=/usr/bin/python

usage() {
    echo "Usage: $0 [-h] [-3]"
    echo "Use -3 to setup for python 3"
    exit 0;
}

while getopts "h3" opt; do
    case "${opt}" in
        h)
            usage
            ;;
        3)
            PYTHON_INTERPRETER=/usr/bin/python3
            ;;
        *)
            usage
            ;;
    esac
done

if [[ ! -e ${PYTHON_INTERPRETER} && -x ${PYTHON_INTERPRETER} ]]; then
    echo "Python executable '${PYTHON_INTERPRETER}' not found"
    exit 1
fi

if [[ -e ${VENV_PATH} ]]; then
    echo "Virtualenv '${VENV_PATH}' already exists"
    exit 1
fi

virtualenv -p ${PYTHON_INTERPRETER} $VENV_PATH $VIRTUALENV_OPTIONS

source $VENV_PATH/bin/activate

pip install --upgrade pip
pip install --requirement $REQUIREMENTS_FILE
pip install --requirement $REQUIREMENTS_DEV
