import os
import json
import csv
from collections import Counter

def process_json_words(data_directory, word_list_file, duplicates_file):
    """
    Reads all JSON files in a directory, extracts the 'word' from each,
    saves the full list to a text file, and saves any duplicate words
    and their frequencies to a CSV file.
    """
    words = []
    if not os.path.isdir(data_directory):
        print(f"Error: Directory '{data_directory}' not found.")
        return

    # 1. Read all JSON files and extract words
    for filename in sorted(os.listdir(data_directory)):
        if filename.endswith('.json'):
            filepath = os.path.join(data_directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'word' in data:
                        words.append(data['word'])
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not process file '{filepath}'. Error: {e}. Skipping.")

    if not words:
        print("No words found in the data directory.")
        return

    # 2. Save the compiled list to word_list.txt
    try:
        with open(word_list_file, 'w', encoding='utf-8') as f:
            for word in words:
                f.write(f"{word}\n")
        print(f"Successfully compiled {len(words)} words into '{word_list_file}'.")
    except IOError as e:
        print(f"Error: Could not write to '{word_list_file}'. Error: {e}")
        return

    # 3. Find and save duplicates
    # Case-insensitive counting
    lower_words = [word.lower() for word in words]
    word_counts = Counter(lower_words)
    duplicates = {word: count for word, count in word_counts.items() if count > 1}

    if not duplicates:
        print("No duplicate words found in the compiled list.")
        return

    try:
        with open(duplicates_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['word', 'frequency'])
            # Sort by frequency (descending), then by word (ascending)
            for word, count in sorted(duplicates.items(), key=lambda item: (-item[1], item[0])):
                writer.writerow([word, count])
        print(f"Found {len(duplicates)} duplicate words. Their frequencies have been saved to '{duplicates_file}'")
    except IOError as e:
        print(f"Error: Could not write to '{duplicates_file}'. Error: {e}")


if __name__ == '__main__':
    process_json_words('data', 'word_list.txt', 'word_list_duplicates.csv')
