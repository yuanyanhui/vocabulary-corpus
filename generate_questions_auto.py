import os
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tqdm import tqdm

# --- Configuration ---
WORDS_FILE = "words_available.txt"
QUESTIONS_FILE = "questions.json"
ENV_FILE = ".env"
API_KEY_NAME = "GEMINI_API_KEY"
MODEL_NAME = "gemini-2.5-flash"
BATCH_SIZE = 10

SYSTEM_PROMPT = """You are an expert in vocabulary and language assessment. Your task is to create a list of multiple-choice questions based on a list of words provided by the user.

For each word in the list, you must generate one JSON object. The entire output must be a single, well-formed JSON array `[...]` containing these objects.

Follow these instructions for each word:
1.  Create a single, clear sentence where the word OR ONE OF ITS INFLECTED FORMS is used correctly but is replaced by a "___" blank.
2.  You may use different inflected forms of the word (such as: verb tenses like "abandoned", "abandoning", "abandons"; plural nouns like "abilities"; comparative/superlative adjectives, etc.) in the sentence as long as they are direct morphological variations of the original word.
3.  The `word` field in the JSON must be the original word from the list you are generating the question for.
4.  The `answer` field must be the specific inflected form of the word that correctly fills the blank in your sentence.
5.  Generate three incorrect "distractor" words.
6.  The distractors MUST meet the following criteria:
    - They must be the same part of speech as the word that fills the blank (the answer).
    - They must make grammatical sense in the sentence.
    - They should be semantically related to the target word or the context of the sentence to be plausible alternatives.
    - They must be clearly incorrect when considering the full meaning and context of the sentence.

Your final output must be a single, well-formed JSON array. Do not include any text, explanations, or markdown formatting like ```json before or after the JSON array.

The user will provide an example of the expected output format in their prompt.
"""


def load_api_key():
    """Loads the Gemini API key from an environment file."""
    load_dotenv(dotenv_path=ENV_FILE)
    api_key = os.getenv(API_KEY_NAME)
    if not api_key:
        print(f"Error: {API_KEY_NAME} not found in {ENV_FILE} or environment variables.")
        print("Please create a .env file and add your Gemini API key to it.")
        exit(1)
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
    with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=4)
    # Add a trailing newline for POSIX compatibility
    with open(QUESTIONS_FILE, 'a', encoding='utf-8') as f:
        f.write('\n')

def generate_batch_prompt(words):
    """Creates a simplified user prompt for the Gemini API for a batch of words."""
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
    api_key = load_api_key()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=SYSTEM_PROMPT,
        generation_config={"response_mime_type": "application/json"},
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

    # --- Generation Loop ---
    new_questions_generated = 0
    # Create batches of words
    word_batches = [words_to_process[i:i + BATCH_SIZE] for i in range(0, len(words_to_process), BATCH_SIZE)]

    for word_batch in tqdm(word_batches, desc="Generating Questions in Batches"):
        try:
            prompt_text = generate_batch_prompt(word_batch)

            response = model.generate_content(prompt_text)

            # The response is expected to be a JSON array.
            response_text = response.text.strip()

            # Find the start and end of the JSON array
            start_index = response_text.find('[')
            end_index = response_text.rfind(']') + 1
            if start_index == -1 or end_index == 0:
                print(f"\nWarning: Could not find a JSON array in the response for batch '{word_batch}'. Skipping.")
                continue

            json_text = response_text[start_index:end_index]
            questions_data = json.loads(json_text)

            if len(questions_data) != len(word_batch):
                print(f"\nWarning: Mismatch in expected number of questions for batch '{word_batch}'.")
                print(f"Expected {len(word_batch)}, but got {len(questions_data)}. Skipping batch.")
                continue

            # Basic validation for each question object
            valid_questions = []
            for i, q_data in enumerate(questions_data):
                if all(k in q_data for k in ['word', 'question', 'answer', 'distractors']):
                     valid_questions.append(q_data)
                else:
                    print(f"\nWarning: Received malformed JSON data for word '{word_batch[i]}'. Skipping.")

            if valid_questions:
                questions.extend(valid_questions)
                new_questions_generated += len(valid_questions)

        except json.JSONDecodeError:
            print(f"\nWarning: Failed to decode JSON for batch '{word_batch}'. Response was:\n{response_text}")
        except Exception as e:
            print(f"\nAn unexpected error occurred for batch '{word_batch}': {e}")

        # Rate limiting
        time.sleep(1)  # Sleep for 1 second between API calls to be safe

    # --- Save Results ---
    if new_questions_generated > 0:
        print(f"\nGenerated {new_questions_generated} new questions.")
        print("Saving updated questions list...")
        save_questions(questions)
        print("Done.")
    else:
        print("\nNo new questions were generated in this run.")

if __name__ == "__main__":
    main()
