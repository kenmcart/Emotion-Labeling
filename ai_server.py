from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
import os
import requests

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")

ALLOWED_ORIGINS = {
    "https://kenmcart.github.io",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
}

MODEL_NAME = "kenmcart/classifier"
HF_INFERENCE_URL = f"https://router.huggingface.co/hf-inference/models/{MODEL_NAME}"
HF_TOKEN = os.getenv("HF_TOKEN")


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


@app.route("/api/predict", methods=["POST", "OPTIONS"])
def predict():
    if request.method == "OPTIONS":
        return "", 204

    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()

    if not text:
        return jsonify({"error": "text is required"}), 400

    try:
        if not HF_TOKEN:
            return jsonify({
                "error": "HF_TOKEN is not configured on Render",
            }), 500

        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = requests.post(
            HF_INFERENCE_URL,
            headers=headers,
            json={"inputs": text},
            timeout=60,
        )

        try:
            provider_result = response.json()
        except ValueError:
            provider_result = response.text

        if not response.ok:
            app.logger.error("Hugging Face error %s: %s", response.status_code, provider_result)
            return jsonify({
                "error": "Hugging Face Inference failed",
                "detail": str(provider_result),
            }), response.status_code

        result = provider_result

        if isinstance(result, list):
            if result and isinstance(result[0], list):
                result = result[0]
            if result:
                prediction = result[0]
            else:
                raise ValueError("Hugging Face returned an empty prediction")
        elif isinstance(result, dict):
            prediction = result
        else:
            raise ValueError("Unexpected Hugging Face response format")

        label = prediction.get("label", "unknown")
        score = float(prediction.get("score", 0.0))

        return jsonify({
            "label": label,
            "score": score,
        })
    except Exception as exc:
        app.logger.exception("Prediction failed")
        return jsonify({
            "error": "model prediction failed",
            "detail": str(exc),
        }), 500


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/ai_assisted.html")
def ai_assisted_page():
    return send_from_directory(BASE_DIR, "ai_assisted.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
