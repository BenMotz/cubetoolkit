FROM debian:bullseye AS base

RUN DEBIAN_FRONTEND=noninteractive apt-get update \
  && apt-get install --yes --no-install-recommends \
  python3 \
  python3-pip \
  vim-tiny \
  libmariadb3 \
  libmagic1 \
  wait-for-it \
  && DEBIAN_FRONTEND=noninteractive apt-get clean \
  && rm -rf /var/lib/apt/lists/*

## Use an intermediate image to build dependency wheels:
FROM base AS build

RUN DEBIAN_FRONTEND=noninteractive apt-get update \
  && apt-get install --yes --no-install-recommends \
  build-essential \
  libmariadb-dev \
  libpython3-dev

WORKDIR "/build"

COPY ./requirements ./requirements/

RUN pip install --upgrade pip \
    && mkdir --parents /build/wheels/ \
    && pip wheel --wheel-dir /build/wheels/ -r /build/requirements/docker.txt

## Deployment image
FROM base AS run

COPY --from=build /build/wheels /wheels/

WORKDIR "/site"

RUN adduser --no-create-home --disabled-login --gecos x toolkit \
    && pip install --upgrade pip \
    && pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
    && rm -rf /wheels/

COPY --chown=toolkit:toolkit . /site/

ENV DB_NAME=toolkit \
    DB_USER=toolkit \
    DB_HOST=localhost \
    DB_PORT=3306 \
    DB_PASSWORD=devserver_db_password \
    SECRET_KEY=""

RUN ln -s /site/containerconfig/tk_run.sh /usr/local/bin/tk_run \
     && ln -s /site/toolkit/docker_settings.py /site/toolkit/settings.py \
     && SECRET_KEY="X" /site/manage.py collectstatic --noinput --settings=toolkit.docker_settings \
     && install -D --owner=toolkit --group=toolkit --directory /site/media/diary \
     && install -D --owner=toolkit --group=toolkit --directory /site/media/documents \
     && install -D --owner=toolkit --group=toolkit --directory /site/media/images \
     && install -D --owner=toolkit --group=toolkit --directory /site/media/printedprogramme \
     && install -D --owner=toolkit --group=toolkit --directory /site/media/volunteers

USER toolkit:toolkit

VOLUME ["/site/media"]
VOLUME ["/log/"]

EXPOSE 8000
