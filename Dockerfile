# syntax=docker/dockerfile:1

FROM python:3.10.9-buster

#WORKDIR /app

COPY . .
RUN pip3 install -r requirements.txt
WORKDIR src/

CMD [ "python3", "server.py"]