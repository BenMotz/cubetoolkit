#!/usr/bin/env bash
# Trivial script to create virtualenv and do initial package install for dev
# or deployment
# (Requires system pip to be available)

VENV_PATH=./venv
VIRTUALENV_OPTIONS=""
# Requirements to run the django app:
REQUIREMENTS_FILE=requirements_python_only.txt
# Requirements to develop/test/deploy:
REQUIREMENTS_DEV=requirements_development.txt

set -e

VIRTUALENV_MAJOR_VERSION=$(virtualenv --version | cut --delimiter=. -f 1)
VIRTUALENV_MINOR_VERSION=$(virtualenv --version | cut --delimiter=. -f 2)

# Virtualenv changed their interface in a breaking way at v1.7: (idiots)
if [ $VIRTUALENV_MAJOR_VERSION -eq 1 ] && [ $VIRTUALENV_MINOR_VERSION -lt 7 ] ; then
    VIRTUALENV_OPTIONS=${VIRTUALENV_OPTIONS}
else
    VIRTUALENV_OPTIONS="${VIRTUALENV_OPTIONS} --system-site-packages"
fi

virtualenv $VENV_PATH $VIRTUALENV_OPTIONS

source $VENV_PATH/bin/activate

pip install --upgrade pip
pip install --requirement $REQUIREMENTS_FILE
pip install --requirement $REQUIREMENTS_DEV
