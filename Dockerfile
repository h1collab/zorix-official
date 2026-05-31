FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV MODEL_NAME=facebook/musicgen-small
ENV DURATION=10

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD exec gunicorn --bind :$PORT --timeout 600 --workers 1 app:app
