import os
import uuid
import torch
import torchaudio
from flask import Flask, request, jsonify, send_from_directory
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write

app = Flask(__name__)

OUT_DIR = "/tmp/music"
os.makedirs(OUT_DIR, exist_ok=True)

MODEL_NAME = os.environ.get("MODEL_NAME", "facebook/musicgen-small")
API_KEY = os.environ.get("ZORIX_MUSIC_API_KEY", "")

model = MusicGen.get_pretrained(MODEL_NAME)
model.set_generation_params(duration=int(os.environ.get("DURATION", "10")))

@app.get("/")
def home():
    return "Zorix MusicGen running"

@app.post("/generate")
def generate():
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "unauthorized"}), 401

    data = request.json or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "missing prompt"}), 400

    duration = int(data.get("duration", os.environ.get("DURATION", "10")))
    model.set_generation_params(duration=min(duration, 30))

    wav = model.generate([prompt])[0].cpu()
    name = f"{uuid.uuid4().hex}.wav"
    path_no_ext = os.path.join(OUT_DIR, name[:-4])

    audio_write(
        path_no_ext,
        wav,
        model.sample_rate,
        strategy="loudness",
        loudness_compressor=True
    )

    return jsonify({
        "prompt": prompt,
        "file": name,
        "url": f"/files/{name}"
    })

@app.get("/files/<filename>")
def files(filename):
    return send_from_directory(OUT_DIR, filename, as_attachment=True)
