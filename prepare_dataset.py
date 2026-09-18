from datasets import load_dataset
import json

dataset = load_dataset("dair-ai/emotion")

tweets = []

for row in dataset["train"]:
    tweets.append(row["text"])

with open("tweets.json", "w", encoding="utf-8") as f:
    json.dump(tweets, f, ensure_ascii=False, indent=2)

print(f"Exported {len(tweets)} tweets")