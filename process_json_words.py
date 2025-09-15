import os
import json
import csv
from collections import defaultdict

def process_json_words(data_directory, word_list_file, duplicates_file):
    """
    Reads all JSON files in a directory, extracts the 'word' from each,
    saves the full list to a text file, and saves any duplicate words,
    their frequencies, and their source filenames to a CSV file.
    """
    if not os.path.isdir(data_directory):
        print(f"Error: Directory '{data_directory}' not found.")
        return

    word_details = defaultdict(lambda: {'casing': '', 'files': []})
    all_words_in_order = []

    # 1. Read all JSON files and extract words and filenames
    for filename in sorted(os.listdir(data_directory)):
        if filename.endswith('.json'):
            filepath = os.path.join(data_directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'word' in data:
                        original_word = data['word']
                        lower_word = original_word.lower()
                        all_words_in_order.append(original_word)

                        # Store the original casing the first time we see the word
                        if not word_details[lower_word]['casing']:
                            word_details[lower_word]['casing'] = original_word

                        word_details[lower_word]['files'].append(filename)

            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not process file '{filepath}'. Error: {e}. Skipping.")

    if not all_words_in_order:
        print("No words found in the data directory.")
        return

    # 2. Save the compiled list to word_list.txt
    try:
        with open(word_list_file, 'w', encoding='utf-8') as f:
            for word in all_words_in_order:
                f.write(f"{word}\n")
        print(f"Successfully compiled {len(all_words_in_order)} words into '{word_list_file}'.")
    except IOError as e:
        print(f"Error: Could not write to '{word_list_file}'. Error: {e}")
        return

    # 3. Find and save duplicates
    duplicates = {
        details['casing']: {
            'frequency': len(details['files']),
            'filenames': ", ".join(sorted(details['files']))
        }
        for word, details in word_details.items() if len(details['files']) > 1
    }

    if not duplicates:
        print("No duplicate words found in the compiled list.")
        return

    try:
        with open(duplicates_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['word', 'frequency', 'filenames'])
            # Sort by frequency (descending), then by word (ascending)
            for word, details in sorted(duplicates.items(), key=lambda item: (-item[1]['frequency'], item[0])):
                writer.writerow([word, details['frequency'], details['filenames']])
        print(f"Found {len(duplicates)} duplicate words. Their details have been saved to '{duplicates_file}'")
    except IOError as e:
        print(f"Error: Could not write to '{duplicates_file}'. Error: {e}")


if __name__ == '__main__':
    process_json_words('data', 'word_list.txt', 'word_list_duplicates.csv')
