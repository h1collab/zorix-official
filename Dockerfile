FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV MODEL_NAME=stabilityai/sdxl-turbo

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir --timeout 1000 -r requirements.txt

RUN python3 -c "import torch; print('TORCH OK', torch.__version__)"

COPY app.py .

CMD exec gunicorn --bind :$PORT --workers 1 --timeout 600 app:app
