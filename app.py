from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

ACE_URL = "http://127.0.0.1:7860"

@app.get("/")
def home():
    return "Zorix ACE-Step Gateway"

@app.post("/generate")
def generate():
    data = request.json or {}

    r = requests.post(
        f"{ACE_URL}/api/generate",
        json=data,
        timeout=3600
    )

    return jsonify(r.json())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
