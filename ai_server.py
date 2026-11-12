from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
from transformers import pipeline

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = Path("/Users/kennedy/Downloads/fallacy-final 3")

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")

classifier = pipeline(
    "text-classification",
    model=str(MODEL_DIR),
    tokenizer=str(MODEL_DIR),
    device=-1,
)


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/ai_assisted.html")
def ai_assisted_page():
    return send_from_directory(BASE_DIR, "ai_assisted.html")


@app.route("/api/predict", methods=["POST"])
def predict():
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
