import json
from classifier import classify_text

# Load test dataset
with open("test_dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

total = len(data)
correct_category = 0
correct_priority = 0
failed_cases = []

for item in data:
    text = item["text"]

    # Get AI response
    response = classify_text(text)

    # Clean JSON
    try:
        cleaned = response.replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned)

        pred_category = result.get("category")
        pred_priority = result.get("priority")

        # Compare
        if pred_category == item["expected_category"]:
            correct_category += 1
        else:
            failed_cases.append({
                "text": text,
                "error": "category mismatch",
                "expected": item["expected_category"],
                "got": pred_category
            })

        if pred_priority == item["expected_priority"]:
            correct_priority += 1

    except Exception as e:
        failed_cases.append({
            "text": text,
            "error": str(e)
        })

# Accuracy calculation
category_acc = (correct_category / total) * 100
priority_acc = (correct_priority / total) * 100

print("\n===== EVALUATION REPORT =====")
print(f"Total Samples: {total}")
print(f"Category Accuracy: {category_acc:.2f}%")
print(f"Priority Accuracy: {priority_acc:.2f}%")

print("\n===== FAILURE CASES =====")
for f in failed_cases:
    print(f)