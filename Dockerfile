# First, compile JS stuff
FROM node:dubnium-buster
WORKDIR /src/
COPY . .
RUN npm install -g requirejs uglify-js jade bower \
 && make init js

# Second, create virtualenv
FROM python:3.8-buster
WORKDIR /src/
COPY --from=0 /src .
RUN python3 -m venv /isso \
 && . /isso/bin/activate \
 && pip3 install --no-cache-dir --upgrade pip \
 && pip3 install --no-cache-dir gunicorn cffi flask \
 && python setup.py install \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Third, create final repository
FROM python:3.8-slim-buster
WORKDIR /isso/
COPY --from=1 /isso .

# Configuration
VOLUME /db /config
EXPOSE 8080
ENV ISSO_SETTINGS /config/isso.cfg
CMD ["/isso/bin/gunicorn", "-b", "0.0.0.0:8080", "-w", "4", "--preload", "isso.run", "--worker-tmp-dir", "/dev/shm"]

# Example of use:
#
# docker build -t isso .
# docker run -it --rm -v /opt/isso:/config -v /opt/isso:/db -v $PWD:$PWD isso /isso/bin/isso -c \$ISSO_SETTINGS import disqus.xml
# docker run -d --rm --name isso -p 8080:8080 -v /opt/isso:/config -v /opt/isso:/db isso
