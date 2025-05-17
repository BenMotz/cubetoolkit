#!/bin/bash
set -eu

export REDIS_URL=${REDIS_URL:-redis://redis:6379/0}

COMMAND=$1

redis_suffix=${REDIS_URL#redis://}
redis_host_port=${redis_suffix%%/*}

echo "Running as: $(id)"

if [[ -v DB_HOST && -v DB_PORT && -n $DB_HOST && -n $DB_PORT ]] ; then
  if ! wait-for-it $DB_HOST:$DB_PORT --timeout=360 ; then
    echo "Database host not available"
    exit 3
  fi
elif ! [[ -S /var/run/mysqld/mysqld.sock ]] ; then
  echo "Database socket not available"
  exit 3
fi

if [[ ${NO_REDIS:-false} != "true" && -n $redis_host_port ]] && ! wait-for-it $redis_host_port --timeout=360 ; then
  echo "Redis not available"
  exit 4
fi

case "$COMMAND" in
    gunicorn)
        echo "Running database migrations"
        /venv/bin/python3 /site/manage.py migrate
        exec /venv/bin/gunicorn wsgi --bind 0.0.0.0:8000 --chdir /site
        ;;
    *)
        echo "Unknown option; expected gunicorn"
        exit 5
        ;;
esac
