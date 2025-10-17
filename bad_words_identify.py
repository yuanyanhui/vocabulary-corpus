import os
import json
import csv
import time
import argparse
from dotenv import load_dotenv
from tqdm import tqdm
from google import genai
from google.genai import types
from cerebras.cloud.sdk import Cerebras


# --- Configuration ---
questions_prefix = "high_school_questions_only"
CSV_QUESTIONS_FILE = f"{questions_prefix}.csv"
JSON_QUESTIONS_FILE = f"{questions_prefix}.json"
BAD_QUESTIONS_FILE = f"bad_words_questions.json"
PROCESSED_COUNT_FILE = "bad_words_processed_count.txt"
ENV_FILE = ".env"
CEREBRAS_MODEL_NAME = "qwen-3-235b-a22b-instruct-2507"   # "qwen-3-235b-a22b-instruct-2507"  "gpt-oss-120b"
GEMINI_MODEL_NAME = "gemini-2.5-pro"
BATCH_SIZE = 50

SYSTEM_PROMPT = """You are an expert in vocabulary and language assessment."""

load_dotenv(dotenv_path=ENV_FILE)
cerebras_client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY_1"))
gemini_client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))


def read_json(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
    return data


def read_csv(csv_file_path):
    data = []
    with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            # The distractors are in the format "{build,board,celebrate}"
            # This needs to be converted to a list of strings.
            if 'distractors' in row and row['distractors']:
                # Remove the curly braces and split by comma
                row['distractors'] = row['distractors'].strip('{}').split(',')

             # Convert appropriate fields to integers if necessary
            if 'id' in row:
                row['id'] = int(row['id'])
            if 'headword_id' in row:
                # Assuming headword_id might be empty
                row['headword_id'] = int(row['headword_id']) if row['headword_id'] else None
            
            data.append(row)
    
    return data


def get_response_cerebas(client, prompt, model=CEREBRAS_MODEL_NAME):
    response = client.chat.completions.create(
                model=model, 
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
                response_format={
                    "type": "json_object"   # json_schema not supported by llama3
                }
            )

    return response.choices[0].message.content


def get_response_gemini(client, prompt_text, model=GEMINI_MODEL_NAME):
    # Create the generate content request with structured output
    response = client.models.generate_content(
        model=model,
        contents=prompt_text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type='application/json',
        )
    )

    return response.text.strip()

def load_saved_progress(questions_file=JSON_QUESTIONS_FILE, processed_words_count_file=PROCESSED_COUNT_FILE, bad_questions_file=BAD_QUESTIONS_FILE):
    """Loads questions, processed ids and revisions."""
    processed_words_count = 0
    existing_bad_questions = []
    try:
        # questions = read_csv(questions_file)
        questions = read_json(questions_file)
            
        if os.path.exists(processed_words_count_file):
            with open(processed_words_count_file, 'r', encoding='utf-8') as f:
                line = f.readline()
                processed_words_count = int(line.strip())
        
        questions_to_process = questions[processed_words_count:]

        # Load existing revisions if available
        if os.path.exists(bad_questions_file):
            with open(bad_questions_file, 'r', encoding='utf-8') as f:
                existing_bad_questions = json.load(f)

        return questions_to_process, processed_words_count, existing_bad_questions
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON. Please check the file format.")
        exit(1)
    except FileNotFoundError:
        print(f"Error: {questions_file} not found. Please ensure the file exists.")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)

def save_batch(bad_questions, processed_words_count, bad_questions_file=BAD_QUESTIONS_FILE, processed_words_count_file=PROCESSED_COUNT_FILE):
    """Saves the list of questions to the JSON file."""
    if 'id' in bad_questions[0]:
        sorted_questions = sorted(bad_questions, key=lambda x: x['id'])
    else:
        sorted_questions = sorted(bad_questions, key=lambda x: x['word'])
    with open(bad_questions_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_questions, f, indent=4)
    # Add a trailing newline for POSIX compatibility
    with open(bad_questions_file, 'a', encoding='utf-8') as f:
        f.write('\n')

    # Save processed IDs
    with open(processed_words_count_file, 'w', encoding='utf-8') as f:
        f.write(str(processed_words_count) + '\n')


def generate_batch_prompt(questions):
    """Creates a user prompt for the Gemini API for a batch of words."""

    return f"""You are given a list of multiple-choice vocabulary questions in JSON format. Each question has the following structure:

            {{
                "id": <number>,
                "headword_id": <number>,
                "word": "<target_word>",
                "sentence": "<sentence_with_blank>",
                "answer": "<correct_answer>",
                "distractors": ["<d1>", "<d2>", "<d3>"]
            }}

            ## Your task:
            - Identify and return any questions that contain words in the sentence or distractors that are not common high-frequency words (i.e., not in the Oxford 3000 or Longman Communication 3000 lists).
            - If all words in a question are appropriate, do not include that question in your response.
            - Ensure that the structure of the returned questions matches the input format exactly.

            ## Output format:
            - Return a JSON list of identified questions.
            
            Here are the questions to process: {json.dumps(questions)}
            """

def main():
    """Main function to generate questions."""
    print("Starting...")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        default="gemini",
        help="Specify the model (default: gemini)",
    )
    args = parser.parse_args()

    model_name = args.model

    print(f"Reviewing questions with model: {model_name}")

    questions_to_process, processed_words_count, bad_questions = load_saved_progress()
   
    print(f"Processing {len(questions_to_process)} total questions.")

    question_batches = [questions_to_process[i:i + BATCH_SIZE] for i in range(0, len(questions_to_process), BATCH_SIZE)]

    for question_batch in tqdm(question_batches, desc="Reviewing Questions in Batches"):
        try:
            prompt_text = generate_batch_prompt(question_batch)

            if model_name.startswith("gemini"):
                response_text = get_response_gemini(gemini_client, prompt_text)
            else:
                response_text = get_response_cerebas(cerebras_client, prompt_text)
            response_list = json.loads(response_text)
            bad_questions.extend(response_list)
            processed_words_count += len(question_batch)
            save_batch(bad_questions, processed_words_count)

            print(f"\nProcessed batch of {len(question_batch)} questions. Total bad questoins: {len(bad_questions)}")
            
        except json.JSONDecodeError:
            tqdm.write(f"\nWarning: Failed to decode JSON for batch '{question_batch}'. Response was:\n{response_text}")
            return
        except Exception as e:
            tqdm.write(f"\nAn unexpected error occurred for batch '{question_batch}': {e}")
            return

        # Rate limiting
        time.sleep(1)  # Sleep for 1 second between API calls to be safe
        

if __name__ == "__main__":
    main()