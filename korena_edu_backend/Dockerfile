FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.in ./

RUN pip install --upgrade pip && \
    pip install pip-tools && \
    pip-compile requirements.in && \
    pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
