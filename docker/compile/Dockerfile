FROM debian:stretch-slim
# FROM debian:buster-slim
# newer Debian Buster does not directly support OpenJDK 8.
# It has version 11 instead, which is not supported by deck2pdf.

ENV LANG=C.UTF-8

# Copy the source code of the presentation maker into the container and
# install it as a Python package with "pip install".
COPY . /tmp/presentation-maker
# Helper script for starting the compilation.
COPY docker/compile/compile_presentation.sh /usr/local/bin/compile_presentation.sh

# apt-get packages for compiling Python
ARG PYTHON_BUILD_DEPS="build-essential libbz2-dev libc6-dev libgdbm-dev libncursesw5-dev libreadline-gplv2-dev libssl-dev libsqlite3-dev tk-dev"

# "mkdir -p /usr/share/man/man1" is needed because the java package fails
# to install otherwise.
# git is currently needed to install the rst2pdf pip package from Github.com
# because only the master branch supports Python 3. They will eventually release
# a new version officially.
# Java and JavaFX are needed for the deck2pdf tool that converts HTML files to PDFs.
# xvfb is needed to run JavaFX applications since they require a display.
# Python 3.6 or newer is needed for rst2pdf. Python 3.6 is compiled from
# the source code because Debian Stretch has only Python 3.5 available in
# the pre-built packages.

RUN mkdir -p /usr/share/man/man1 \
  && apt-get update -qqy && DEBIAN_FRONTEND=noninteractive apt-get install -qqy --no-install-recommends \
    -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" \
    apt-utils \
    ca-certificates \
    curl \
    git \
    openjdk-8-jdk-headless \
    openjfx \
    xvfb \
    xauth \
    $PYTHON_BUILD_DEPS \
  # Compile Python 3.6
  && cd /usr/local/src \
  && curl -LSs -o Python-3.6.9.tar.gz https://www.python.org/ftp/python/3.6.9/Python-3.6.9.tgz \
  && tar -xzf Python-3.6.9.tar.gz \
  && rm Python-3.6.9.tar.gz \
  && cd /usr/local/src/Python-3.6.9 \
  && ./configure \
  && make \
  && make install \
  && cd / \
  && rm -rf /usr/local/src/Python-3.6.9 \
  && pip3 install --upgrade pip wheel setuptools \
  && pip3 install --no-cache-dir --disable-pip-version-check \
    /tmp/presentation-maker \
  && rm -rf /tmp/presentation-maker \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
  && rm -rf /root/.cache \
  && apt-get purge -qqy git $PYTHON_BUILD_DEPS

# pip install from repo URL
# pip3 install --no-cache-dir --disable-pip-version-check \
# "https://github.com/Aalto-LeTech/presentation-maker/archive/0.0.1.zip" \

WORKDIR /compile
VOLUME /compile

# Java opts for deck2pdf
ENV JAVA_OPTS="-Dprism.order=sw"

ENTRYPOINT ["compile_presentation.sh"]

