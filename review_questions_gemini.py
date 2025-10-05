import os
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tqdm import tqdm

# --- Configuration ---
QUESTIONS_FILE = "gemini-pro-questions.json"
REVISIONS_FILE = "gemini-pro-questions-revisions.json"
PROCESSED_IDS_FILE = "processed_words_count.txt"
ENV_FILE = ".env"
API_KEY_NAME = "GEMINI_API_KEY"
MODEL_NAME = "gemini-2.5-pro"  # Note: Model names might change, verify in the documentation.
BATCH_SIZE = 50

SYSTEM_PROMPT = """You are an expert in vocabulary and language assessment."""


def load_api_key():
    """Loads the Gemini API key from an environment file."""
    load_dotenv(dotenv_path=ENV_FILE)
    api_key = os.getenv(API_KEY_NAME)
    if not api_key:
        print(f"Error: {API_KEY_NAME} not found in {ENV_FILE} or environment variables.")
        print("Please create a .env file and add your Gemini API key to it.")
        exit(1)
    # The new SDK automatically picks up the key from the environment variable,
    # so we just need to ensure it's loaded.
    return api_key


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
    print("Starting question generation process...")

    # --- Initialization ---
    load_api_key()
    # The new SDK uses a client object. It automatically finds the API key
    # from the environment variable GEMINI_API_KEY.
    client = genai.Client()

    # Define model configuration, including system prompt and JSON output.
    model_config = types.GenerationConfig(
        response_mime_type="application/json"
    )

    questions_to_process, processed_words_count, question_revisions = load_saved_progress()
   
    print(f"Processing {len(questions_to_process)} total questions.")

    question_batches = [questions_to_process[i:i + BATCH_SIZE] for i in range(0, len(questions_to_process), BATCH_SIZE)]

    for question_batch in tqdm(question_batches, desc="Revising Questions in Batches"):
        try:
            prompt_text = generate_batch_prompt(question_batch)

            # Create the generate content request with structured output
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type='application/json',
                )
            )

            response_text = response.text.strip()
            revisions_data = json.loads(response_text)

            question_revisions.extend(revisions_data)
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