FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install uv

WORKDIR /app

COPY app.py .

RUN git clone https://github.com/ACE-Step/ACE-Step-1.5 /ace-step

WORKDIR /ace-step

RUN uv sync

WORKDIR /app

CMD python app.py
