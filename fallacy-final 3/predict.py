
from pathlib import Path
from transformers import pipeline

# Directory containing predict.py
model_path = str(Path(__file__).resolve().parent)

classifier = pipeline(
    "text-classification",
    model=model_path,
    tokenizer=model_path,
    device=-1
)

argument = (
    "Ice cream sales increase in the summer and so do shark attacks, hence buying ice cream causes shark attacks."
)

prediction = classifier(
    argument,
    truncation=True,
    max_length=256
)

print(prediction)