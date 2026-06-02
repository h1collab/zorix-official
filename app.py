import os
import subprocess
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

ACE_PORT = 7860
ACE_URL = f"http://127.0.0.1:{ACE_PORT}"
API_KEY = os.environ.get("ACESTEP_API_KEY", "zorix-secret-key")

ace_process = None


def start_ace():
    global ace_process

    if ace_process is not None and ace_process.poll() is None:
        return

    ace_process = subprocess.Popen(
        [
            "uv", "run", "acestep",
            "--server-name", "0.0.0.0",
            "--port", str(ACE_PORT),
            "--enable-api",
            "--api-key", API_KEY,
            "--init_llm", "false"
        ],
        cwd="/ace-step"
    )


@app.get("/")
def home():
    start_ace()
    return jsonify({
        "ok": True,
        "service": "Zorix ACE-Step Gateway",
        "ace_url": ACE_URL
    })


@app.get("/health")
def health():
    start_ace()
    try:
        r = requests.get(ACE_URL, timeout=5)
        return jsonify({
            "ok": True,
            "ace_status": r.status_code
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "starting": True,
            "error": str(e)
        })


@app.post("/generate")
def generate():
    start_ace()

    data = request.json or {}

    for _ in range(120):
        try:
            requests.get(ACE_URL, timeout=3)
            break
        except Exception:
            time.sleep(2)

    return jsonify({
        "ok": False,
        "message": "ACE-Step server started, but API endpoint must be confirmed from logs/routes.",
        "input": data
    })
