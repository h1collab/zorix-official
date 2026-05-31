import os, uuid
import torch
import scipy.io.wavfile
from flask import Flask, request, jsonify, send_from_directory
from transformers import AutoProcessor, MusicgenForConditionalGeneration

app = Flask(__name__)

OUT_DIR = "/tmp/music"
os.makedirs(OUT_DIR, exist_ok=True)

MODEL_NAME = os.environ.get("MODEL_NAME", "facebook/musicgen-small")
API_KEY = os.environ.get("ZORIX_MUSIC_API_KEY", "")

device = "cuda" if torch.cuda.is_available() else "cpu"

processor = AutoProcessor.from_pretrained(MODEL_NAME)
model = MusicgenForConditionalGeneration.from_pretrained(MODEL_NAME).to(device)

@app.get("/")
def home():
    return f"Zorix MusicGen running on {device}"

@app.post("/generate")
def generate():
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "unauthorized"}), 401

    data = request.json or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "missing prompt"}), 400

    max_new_tokens = int(data.get("max_new_tokens", 256))

    inputs = processor(
        text=[prompt],
        padding=True,
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        audio_values = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens
        )

    audio = audio_values[0, 0].detach().cpu().numpy()
    sampling_rate = model.config.audio_encoder.sampling_rate

    name = f"{uuid.uuid4().hex}.wav"
    path = os.path.join(OUT_DIR, name)

    scipy.io.wavfile.write(path, rate=sampling_rate, data=audio)

    return jsonify({
        "prompt": prompt,
        "device": device,
        "file": name,
        "url": f"/files/{name}"
    })

@app.get("/files/<filename>")
def files(filename):
    return send_from_directory(OUT_DIR, filename, as_attachment=True)
