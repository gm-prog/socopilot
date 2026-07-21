FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt

RUN pip install --default-timeout=200 --retries 10 --no-cache-dir -r requirements.txt

COPY backend/ /app/
