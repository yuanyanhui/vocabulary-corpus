import json

def convert_jsonl_to_json(input_file_path, output_file_path):
    """
    Extracts specific data from a JSONL file and saves it as a JSON file.

    Args:
        input_file_path (str): The path to the input JSONL file.
        output_file_path (str): The path to the output JSON file.
    """
    extracted_data = []
    with open(input_file_path, 'r', encoding='utf-8') as infile:
        for line in infile:
            try:
                # Load the JSON object from each line
                data = json.loads(line)

                # Extract the required data using the specified paths
                word = data.get("headWord")
                
                exam_content = data.get("content", {}).get("word", {}).get("content", {}).get("exam", [])
                
                if not exam_content:
                    continue
                
                # Assuming there is only one exam object per word
                exam_item = exam_content[0]
                question = exam_item.get("question")
                
                choices = exam_item.get("choices", [])
                answer_index = exam_item.get("answer", {}).get("rightIndex")
                
                answer = ""
                distractors = []
                
                for choice in choices:
                    if choice.get("choiceIndex") == answer_index:
                        answer = choice.get("choice")
                    else:
                        distractors.append(choice.get("choice"))
                
                # Construct the new JSON object
                if word and question and answer:
                    extracted_object = {
                        "word": word,
                        "question": question,
                        "answer": answer,
                        "distractors": distractors
                    }
                    extracted_data.append(extracted_object)

            except json.JSONDecodeError as e:
                print(f"Skipping line due to JSON decode error: {e}")
            except (KeyError, IndexError, AttributeError) as e:
                print(f"Skipping line due to missing key or index: {e}")


    # Save the array of extracted data to the output JSON file
    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        json.dump(extracted_data, outfile, indent=4, ensure_ascii=False)
        print(f"Extracted {len(extracted_data)} questions.")

# Define the input and output file paths
input_filename = 'CET4_2.jsonl'
output_filename = 'CET4_2_questions.json'

# Run the conversion function
convert_jsonl_to_json(input_filename, output_filename)

print(f"Data has been successfully extracted and saved to '{output_filename}'")
