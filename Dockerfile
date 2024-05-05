# Isso production Dockerfile

ARG PY_VERSION=3.10

# =======================================================
# First stage: Build Javascript client parts using NodeJS
# =======================================================

FROM docker.io/node:current-alpine AS isso-js
WORKDIR /src/

# make is not installed by default on alpine
RUN apk add --no-cache make

# Only copy necessities, to not trigger re-builds unnecessarily
COPY ["Makefile", "package.json", "package-lock.json", "./"]

# Disable nagware and save some time skipping "security" "audits"
RUN echo -e "audit=false\nfund=false" > /root/.npmrc

# Install node packages from npm
RUN make init

# Copy Javascript source code
COPY ["isso/js/", "./isso/js/"]

# Run webpack to generate minified Javascript
RUN make js


# ==================================================
# Second stage: Create production-ready Isso package
# ==================================================

FROM docker.io/python:${PY_VERSION}-alpine AS isso-builder
WORKDIR /isso/

# Install cffi dependencies since they're not present on alpine by default
# (required by cffi which in turn is required by misaka)
RUN apk add --no-cache gcc libffi-dev libc-dev

# Use pip from /usr/local/lib to install virtualenv from PyPI
# (Do not use the alpine py3-virtualenv package which would be stuck on the
#  Python version from the alpine repos (3.9 as of May 2024), otherwise there
#  would be a mismatch between PY_VERSION and the virtualenv used)
RUN pip install virtualenv

# # Set up virtualenv
RUN virtualenv --download /isso \
 && . /isso/bin/activate \
 && pip install --no-cache-dir --upgrade pip gunicorn cffi

# Install Isso's python dependencies via pip in a separate step before copying
# over client files, so that changing Isso js/python source code will not
# trigger a re-installation of all pip packages from scratch
COPY ["setup.py", "setup.cfg", "README.md", "LICENSE", "./"]
RUN --mount=type=cache,target=/root/.cache \
  . /isso/bin/activate \
 && pip install -e .

# Then copy over files
# SRC "isso/" is treated as "isso/*" by docker, so copy to subdir explicitly
COPY ["./isso/", "/isso/isso/"]
COPY ["./contrib/", "./contrib/"]

# Copy over generated Javascript client files
COPY --from=isso-js /src/isso/js/ ./isso/js

# Build and install Isso package (pip dependencies cached from previous step)
RUN --mount=type=cache,target=/root/.cache \
 . /isso/bin/activate \
 && pip install -e . --no-deps


# =====================
# Third stage: Run Isso
# =====================

FROM docker.io/python:${PY_VERSION}-alpine AS isso
WORKDIR /isso/
COPY --from=isso-builder /isso/ .

LABEL org.opencontainers.image.source=https://github.com/isso-comments/isso
LABEL org.opencontainers.image.description="Isso – a commenting server similar to Disqus"
LABEL org.opencontainers.image.licenses=MIT

# Clean up
RUN rm -rf /var/apk/cache/* /tmp/* /var/tmp/*

# Setup permissions for volume mounts
RUN mkdir /db /config && chmod 1777 /db /config

# Configuration
VOLUME /db /config
EXPOSE 8080
ENV ISSO_SETTINGS /config/isso.cfg

# Run Isso via gunicorn WSGI server
ENTRYPOINT ["/isso/bin/gunicorn", "-b", "0.0.0.0:8080", "-w", "4", "--preload", "--worker-tmp-dir", "/dev/shm"]
CMD ["isso.run"]

# Example of use:
#
# Build:
# $ docker build -t isso .
#
# Run:
# $ mkdir -p config/ db/
# $ cp contrib/isso.sample.cfg config/isso.cfg
# Set 'dbpath' to '/db/comments.db' and adjust 'host'
# $ docker run -d --rm --name isso -p 127.0.0.1:8080:8080 -v $PWD/config:/config -v $PWD/db:/db isso:latest
