import os
import json
import time
import argparse
from dotenv import load_dotenv
from tqdm import tqdm
from google import genai
from google.genai import types
from cerebras.cloud.sdk import Cerebras

# --- Configuration ---
questions_prefix = "high_school_questions_only_bad"
QUESTIONS_FILE = f"{questions_prefix}.json"
REVISIONS_FILE = f"{questions_prefix}-revisions.json"
PROCESSED_IDS_FILE = f"{questions_prefix}_revised_count.txt"
ENV_FILE = ".env"
CEREBRAS_MODEL_NAME = "qwen-3-235b-a22b-instruct-2507"   # "qwen-3-235b-a22b-instruct-2507"  "gpt-oss-120b"
GEMINI_MODEL_NAME = "gemini-2.5-pro"
BATCH_SIZE = 100

SYSTEM_PROMPT = """You are an expert in vocabulary and language assessment."""

load_dotenv(dotenv_path=ENV_FILE)
cerebras_client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY_1"))
gemini_client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))


def get_response_cerebas(client, prompt, model=CEREBRAS_MODEL_NAME):
    response = client.chat.completions.create(
                model=model, 
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
                response_format={
                    "type": "json_object"  
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


def load_saved_progress(questions_file=QUESTIONS_FILE, processed_words_count_file=PROCESSED_IDS_FILE, revisions_file=REVISIONS_FILE):
    """Loads questions, processed ids and revisions."""
    processed_words_count = 0
    existing_revisions = []
    try:
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)
            
        if os.path.exists(processed_words_count_file):
            with open(processed_words_count_file, 'r', encoding='utf-8') as f:
                line = f.readline()
                processed_words_count = int(line.strip())
        
        questions_to_process = questions[processed_words_count:]

        # Load existing revisions if available
        if os.path.exists(revisions_file):
            with open(revisions_file, 'r', encoding='utf-8') as f:
                existing_revisions = json.load(f)

        return questions_to_process, processed_words_count, existing_revisions
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON. Please check the file format.")
        exit(1)
    except FileNotFoundError:
        print(f"Error: {questions_file} not found. Please ensure the file exists.")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)


def save_batch(revisions, processed_words_count, revisions_file=REVISIONS_FILE, processed_words_count_file=PROCESSED_IDS_FILE):
    """Saves the list of questions to the JSON file."""
    if 'id' in revisions[0]:
        sorted_revisions = sorted(revisions, key=lambda x: x['id'])
    else:
        sorted_revisions = sorted(revisions, key=lambda x: x['word'])
    with open(revisions_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_revisions, f, indent=4)
    # Add a trailing newline for POSIX compatibility
    with open(revisions_file, 'a', encoding='utf-8') as f:
        f.write('\n')

    # Save processed IDs
    with open(processed_words_count_file, 'w', encoding='utf-8') as f:
        # concatenate existing processed IDs into a single string
        f.write(str(processed_words_count) + '\n')


def generate_batch_prompt(questions):
    """Creates a user prompt for the Gemini API for a batch of words."""

    return f"""The attached json code contains an array of multiple-choice vocabulary questions. Please identify bad questions not meeting the following requirements. 

            ```
            ## Sentence Requirements
            Each sentence must:
            - Clearly establish context that demonstrates the meaning of the target word.
            - Contain sufficient clues (emotional tone, situation, cause–effect, or sensory cues) that make only the target word fit naturally.
            - Maintain natural, fluent, and grammatically correct English.

            ## Distractor Requirements
            Each distractor must:
            - Match the part of speech of the correct answer
            - Be grammatically valid in the sentence context
            - Relate semantically to the target word or sentence topic (ensuring plausibility)
            - Be clearly incorrect given the complete sentence meaning and context

            ## Quality Standards
            - Sentences should demonstrate the word's meaning through context
            - Distractors should be challenging but definitively wrong
            - All options should appear plausible to someone unfamiliar with the target word
            ```

            Please provide revisions for the identified bad questions by modifying either the sentence or the distractors. Output revised items in a single json array without explanations.
            
            Here are the questions to process: {json.dumps(questions)}
            """

def main():
    """Main function to generate questions."""    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-pro",
        help="Specify the model (default: gemini-pro)",
    )
    args = parser.parse_args()

    model_name = args.model

    print(f"Revising questions with model: {model_name}")

    questions_to_process, processed_words_count, question_revisions = load_saved_progress()
   
    print(f"Processing {len(questions_to_process)} total questions.")

    question_batches = [questions_to_process[i:i + BATCH_SIZE] for i in range(0, len(questions_to_process), BATCH_SIZE)]

    for question_batch in tqdm(question_batches, desc="Revising Questions in Batches"):
        try:
            prompt_text = generate_batch_prompt(question_batch)
            if model_name.startswith("gemini"):
                response_text = get_response_gemini(gemini_client, prompt_text)
            else:
                response_text = get_response_cerebas(cerebras_client, prompt_text)
            
            response_list = json.loads(response_text)
            question_revisions.extend(response_list)
            processed_words_count += len(question_batch)

            save_batch(question_revisions, processed_words_count)

            print(f"\nProcessed batch of {len(question_batch)} questions. Total revisions so far: {len(question_revisions)}")
            
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