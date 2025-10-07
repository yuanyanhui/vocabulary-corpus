import os
import json
import csv
import time
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv
from tqdm import tqdm

# --- Configuration ---
CSV_QUESTIONS_FILE = "gpt-qwen-gemini-questions.csv"
JSON_QUESTIONS_FILE = "gpt-qwen-gemini-questions.json"
BAD_QUESTIONS_FILE = "gpt-qwen-gemini-questions-bad.json"
PROCESSED_IDS_FILE = "gqg_processed_words_count.txt"
ENV_FILE = ".env"
CEREBAS_MODEL_NAME = "qwen-3-235b-a22b-instruct-2507"   # "qwen-3-235b-a22b-instruct-2507"  "gpt-oss-120b"
BATCH_SIZE = 20

SYSTEM_PROMPT = """You are an expert in vocabulary and language assessment."""

load_dotenv(dotenv_path=ENV_FILE)
cerebras_client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY"))


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


def get_response(client, model, prompt):
    response = client.chat.completions.create(
                model=model, 
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
                response_format={
                    "type": "json_object"   # json_schema not supported by llama3
                }
            )

    return response.choices[0].message.content


def load_saved_progress(questions_file=JSON_QUESTIONS_FILE, processed_words_count_file=PROCESSED_IDS_FILE, bad_questions_file=BAD_QUESTIONS_FILE):
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

def save_batch(revisions, processed_words_count, bad_questions_file=BAD_QUESTIONS_FILE, processed_words_count_file=PROCESSED_IDS_FILE):
    """Saves the list of questions to the JSON file."""
    sorted_questions = sorted(revisions, key=lambda x: x['word'])
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
            - Identify questions where the sentence lacks sufficient context to make the correct answer (answer) the only clearly valid choice. These are cases where one or more distractors could also fit grammatically or logically.

            ## Output format:
            - Return a JSON list of identified questions.
            
            Here are the questions to process: {json.dumps(questions)}
            """

def main():
    """Main function to generate questions."""
    print("Starting...")

    questions_to_process, processed_words_count, bad_questions = load_saved_progress()
   
    print(f"Processing {len(questions_to_process)} total questions.")

    question_batches = [questions_to_process[i:i + BATCH_SIZE] for i in range(0, len(questions_to_process), BATCH_SIZE)]

    for question_batch in tqdm(question_batches, desc="Reviewing Questions in Batches"):
        try:
            prompt_text = generate_batch_prompt(question_batch)

            # Create the generate content request with structured output
            response_text = get_response(cerebras_client, CEREBAS_MODEL_NAME, prompt_text)
            revisions_data = json.loads(response_text)
            bad_questions.extend(revisions_data)
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
        time.sleep(5)  # Sleep for 1 second between API calls to be safe
        

if __name__ == "__main__":
    main()