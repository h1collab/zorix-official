import os
import uuid
import torch
from flask import Flask, request, jsonify, send_from_directory
from diffusers import AutoPipelineForText2Image

app = Flask(__name__)

OUT_DIR = "/tmp/images"
os.makedirs(OUT_DIR, exist_ok=True)

MODEL_NAME = os.environ.get("MODEL_NAME", "stabilityai/sdxl-turbo")
API_KEY = os.environ.get("ZORIX_IMAGE_API_KEY", "")

device = "cuda" if torch.cuda.is_available() else "cpu"
pipe = None


def load_pipe():
    global pipe

    if pipe is None:
        dtype = torch.float16 if device == "cuda" else torch.float32

        pipe = AutoPipelineForText2Image.from_pretrained(
            MODEL_NAME,
            torch_dtype=dtype,
            variant="fp16" if device == "cuda" else None
        )

        pipe = pipe.to(device)

        if device == "cuda":
            pipe.enable_model_cpu_offload()

    return pipe


@app.get("/")
def home():
    return jsonify({
        "ok": True,
        "service": "Zorix Image SDXL Turbo",
        "model": MODEL_NAME,
        "device": device,
        "loaded": pipe is not None
    })


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "device": device,
        "model": MODEL_NAME,
        "loaded": pipe is not None
    })


@app.post("/generate")
def generate():
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "unauthorized"}), 401

    data = request.json or {}

    prompt = str(data.get("prompt", "")).strip()
    if not prompt:
        return jsonify({"error": "missing prompt"}), 400

    negative_prompt = str(data.get("negative_prompt", "")).strip()

    width = int(data.get("width", 1024))
    height = int(data.get("height", 1024))
    steps = int(data.get("steps", 4))
    guidance_scale = float(data.get("guidance_scale", 0.0))

    width = max(512, min(width, 1024))
    height = max(512, min(height, 1024))
    steps = max(1, min(steps, 8))

    p = load_pipe()

    with torch.inference_mode():
        image = p(
            prompt=prompt,
            negative_prompt=negative_prompt if negative_prompt else None,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale
        ).images[0]

    filename = f"{uuid.uuid4().hex}.png"
    path = os.path.join(OUT_DIR, filename)
    image.save(path)

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
