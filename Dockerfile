FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV ACESTEP_API_KEY=zorix-secret-key

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip uv flask gunicorn requests

RUN git clone https://github.com/ACE-Step/ACE-Step-1.5.git /ace-step

WORKDIR /ace-step
RUN uv sync

WORKDIR /app
COPY app.py .

CMD exec gunicorn --bind :$PORT --workers 1 --timeout 3600 app:app
