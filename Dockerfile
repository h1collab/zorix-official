FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir --timeout 1000 -r requirements.txt

COPY . .

CMD exec gunicorn --bind :$PORT --workers 1 --timeout 600 app:app
