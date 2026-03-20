# process_words.py 
import os
import json
import time
from tqdm import tqdm
from google import genai
from google.genai import types

from openai import OpenAI

SYSTEM_PROMPT = "You are an expert linguist and JSON data processor."
PROCESSED_FILES_RECORD = "processed_files.txt"
SOURCE_DIR = "source"
UPDATED_DIR = "updated_nim"

NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_NIM_MODEL = "qwen/qwen3.5-397b-a17b" # "minimaxai/minimax-m2.5" "nvidia/nemotron-3-super-120b-a12b" "qwen/qwen3.5-397b-a17b" "z-ai/glm5"  "moonshotai/kimi-k2.5"
nvidia_client = OpenAI(base_url=NVIDIA_NIM_BASE_URL, api_key=os.environ.get("NVIDIA_API_KEY"))

CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
CEREBRAS_MODEL = "qwen-3-235b-a22b-instruct-2507" # "zai-glm-4.7" 
# cerebras_client = OpenAI(base_url=CEREBRAS_BASE_URL, api_key=os.environ.get("CEREBRAS_API_KEY"))

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "openai/gpt-oss-120b" 
# groq_client = OpenAI(base_url=GROQ_BASE_URL, api_key=os.environ.get("GROQ_API_KEY"))


def generate_batch_prompt(words: list[dict]) -> str:
    """Creates a highly structured user prompt for the Gemini API to remap dictionary examples."""
    
    # Ensure the input JSON is formatted nicely for the LLM to read, 
    # and keep Unicode characters (like Chinese) intact.
    input_json_str = json.dumps(words, indent=2, ensure_ascii=False)

    return f'''

    ### Task
    Your objective is to restructure a JSON array of dictionary entries. 
    Currently, the "examples" field is at the root level of each dictionary entry. You must analyze the grammatical usage and semantic meaning of each sentence in the "examples" list and move it inside the "definitions" list, placing it under the specific definition it best illustrates.

    ### Rules
    1. **Grammatical and Semantic Matching:** Read each example sentence carefully. Determine both the context and the part of speech (POS) of the target word as it is used in the sentence. Match the example to the definition where *both* the meaning and the `partOfSpeech` align. 
       * *Clue:* If a word like "battle" is used as a verb in the example sentence, it MUST be mapped to a definition where the `partOfSpeech` is "verb", not "noun".
    2. **Move, Do Not Copy:** Remove the "examples" array from the root level and nest the examples inside the corresponding "definitions" object. If a definition has no matching examples, assign it an empty array: `"examples": []`.
    3. **Preserve Content:** Do NOT alter, add, or remove any original text, definitions, or translations. Only change the JSON structure.
    4. **Complete Mapping:** ALL words and their definitions in the json array must be properly mapped.
    5. **Valid JSON Only:** Your output MUST be a single, valid JSON array including all entries. Do not include introductory text, conversational filler, or markdown formatting outside of the JSON block.
   

    ### Example

    **Input Structure:**
    ```json
    {{
      "word": "battle",
      "definitions": [
        {{
          "partOfSpeech": "noun",
          "definition": "A fight or conflict between armed forces, especially in a war, or a prolonged struggle against an opponent or obstacle.",
          "chineseTranslation": "战斗；战役；斗争"
        }},
        {{
          "partOfSpeech": "verb",
          "definition": "To engage in a fight or struggle against someone or something.",
          "chineseTranslation": "作战；斗争"
        }},
        {{
          "partOfSpeech": "noun",
          "definition": "A vigorous contest or competition, often metaphorical, such as in sports or business.",
          "chineseTranslation": "激烈的竞争；较量"
        }}
      ],
      "examples": [
        {{
          "sentence": "The Battle of Waterloo marked the end of Napoleon's rule in Europe.",
          "translation": "滑铁卢战役标志着拿破仑在欧洲统治的结束。"
        }},
        {{
          "sentence": "She battles daily with anxiety to maintain her mental health.",
          "translation": "她每天都在与焦虑作斗争，以维持心理健康。"
        }},
        {{
          "sentence": "In the business world, companies often battle for market share.",
          "translation": "在商业世界中，公司经常为市场份额而竞争。"
        }},
        {{
          "sentence": "The team battled through injuries to win the championship.",
          "translation": "球队克服伤病赢得了冠军。"
        }}
      ]
    }}
    ```

    **Target Output Structure:**
    ```json
    {{
      "word": "battle",
      "definitions": [
        {{
          "partOfSpeech": "noun",
          "definition": "A fight or conflict between armed forces, especially in a war, or a prolonged struggle against an opponent or obstacle.",
          "chineseTranslation": "战斗；战役；斗争",
          "examples": [
            {{
              "sentence": "The Battle of Waterloo marked the end of Napoleon's rule in Europe.",
              "translation": "滑铁卢战役标志着拿破仑在欧洲统治的结束。"
            }}
          ]
        }},
        {{
          "partOfSpeech": "verb",
          "definition": "To engage in a fight or struggle against someone or something.",
          "chineseTranslation": "作战；斗争",
          "examples": [
            {{
              "sentence": "She battles daily with anxiety to maintain her mental health.",
              "translation": "她每天都在与焦虑作斗争，以维持心理健康。"
            }},
            {{
              "sentence": "In the business world, companies often battle for market share.",
              "translation": "在商业世界中，公司经常为市场份额而竞争。"
            }},
            {{
              "sentence": "The team battled through injuries to win the championship.",
              "translation": "球队克服伤病赢得了冠军。"
            }}
          ]
        }},
        {{
          "partOfSpeech": "noun",
          "definition": "A vigorous contest or competition, often metaphorical, such as in sports or business.",
          "chineseTranslation": "激烈的竞争；较量",
          "examples": []
        }}
      ]
    }}
    ```

    ### Data to Process
    Please process the following JSON array according to the rules and structure above:

    ```json
    {input_json_str}
    ```
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
            thinking_level="high"
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


def openai_generate(client: OpenAI, model: str, user_message: str, system_prompt: str = "") -> str:
    print(f"Sending request to {model}...")
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})
 
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=56320, # 56k tokens
        temperature=1.0,
        stream=False,
        # Force the model to output a valid JSON object
        response_format={"type": "json_object"},
        # extra_body={"chat_template_kwargs": {"enable_thinking": True, "clear_thinking": False}},
    )

    reasoning = getattr(response.choices[0].message, 'reasoning_content', None) 
    print(reasoning if reasoning else "(No reasoning trace returned)")

    return response.choices[0].message.content


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
            updated_words = openai_generate(nvidia_client, NVIDIA_NIM_MODEL, prompt, system_prompt=SYSTEM_PROMPT)
            # updated_words = openai_generate(groq_client, GROQ_MODEL, prompt, system_prompt=SYSTEM_PROMPT)
            
            # save the updated words to the "updated" directory with the same filename
            with open(updated_path, "w", encoding='utf-8') as f:
                json.dump(json.loads(updated_words), f, ensure_ascii=False, indent=2)

            # Record the file as successfully processed
            # save_processed_file(filename)

        except json.JSONDecodeError:
            tqdm.write(f"\nWarning: Failed to decode JSON for file '{filename}'. Response from API may be invalid.")
            break
        except Exception as e:
            tqdm.write(f"\nAn unexpected error occurred for file '{filename}': {e}")
            break

        # Rate limiting: Sleep between API calls
        time.sleep(5)

        break  # Remove this break to process all files


if __name__ == "__main__":
    main()