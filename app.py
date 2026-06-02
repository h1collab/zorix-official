import os, subprocess, time, requests
from flask import Flask, request, jsonify

app = Flask(__name__)

ACE_PORT = 7860
ACE_URL = f"http://127.0.0.1:{ACE_PORT}"
API_KEY = os.environ.get("ACESTEP_API_KEY", "zorix-secret-key")
ace_process = None

def start_ace():
    global ace_process
    if ace_process and ace_process.poll() is None:
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

def wait_ace():
    for _ in range(180):
        try:
            r = requests.get(f"{ACE_URL}/", timeout=3)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False

@app.get("/")
def home():
    start_ace()
    return jsonify({"ok": True, "service": "Zorix ACE-Step Gateway", "ace_url": ACE_URL})

@app.get("/health")
def health():
    start_ace()
    try:
        r = requests.get(f"{ACE_URL}/", timeout=5)
        return jsonify({"ok": True, "ace_status": r.status_code})
    except Exception as e:
        return jsonify({"ok": False, "starting": True, "error": str(e)})

@app.post("/generate")
def generate():
    start_ace()
    if not wait_ace():
        return jsonify({"ok": False, "error": "ACE-Step not ready"}), 503

    data = request.json or {}
    payload = {
        "prompt": data.get("prompt", "epic cinematic orchestral music"),
        "duration": int(data.get("duration", 120))
    }

    r = requests.post(
        f"{ACE_URL}/v1/music/generate",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json=payload,
        timeout=3600
    )

    return jsonify(r.json()), r.status_code

@app.get("/job/<job_id>")
def job(job_id):
    start_ace()
    r = requests.get(
        f"{ACE_URL}/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=60
    )
    return jsonify(r.json()), r.status_code
