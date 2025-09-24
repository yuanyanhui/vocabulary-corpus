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
MODEL_NAME = "gemini-1.5-flash-latest"

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

def generate_prompt(word):
    """Creates a detailed prompt for the Gemini API."""
    return f"""
You are an expert in vocabulary and language assessment. Your task is to create a multiple-choice question to test the user's understanding of the word "{word}".

Follow these instructions precisely:
1.  Create a single, clear sentence where the word "{word}" is used correctly but is replaced by a "___" blank.
2.  The word for this question is: **{word}**
3.  The correct answer is the word itself.
4.  Generate three incorrect "distractor" words.
5.  The distractors MUST meet the following criteria:
    - They must be the same part of speech as "{word}".
    - They must make grammatical sense in the sentence.
    - They should be semantically related to the target word or the context of the sentence to be plausible alternatives.
    - They must be clearly incorrect when considering the full meaning and context of the sentence.

Your final output must be a single, well-formed JSON object. Do not include any text, explanations, or markdown formatting like ```json before or after the JSON object.

The JSON object must have the following structure:
{{
    "word": "{word}",
    "question": "The sentence with the blank.",
    "answer": "{word}",
    "distractors": [
        "distractor1",
        "distractor2",
        "distractor3"
    ]
}}

Now, generate the JSON for the word: **{word}**
"""

def main():
    """Main function to generate questions."""
    print("Starting question generation process...")

    # --- Initialization ---
    api_key = load_api_key()
    client = genai.Client(api_key=api_key)

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
    for word in tqdm(words_to_process, desc="Generating Questions"):
        try:
            prompt_text = generate_prompt(word)
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt_text)])]

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents
            )

            # Clean up the response text to extract only the JSON
            response_text = response.text.strip()
            # Find the start and end of the JSON object
            start_index = response_text.find('{')
            end_index = response_text.rfind('}') + 1
            if start_index == -1 or end_index == 0:
                print(f"\nWarning: Could not find a JSON object in the response for '{word}'. Skipping.")
                continue

            json_text = response_text[start_index:end_index]

            question_data = json.loads(json_text)

            # Basic validation
            if 'word' in question_data and 'question' in question_data and 'answer' in question_data and 'distractors' in question_data:
                questions.append(question_data)
                new_questions_generated += 1
            else:
                print(f"\nWarning: Received malformed JSON data for '{word}'. Skipping.")

        except json.JSONDecodeError:
            print(f"\nWarning: Failed to decode JSON for word '{word}'. Response was:\n{response.text}")
        except Exception as e:
            print(f"\nAn unexpected error occurred for word '{word}': {e}")

        # Rate limiting
        time.sleep(1) # Sleep for 1 second between API calls to be safe

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
