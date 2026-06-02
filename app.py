import os
import uuid
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

processor = None
model = None


def load_model():
    global processor, model

    if processor is None:
        processor = AutoProcessor.from_pretrained(MODEL_NAME)

    if model is None:
        model = MusicgenForConditionalGeneration.from_pretrained(MODEL_NAME)
        model.to(device)
        model.eval()

    return processor, model


@app.get("/")
def home():
    return f"Zorix MusicGen Small ready. Device: {device}"


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "model": MODEL_NAME,
        "device": device,
        "loaded": model is not None
    })


@app.post("/generate")
def generate():
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "unauthorized"}), 401

    data = request.json or {}
    prompt = str(data.get("prompt", "")).strip()

    if not prompt:
        return jsonify({"error": "missing prompt"}), 400

    max_new_tokens = int(data.get("max_new_tokens", 256))
    max_new_tokens = max(64, min(max_new_tokens, 1024))

    p, m = load_model()

    inputs = p(
        text=[prompt],
        padding=True,
        return_tensors="pt"
    )

    inputs = {
        k: v.to(device)
        for k, v in inputs.items()
    }

    with torch.no_grad():
        audio_values = m.generate(
            **inputs,
            max_new_tokens=max_new_tokens
        )

    audio = audio_values[0, 0].detach().cpu().numpy()
    sampling_rate = m.config.audio_encoder.sampling_rate

    filename = f"{uuid.uuid4().hex}.wav"
    path = os.path.join(OUT_DIR, filename)

    scipy.io.wavfile.write(path, rate=sampling_rate, data=audio)

    return jsonify({
        "ok": True,
        "prompt": prompt,
        "model": MODEL_NAME,
        "device": device,
        "file": filename,
        "url": f"/files/{filename}"
    })


@app.get("/files/<filename>")
def files(filename):
    return send_from_directory(
        OUT_DIR,
        filename,
        as_attachment=True
    )
