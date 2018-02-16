FROM python:3.6
ARG ISSO_VER=0.10.6

RUN apt-get update && apt-get install -y python-dev \
    libffi-dev \
    sqlite3 \
    openssl \
 && pip install --no-cache "isso==${ISSO_VER}" \
 && rm -rf /tmp/*

EXPOSE 8081

VOLUME /db /config

CMD ["isso", "-c", "/config/isso.conf", "run"]
