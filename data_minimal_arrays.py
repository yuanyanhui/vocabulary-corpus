import json
from pathlib import Path

def generate_minimal_arrays():
    input_dir = Path("data_simple")
    output_dir = Path("data_minimal_arrays")

    # Create the output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Make sure the input directory exists
    if not input_dir.exists():
        print(f"Error: The directory '{input_dir}' does not exist.")
        return

    word_list = []
    list_count = 1
    # Iterate over all JSON files in the input directory alphabetically
    for file_path in sorted(input_dir.glob("*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # remvoe "phonetics" from the data
            data.pop("phonetics", None)
            
            # append the simplified data to the list
            word_list.append(data)

            if len(word_list) == 100:
                # Save to the new directory with the same file name
                output_path = output_dir / f'words_{list_count}.json'
            
                # ensure_ascii=False ensures Chinese characters are saved properly instead of \uXXXX
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(word_list, f, ensure_ascii=False, indent=2)
                
                print(f"Processed: {output_path}")
                list_count += 1
                word_list = []  # Clear the list for the next batch
        except Exception as e:
            print(f"Failed to process {file_path.name}: {e}")

    # Save any remaining data if the total number of files is not a multiple of 100
    if word_list:
        output_path = output_dir / f'words_{list_count}.json'
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(word_list, f, ensure_ascii=False, indent=2)
        print(f"Processed: {output_path}")

    print("Data processing complete!")

if __name__ == "__main__":
    generate_minimal_arrays()