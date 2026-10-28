#!/bin/bash

# Builds the docker image and use it to run the test suite.
# (You should be able to pass a list of tests through)
#
set -eu

IMAGE_TAG=${IMAGE_TAG:-dev}

cd "$(dirname "$0")"

docker build --build-arg ENV_NAME=dev --build-arg TOOLKIT_UID="$(id -u)" --tag toolkit:$IMAGE_TAG .

# The image only has the base requirements, so the dev/test requirements need
# to be installed into the container:
docker run --rm --user root --entrypoint bash toolkit:$IMAGE_TAG -c \
  '/venv/bin/pip install --quiet -r requirements/dev.txt && ./runtests_container.sh "$@"' -- "$@"
