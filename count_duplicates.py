import json

# Load JSON files
def load_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

flash_data = load_json("questions_gpt_oss.json")
qwen_data = load_json("questions_qwen.json")

# Build a set of (word, question) from first file
flash_set = {(item["word"], item["question"]) for item in flash_data}

# Find duplicates in second file
duplicates = [
    item for item in qwen_data
    if (item["word"], item["question"]) in flash_set
]

# create a list of duplicates words
duplicate_words = [item["word"] for item in duplicates]
print(f"Found {len(duplicates)} duplicate items.")
for word in duplicate_words:
    print(word)

# Print results
# if duplicates:
#     print("Duplicate items found:")
#     for dup in duplicates:
#         print(json.dumps(dup, ensure_ascii=False, indent=2))
# else:
#     print("No duplicates found.")
