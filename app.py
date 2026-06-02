import os
import json
import time
import shutil
import subprocess
import urllib.parse
import requests
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

ACE_PORT = int(os.environ.get("ACE_PORT", "7860"))
ACE_URL = f"http://127.0.0.1:{ACE_PORT}"

API_KEY = os.environ.get("ACESTEP_API_KEY", "zorix-secret-key")

# 强制 GPU
os.environ["ACESTEP_DEVICE"] = "cuda"
os.environ["CUDA_VISIBLE_DEVICES"] = os.environ.get("CUDA_VISIBLE_DEVICES", "0")
os.environ["ACESTEP_OFFLOAD_TO_CPU"] = "false"
os.environ["ACESTEP_OFFLOAD_DIT_TO_CPU"] = "false"

ace_process = None


def run_cmd(cmd, timeout=10):
    try:
        r = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        return {
            "ok": r.returncode == 0,
            "code": r.returncode,
            "stdout": r.stdout[-2000:],
            "stderr": r.stderr[-2000:]
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def gpu_ok():
    r = run_cmd(["nvidia-smi"], timeout=8)
    return r.get("ok") is True


def start_ace():
    global ace_process

    if ace_process is not None and ace_process.poll() is None:
        return

    env = os.environ.copy()
    env["ACESTEP_API_HOST"] = "0.0.0.0"
    env["ACESTEP_API_PORT"] = str(ACE_PORT)
    env["ACESTEP_API_KEY"] = API_KEY
    env["ACESTEP_DEVICE"] = "cuda"
    env["ACESTEP_OFFLOAD_TO_CPU"] = "false"
    env["ACESTEP_OFFLOAD_DIT_TO_CPU"] = "false"

    ace_process = subprocess.Popen(
        [
            "uv", "run", "acestep",
            "--server-name", "0.0.0.0",
            "--port", str(ACE_PORT),
            "--enable-api",
            "--api-key", API_KEY,
            "--init_llm", "false"
        ],
        cwd="/ace-step",
        env=env
    )


def wait_ace(timeout_sec=360):
    start = time.time()

    while time.time() - start < timeout_sec:
        try:
            r = requests.get(
                f"{ACE_URL}/health",
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=5
            )
            if r.status_code < 500:
                return True
        except Exception:
            pass

        time.sleep(2)

    return False


def ace_post(path, payload, timeout=3600):
    return requests.post(
        f"{ACE_URL}{path}",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=timeout
    )


def parse_task_id(resp_json):
    data = resp_json.get("data")

    if isinstance(data, dict):
        for key in ["task_id", "taskId", "id", "job_id", "jobId"]:
            if key in data:
                return data[key]

    for key in ["task_id", "taskId", "id", "job_id", "jobId"]:
        if key in resp_json:
            return resp_json[key]

    return None


def extract_audio_path(query_json):
    data = query_json.get("data")

    if not isinstance(data, list) or not data:
        return None, query_json

    item = data[0]
    status = item.get("status")

    if status == 2:
        return None, query_json

    if status != 1:
        return None, query_json

    result = item.get("result")

    if isinstance(result, str):
        try:
            result = json.loads(result)
        except Exception:
            return None, query_json

    if isinstance(result, list) and result:
        first = result[0]
        file_url = first.get("file") or first.get("audio") or first.get("url")
    elif isinstance(result, dict):
        file_url = result.get("file") or result.get("audio") or result.get("url")
    else:
        file_url = None

    if not file_url:
        return None, query_json

    # file_url 可能是 /v1/audio?path=...
    if file_url.startswith("/v1/audio"):
        parsed = urllib.parse.urlparse(file_url)
        qs = urllib.parse.parse_qs(parsed.query)
        path = qs.get("path", [None])[0]
        return path, query_json

    # 也可能直接就是本地 path
    return file_url, query_json


@app.get("/")
def home():
    start_ace()
    return jsonify({
        "ok": True,
        "service": "Zorix ACE-Step Direct MP3",
        "ace_url": ACE_URL,
        "gpu_required": True,
        "gpu_ok": gpu_ok()
    })


@app.get("/health")
def health():
    start_ace()

    try:
        r = requests.get(
            f"{ACE_URL}/health",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=5
        )
        return jsonify({
            "ok": True,
            "gpu_ok": gpu_ok(),
            "ace_status": r.status_code,
            "ace": r.text[:1000]
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "starting": True,
            "gpu_ok": gpu_ok(),
            "error": str(e)
        })


@app.post("/generate")
def generate():
    start_ace()

    if not gpu_ok():
        return jsonify({
            "ok": False,
            "error": "GPU not available. Cloud Run must use NVIDIA L4 GPU."
        }), 500

    if not wait_ace(timeout_sec=360):
        return jsonify({
            "ok": False,
            "error": "ACE-Step API not ready"
        }), 503

    data = request.json or {}

    prompt = str(data.get("prompt", "epic cinematic orchestral music")).strip()
    lyrics = str(data.get("lyrics", "")).strip()

    duration = int(data.get("duration", 120))
    duration = max(10, min(duration, 600))

    payload = {
        "prompt": prompt,
        "lyrics": lyrics,
        "audio_duration": duration,
        "audio_format": "mp3",
        "model": data.get("model", "acestep-v15-turbo"),
        "thinking": bool(data.get("thinking", False)),
        "task_type": data.get("task_type", "text2music"),
        "vocal_language": data.get("vocal_language", "en")
    }

    # 可选参数
    for k in [
        "bpm",
        "key_scale",
        "time_signature",
        "seed",
        "timesteps",
        "guidance_scale",
        "infer_step",
        "use_format",
        "sample_mode",
        "sample_query"
    ]:
        if k in data:
            payload[k] = data[k]

    release = ace_post("/release_task", payload, timeout=3600)

    try:
        release_json = release.json()
    except Exception:
        return jsonify({
            "ok": False,
            "stage": "release_task",
            "status": release.status_code,
            "raw": release.text[:2000]
        }), 500

    if release.status_code >= 400:
        return jsonify({
            "ok": False,
            "stage": "release_task",
            "status": release.status_code,
            "ace": release_json
        }), release.status_code

    task_id = parse_task_id(release_json)

    if not task_id:
        return jsonify({
            "ok": False,
            "stage": "parse_task_id",
            "ace": release_json
        }), 500

    # 等任务完成
    last_query = None

    for _ in range(360):
        q = ace_post(
            "/query_result",
            {"task_id_list": [task_id]},
            timeout=60
        )

        try:
            qj = q.json()
        except Exception:
            last_query = {"raw": q.text[:2000], "status": q.status_code}
            time.sleep(2)
            continue

        last_query = qj
        audio_path, full_result = extract_audio_path(qj)

        if audio_path:
            # 下载 mp3
            download_url = f"{ACE_URL}/v1/audio?path={urllib.parse.quote(audio_path, safe='')}"
            audio_resp = requests.get(
                download_url,
                headers={"Authorization": f"Bearer {API_KEY}"},
                stream=True,
                timeout=600
            )

            if audio_resp.status_code >= 400:
                return jsonify({
                    "ok": False,
                    "stage": "download_audio",
                    "status": audio_resp.status_code,
                    "raw": audio_resp.text[:2000],
                    "path": audio_path
                }), 500

            out_path = f"/tmp/zorix_ace_{task_id}.mp3"

            with open(out_path, "wb") as f:
                for chunk in audio_resp.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

            return send_file(
                out_path,
                mimetype="audio/mpeg",
                as_attachment=True,
                download_name="zorix_music.mp3"
            )

        # 失败
        try:
            arr = qj.get("data", [])
            if arr and arr[0].get("status") == 2:
                return jsonify({
                    "ok": False,
                    "stage": "generation_failed",
                    "task_id": task_id,
                    "ace": qj
                }), 500
        except Exception:
            pass

        time.sleep(2)

    return jsonify({
        "ok": False,
        "error": "timeout waiting for generation",
        "task_id": task_id,
        "last_query": last_query
    }), 504


@app.post("/task")
def task():
    start_ace()
    data = request.json or {}
    r = ace_post("/query_result", data, timeout=60)
    return jsonify(r.json()), r.status_code
