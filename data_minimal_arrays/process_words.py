# process_words.py 
import os
import json
import time
from tqdm import tqdm
from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are a linguist in English and Chinese."""
PROCESSED_FILES_RECORD = "processed_files.txt"
SOURCE_DIR = "source"
UPDATED_DIR = "updated"


def generate_batch_prompt(words):
    """Creates a user prompt for the Gemini API for a batch of words."""

    return f'''The following json is a dictionary entry.
    ```
    {{
      "word": "zymotic",
      "definitions": [
        {{
          "partOfSpeech": "adjective",
          "definition": "Relating to or caused by fermentation, especially in biological or chemical processes.",
          "chineseTranslation": "与发酵相关的，尤其在生物或化学过程中"
        }},
        {{
          "partOfSpeech": "adjective",
          "definition": "Archaic: Relating to infectious diseases, particularly those thought to be caused by fermentation-like processes.",
          "chineseTranslation": "过时的，与传染病相关的，特别是那些被认为由类似发酵过程引起的疾病"
        }}
      ],
      "examples": [
        {{
          "sentence": "The scientist studied the zymotic reactions in yeast to improve fermentation efficiency.",
          "translation": "科学家研究酵母中的发酵反应，以提高发酵效率。"
        }},
        {{
          "sentence": "Historically, zymotic diseases like cholera were linked to poor sanitation in cities.",
          "translation": "历史上，发酵相关的疾病如霍乱与城市卫生条件差有关。"
        }},
        {{
          "sentence": "In modern biotechnology, understanding zymotic principles has led to advancements in biofuel production.",
          "translation": "在现代生物技术中，理解发酵原理导致了生物燃料生产的进步。"
        }}
      ]
    }}
    ```
    The "examples" field is on the same level as the "definitions" field. Ideally, an example helps explain a particular definition. Therefore, it would be better to associate the examples with the definitions. To do so, we have to move the examples under their corresponding definitions.
    ```
    {{
      "word": "zymotic",
      "definitions": [
        {{
          "partOfSpeech": "adjective",
          "definition": "Relating to or caused by fermentation, especially in biological or chemical processes.",
          "chineseTranslation": "与发酵相关的，尤其在生物或化学过程中",
          "examples": [
              {{
                "sentence": "The scientist studied the zymotic reactions in yeast to improve fermentation efficiency.",
                "translation": "科学家研究酵母中的发酵反应，以提高发酵效率。"
              }},
              {{
                "sentence": "In modern biotechnology, understanding zymotic principles has led to advancements in biofuel production.",
                "translation": "在现代生物技术中，理解发酵原理导致了生物燃料生产的进步。"
              }}
            ]
        }},
        {{
          "partOfSpeech": "adjective",
          "definition": "Archaic: Relating to infectious diseases, particularly those thought to be caused by fermentation-like processes.",
          "chineseTranslation": "过时的，与传染病相关的，特别是那些被认为由类似发酵过程引起的疾病",
          "examples": [
              {{
                "sentence": "Historically, zymotic diseases like cholera were linked to poor sanitation in cities.",
                "translation": "历史上，发酵相关的疾病如霍乱与城市卫生条件差有关。"
              }}
            ]
        }}
      ]
    }}
    ```
    Your task is to update all the entries in the following json array: {json.dumps(words)}
    '''


def generate(prompt):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-3-flash-preview"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=-1,
        ),
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
       
    return response.text.strip()


def load_processed_files(record_file=PROCESSED_FILES_RECORD):
    """Loads the list of already processed file names."""
    processed = set()
    if os.path.exists(record_file):
        with open(record_file, 'r', encoding='utf-8') as f:
            for line in f:
                filename = line.strip()
                if filename:
                    processed.add(filename)
    return processed


def save_processed_file(filename, record_file=PROCESSED_FILES_RECORD):
    """Saves a processed file name to the tracking record."""
    with open(record_file, 'a', encoding='utf-8') as f:
        f.write(f"{filename}\n")


def main():
    # Ensure directories exist
    os.makedirs(SOURCE_DIR, exist_ok=True)
    os.makedirs(UPDATED_DIR, exist_ok=True)

    # Load progress
    processed_files = load_processed_files()
    
    # Get all json files in source directory
    all_files = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".json")]
    
    # Filter out files that have already been processed
    files_to_process = [f for f in all_files if f not in processed_files]
    
    print(f"Total files: {len(all_files)}")
    print(f"Already processed: {len(processed_files)}")
    print(f"Files to process: {len(files_to_process)}\n")

    # Iterate through the files with a progress bar
    for filename in tqdm(files_to_process, desc="Processing files"):
        try:
            source_path = os.path.join(SOURCE_DIR, filename)
            updated_path = os.path.join(UPDATED_DIR, filename)

            with open(source_path, "r", encoding='utf-8') as f:
                words = json.load(f)
            
            prompt = generate_batch_prompt(words)
            updated_words = generate(prompt)
            
            # save the updated words to the "updated" directory with the same filename
            with open(updated_path, "w", encoding='utf-8') as f:
                json.dump(json.loads(updated_words), f, ensure_ascii=False, indent=2)

            # Record the file as successfully processed
            save_processed_file(filename)

        except json.JSONDecodeError:
            tqdm.write(f"\nWarning: Failed to decode JSON for file '{filename}'. Response from API may be invalid.")
            break
        except Exception as e:
            tqdm.write(f"\nAn unexpected error occurred for file '{filename}': {e}")
            break

        # Rate limiting: Sleep between API calls
        time.sleep(5)


if __name__ == "__main__":
    main()