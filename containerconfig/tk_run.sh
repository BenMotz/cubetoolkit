#!/bin/bash
set -eu

export DB_HOST=${DB_HOST:-mariadb}
export DB_PORT=${DB_PORT:-3306}
export REDIS_URL=${REDIS_URL:-redis://redis:6379/0}

COMMAND=$1

redis_suffix=${REDIS_URL#redis://}
redis_host_port=${redis_suffix%%/*}

 if [[ -z $SECRET_KEY ]] ; then
   echo SECRET_KEY environment variable not defined
   exit 2
 fi

if ! wait-for-it $DB_HOST:$DB_PORT --timeout=360 ; then
  echo "Database not available"
  exit 3
fi

if ! wait-for-it $redis_host_port --timeout=360 ; then
  echo "Redis not available"
  exit 4
fi

case "$COMMAND" in
    celery)
        exec /usr/local/bin/celery --app=toolkit worker --loglevel=INFO --concurrency=1
        ;;
    gunicorn)
        echo "Running database migrations"
        /site/manage.py migrate
        exec /usr/local/bin/gunicorn wsgi --bind 0.0.0.0:8000 --chdir /site
        ;;
    *)
        echo "Unknown option; expected gunicorn or celery"
        exit 5
        ;;
esac
