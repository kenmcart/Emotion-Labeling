from pathlib import Path
from datasets import load_dataset
from transformers import pipeline
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd

model_path = str(Path(__file__).resolve().parent)

classifier = pipeline(
    "text-classification",
    model=model_path,
    tokenizer=model_path,
    device=-1
)

test_data = load_dataset(
    "kuwrom/fallacy",
    "classification",
    split="test"
)

test_data = test_data.shuffle(seed=42).select(range(200))
label_names = test_data.features["label"].names

texts = list(test_data["text"])

predictions = classifier(
    texts,
    batch_size=16,
    truncation=True,
    max_length=256
)

model_label2id = classifier.model.config.label2id

predicted_labels = [
    model_label2id[p["label"]]
    for p in predictions
]

actual_labels = test_data["label"]
accuracy = accuracy_score(actual_labels, predicted_labels)

print(f"\nCorrect: {sum(p == a for p, a in zip(predicted_labels, actual_labels))}")
print(f"Total: {len(actual_labels)}")
print(f"Accuracy: {accuracy:.2%}")

print("\nClassification Report:")
print(classification_report(
    actual_labels,
    predicted_labels,
    labels=list(range(len(label_names))),
    target_names=label_names,
    zero_division=0
))

print("\nExamples the model got wrong:")

shown = 0

for text, actual, predicted in zip(
    texts, actual_labels, predicted_labels
):
    if actual != predicted:
        print("\nArgument:", text)
        print("Correct:", label_names[actual])
        print("Predicted:", label_names[predicted])

        shown += 1
        if shown == 20:
            break

model_outputs = [p["label"] for p in predictions]

ground_truth = [
    label_names[int(label)] for label in actual_labels
]

study_df = pd.DataFrame({
    "input": texts,
    "model_output": model_outputs,
    "ground_truth": ground_truth
})

study_df["correct"] = (
    study_df["model_output"] == study_df["ground_truth"]
)

study_df.to_csv("fallacy_study_dataset.csv", index=False)

print("Saved fallacy_study_dataset.csv")
print("Number of trials:", len(study_df))
print("Model accuracy:", study_df["correct"].mean())