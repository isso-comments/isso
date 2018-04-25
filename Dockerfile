# First, compile JS stuff
FROM node
WORKDIR /src/
COPY . .
RUN npm install -g requirejs uglify-js jade bower
RUN make init js

# Second, create virtualenv
FROM python:3-stretch
WORKDIR /src/
COPY --from=0 /src .
RUN apt-get -qqy update && apt-get -qqy install python3-dev sqlite3
RUN python3 -m venv /isso \
 && . /isso/bin/activate \
 && python setup.py install \
 && pip install gunicorn

# Third, create final repository
FROM python:3-slim-stretch
WORKDIR /isso/
COPY --from=1 /isso .

# Configuration
VOLUME /db /config
EXPOSE 8080
ENV ISSO_SETTINGS /config/isso.cfg
CMD ["/isso/bin/gunicorn", "-b", "0.0.0.0:8080", "-w", "4", "--preload", "isso.run"]

# Example of use:
#
# docker build -t isso .
# docker run -it --rm -v /opt/isso:/config -v /opt/isso:/db -v $PWD:$PWD isso /isso/bin/isso -c \$ISSO_SETTINGS import disqus.xml
# docker run -d --rm --name isso -p 8080:8080 -v /opt/isso:/config -v /opt/isso:/db isso
