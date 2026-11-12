from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
from transformers import pipeline

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")

ALLOWED_ORIGINS = {
    "https://kenmcart.github.io",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
}


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


classifier = pipeline(
    "text-classification",
    model="kenmcart/classifier",
    tokenizer="kenmcart/classifier",
    device=-1,
)


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/ai_assisted.html")
def ai_assisted_page():
    return send_from_directory(BASE_DIR, "ai_assisted.html")


@app.route("/api/predict", methods=["POST", "OPTIONS"])
def predict():
    if request.method == "OPTIONS":
        return "", 204

    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()

    if not text:
        return jsonify({"error": "text is required"}), 400

    result = classifier(text, truncation=True, max_length=256)[0]
    return jsonify({
        "label": result["label"],
        "score": float(result["score"]),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
