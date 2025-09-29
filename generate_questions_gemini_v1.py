import os
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tqdm import tqdm
import shutil

# --- Configuration ---
WORDS_FILE = "words_available.txt"
QUESTIONS_FILE = "questions_pro.json"
ENV_FILE = ".env"
API_KEY_NAME = "GEMINI_API_KEY"
MODEL_NAME = "gemini-2.5-pro"  # Note: Model names might change, verify in the documentation.
BATCH_SIZE = 30

SYSTEM_PROMPT = """You are an expert in vocabulary and language assessment. Your task is to create multiple-choice questions based on a provided word list.

## Output Format
Generate a single, well-formed JSON array containing one object per word. Each object must include:
- `word`: The original word from the provided list
- `answer`: The specific inflected form that correctly completes the sentence
- `distractors`: Array of three incorrect options

Do not include any explanatory text, markdown formatting, or code blocks—output only the JSON array.

## Instructions for Each Word
1. **Sentence Creation**: Write a clear, contextually rich sentence using the word or one of its inflected forms, replacing it with "___"
2. **Inflected Forms**: You may use any direct morphological variation of the original word (verb tenses, plural nouns, comparative/superlative adjectives, etc.)
3. **Contextual Usage**: When possible, incorporate the word within a natural phrase or idiomatic expression

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

The user will provide the word list and expected output format example.
"""


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

def load_words():
    """Loads the list of words from the specified file."""
    try:
        with open(WORDS_FILE, 'r', encoding='utf-8') as f:
            return sorted([line.strip() for line in f if line.strip()])
    except FileNotFoundError:
        print(f"Error: Words file not found at {WORDS_FILE}")
        return []

def load_existing_questions():
    """Loads existing questions and a set of processed words."""
    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            questions = json.load(f)
            processed_words = {q['word'] for q in questions}
            return questions, processed_words
    except (FileNotFoundError, json.JSONDecodeError):
        return [], set()

def save_questions(questions):
    """Saves the list of questions to the JSON file."""
    # Sort questions by the original 'word' field before saving
    sorted_questions = sorted(questions, key=lambda x: x['word'])
    with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sorted_questions, f, indent=4)
    # Add a trailing newline for POSIX compatibility
    with open(QUESTIONS_FILE, 'a', encoding='utf-8') as f:
        f.write('\n')

def generate_batch_prompt(words):
    """Creates a user prompt for the Gemini API for a batch of words."""
    word_list_str = ", ".join([f'"{word}"' for word in words])
    return f"""
        I need multiple-choice questions for the following words: {word_list_str}.

        Here is an example of the expected JSON output format for the words "abandon", "ability", "able", "abolish", "abortion":
        ```json
        [
            {{
                "word": "abandon",
                "question": "The old mansion had been ___ for decades, with broken windows and overgrown gardens.",
                "answer": "abandoned",
                "distractors": [
                    "renovated",
                    "occupied",
                    "maintained"
                ]
            }},
            {{
                "word": "ability",
                "question": "Her remarkable mathematical ___ have impressed professors throughout her academic career.",
                "answer": "abilities",
                "distractors": [
                    "tendencies",
                    "opportunities",
                    "ambitions"
                ]
            }},
            {{
                "word": "able",
                "question": "After months of practice, she was finally ___ to play the piece flawlessly.",
                "answer": "able",
                "distractors": [
                    "willing",
                    "eager",
                    "ready"
                ]
            }},
            {{
                "word": "abolish",
                "question": "The new administration ___ the outdated regulation in their first month in office.",
                "answer": "abolished",
                "distractors": [
                    "reinforced",
                    "modified",
                    "postponed"
                ]
            }},
            {{
                "word": "abortion",
                "question": "The clinic provided counseling services for women considering ___ as well as those choosing to continue their pregnancies.",
                "answer": "abortion",
                "distractors": [
                    "adoption",
                    "delivery",
                    "conception"
                ]
            }}
        ]
        ```

        Now, generate the JSON array for the words: **{word_list_str}**
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

    all_words = load_words()
    if not all_words:
        return

    questions, processed_words = load_existing_questions()
    words_to_process = [word for word in all_words if word not in processed_words]

    if not words_to_process:
        print("All words from the list have already been processed. Nothing to do.")
        return

    print(f"Found {len(all_words)} total words.")
    print(f"{len(processed_words)} words already processed.")
    print(f"Starting generation for {len(words_to_process)} new words.")

    if len(processed_words) > 0:
        # backup existing questions file with timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        backup_file = f"{QUESTIONS_FILE}.{timestamp}.bak"
        shutil.copy(QUESTIONS_FILE, backup_file)
        print(f"Backed up existing questions file to {backup_file}")

    # --- Generation Loop ---
    new_questions_generated = 0
    # Create batches of words
    word_batches = [words_to_process[i:i + BATCH_SIZE] for i in range(0, len(words_to_process), BATCH_SIZE)]

    for word_batch in tqdm(word_batches, desc="Generating Questions in Batches"):
        try:
            prompt_text = generate_batch_prompt(word_batch)

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
            questions_data = json.loads(response_text)

            if len(questions_data) != len(word_batch):
                tqdm.write(f"\nWarning: Mismatch in expected number of questions for batch '{word_batch}'.")
                tqdm.write(f"Expected {len(word_batch)}, but got {len(questions_data)}. Skipping batch.")
                continue

            # Basic validation for each question object
            valid_questions = []
            for i, q_data in enumerate(questions_data):
                if all(k in q_data for k in ['word', 'question', 'answer', 'distractors']):
                     valid_questions.append(q_data)
                else:
                    tqdm.write(f"\nWarning: Received malformed JSON data for word '{word_batch[i]}'. Skipping.")

            if valid_questions:
                questions.extend(valid_questions)
                new_questions_generated += len(valid_questions)
                # Save the updated list of questions right after processing the batch
                save_questions(questions)
                tqdm.write(f"Saved {len(valid_questions)} new questions from batch.")

        except json.JSONDecodeError:
            tqdm.write(f"\nWarning: Failed to decode JSON for batch '{word_batch}'. Response was:\n{response_text}")
            return
        except Exception as e:
            tqdm.write(f"\nAn unexpected error occurred for batch '{word_batch}': {e}")
            return

        # Rate limiting
        time.sleep(5)  # Sleep for 1 second between API calls to be safe

    # --- Final Summary ---
    if new_questions_generated > 0:
        print(f"\nGeneration complete. A total of {new_questions_generated} new questions were generated and saved.")
    else:
        print("\nNo new questions were generated in this run.")

if __name__ == "__main__":
    main()