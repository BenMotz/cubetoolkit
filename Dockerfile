FROM debian

MAINTAINER Ben Motz <ben@cubecinema.com>

RUN apt-get update && \
  apt-get install -y \
  python \
  python-virtualenv \
  python-imaging \
  python-mysqldb \
  apache2 \
  libapache2-mod-wsgi \
  vim-tiny \
  && mkdir /site

WORKDIR "/site"

COPY requirements_python_only.txt "/site/"

RUN virtualenv venv --system-site-packages &&\
    . venv/bin/activate &&\
    pip install -r requirements_python_only.txt

COPY "." "/site/"

RUN ln -s \
       /site/serverconfig/apache-sites-available/toolkit-docker.conf \
       /etc/apache2/sites-enabled/toolkit.conf \
    && \
    ln -s \
       /site/toolkit/docker_settings.py /site/toolkit/settings.py \
    && \
    rm /etc/apache2/sites-enabled/000-default.conf \
    && \
    install -d /var/log/cubetoolkit -g www-data -m 0770 \
    && \
    /site/venv/bin/python manage.py collectstatic \
       --noinput --settings=toolkit.devserver_settings

ENV DB_NAME=toolkit \
    DB_USER=toolkit \
    DB_HOST=localhost \
    DB_PORT=3306 \
    DB_PASSWORD=password \
    SECRET_KEY=""

VOLUME ["/site/media"]

EXPOSE 80

CMD ["/usr/sbin/apache2ctl", "-DFOREGROUND"]
