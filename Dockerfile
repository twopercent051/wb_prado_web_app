FROM python:3.10-buster

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app
RUN pip install -r /usr/src/app/requirements.txt
COPY . /usr/src/app