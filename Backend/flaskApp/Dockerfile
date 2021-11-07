FROM ubuntu:18.04
RUN apt update
# Install everything we'd need in a build environment within Docker
RUN apt install \
    wget \
    git \
    build-essential \
    curl \
    autoconf \
    automake \
    libtool \
    pkg-config \
    apt-transport-https \
    ppa-purge \
    zsh \
    screen \
    byobu \
    parallel \
    iperf3 \
    iotop \
    atop \
    nethogs \
    htop \
    software-properties-common \
    tesseract-ocr \
    libtesseract-dev \
    -y
################################################################################
###### Everything above this line can be part of a ubuntu-build base image #####
################################################################################
# Install Dependencies for the software we wish to compile
RUN apt install \
    libicu-dev \
    libpango1.0-dev \
    libcairo2-dev \
    libleptonica-dev \
    -y

RUN apt-get update \
   && apt-get install -y python3-pip python3-dev \
   && cd /usr/local/bin \
   && ln -s /usr/bin/python3 python \
   && pip3 install --upgrade pip \
   && apt-get -y install sudo \
   && apt-get clean \
   && apt-get autoremove

WORKDIR /app

ADD requirements.txt ./

RUN pip3 install -r requirements.txt

ADD app ./

ENV FLASK_APP=app
ENV FLASK_DEBUG=1
EXPOSE 5000 5000
CMD gunicorn -w 2 --threads 2 app:app --bind 0.0.0.0:5000 --backlog 1024 --timeout 120