FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV SERVER_NAME=0.0.0.0
ENV ACESTEP_INIT_LLM=false
ENV ACESTEP_DOWNLOAD_SOURCE=huggingface
ENV ACESTEP_API_KEY=zorix-secret-key

RUN apt-get update && apt-get install -y \
    python3.11 python3.11-venv python3-pip git curl ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip3 install --upgrade pip uv

RUN git clone https://github.com/ACE-Step/ACE-Step-1.5.git .

RUN uv sync

CMD uv run acestep \
  --server-name 0.0.0.0 \
  --port ${PORT} \
  --enable-api \
  --api-key ${ACESTEP_API_KEY} \
  --init_llm false
