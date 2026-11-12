from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

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
model = None
tokenizer = None


def load_model_and_tokenizer():
    global model, tokenizer
    if model is None or tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        model.eval()
    return model, tokenizer


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
        model_obj, tokenizer_obj = load_model_and_tokenizer()
        inputs = tokenizer_obj(text, truncation=True, max_length=256, return_tensors="pt")
        inputs.pop("token_type_ids", None)

        with torch.no_grad():
            logits = model_obj(**inputs).logits

        probs = torch.softmax(logits, dim=-1)
        pred_idx = int(torch.argmax(probs, dim=-1))
        score = float(probs[0][pred_idx].item())
        label = model_obj.config.id2label.get(pred_idx, str(pred_idx))

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
