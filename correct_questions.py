import json

# Input/output file names
REPLACEMENTS_FILE = "gemini-pro-questions-revisions.json"
TARGET_FILE = "gemini-pro-questions.json"
OUTPUT_FILE = "gemini-pro-questions-final.json"

def main():
    # Load both JSON files
    with open(REPLACEMENTS_FILE, "r", encoding="utf-8") as f:
        replacements = json.load(f)

    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        target = json.load(f)

    # Index replacements by word
    replacements_dict = {item["word"]: item for item in replacements}

    # Replace items in target where word matches
    updated = []
    for item in target:
        word = item.get("word")
        if word in replacements_dict:
            updated.append(replacements_dict[word])
        else:
            updated.append(item)

    # Save updated JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(updated, f, ensure_ascii=False, indent=4)

    print(f"Updated file saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
