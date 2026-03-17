import json
from pathlib import Path

def simplify_dictionary_data():
    input_dir = Path("data")
    output_dir = Path("data_simple")

    # Create the output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Make sure the input directory exists
    if not input_dir.exists():
        print(f"Error: The directory '{input_dir}' does not exist.")
        return

    # Iterate over all JSON files in the input directory
    for file_path in input_dir.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Extract and filter definitions
            simplified_definitions = [
                # Only keep specific keys if they exist in the original definition
                {k: d[k] for k in ["partOfSpeech", "definition", "chineseTranslation"] if k in d}
                for d in data.get("definitions", [])
            ]
            
            # Extract and filter examples
            simplified_examples = [
                # Only keep specific keys if they exist in the original example
                {k: e[k] for k in ["sentence", "translation"] if k in e}
                for e in data.get("examples", [])
            ]
            
            # Construct the new simplified dictionary
            simplified_data = {
                "word": data.get("word"),
                "phonetics": data.get("phonetics"),
                "definitions": simplified_definitions,
                "examples": simplified_examples
            }
            
            # Remove keys where the value is None (in case "word" or "phonetics" were missing)
            simplified_data = {k: v for k, v in simplified_data.items() if v is not None}
            
            # Save to the new directory with the same file name
            output_path = output_dir / file_path.name
            
            # ensure_ascii=False ensures Chinese characters are saved properly instead of \uXXXX
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(simplified_data, f, ensure_ascii=False, indent=2)
                
            print(f"Processed: {file_path.name}")
            
        except Exception as e:
            print(f"Failed to process {file_path.name}: {e}")

    print("Data extraction complete!")

if __name__ == "__main__":
    simplify_dictionary_data()