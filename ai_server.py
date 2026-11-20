from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")

torch.set_num_threads(1)

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
    """Load and cache the model once on the first prediction request."""
    global model, tokenizer
    if model is None or tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_NAME,
            low_cpu_mem_usage=False,
        )
        model.eval()

        # Quantize linear layers after loading to reduce runtime memory.
        model = torch.quantization.quantize_dynamic(
            model,
            {torch.nn.Linear},
            dtype=torch.qint8,
        )
        model.eval()
    return model, tokenizer


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS or origin.startswith("https://kenmcart.github.io"):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Vary"] = "Origin"
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
        inputs = tokenizer_obj(
            text,
            truncation=True,
            max_length=256,
            return_tensors="pt",
        )
        inputs.pop("token_type_ids", None)

        with torch.no_grad():
            logits = model_obj(**inputs).logits

        probabilities = torch.softmax(logits, dim=-1)
        predicted_index = int(torch.argmax(probabilities, dim=-1).item())
        score = float(probabilities[0][predicted_index].item())

        id2label = model_obj.config.id2label or {}
        label = id2label.get(predicted_index, id2label.get(str(predicted_index), str(predicted_index)))

        return jsonify({"label": label, "score": score})
    except Exception as exc:
        app.logger.exception("Prediction failed")
        return jsonify({
            "error": "model prediction failed",
            "detail": str(exc),
        }), 500


@app.route("/api/warmup", methods=["GET", "OPTIONS"])
def warmup():
    if request.method == "OPTIONS":
        return "", 204

    try:
        load_model_and_tokenizer()
        return jsonify({"status": "ready"})
    except Exception as exc:
        app.logger.exception("Model warmup failed")
        return jsonify({"status": "error", "detail": str(exc)}), 500


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/ai_assisted.html")
def ai_assisted_page():
    return send_from_directory(BASE_DIR, "ai_assisted.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
