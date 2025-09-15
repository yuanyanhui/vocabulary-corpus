import csv
from collections import Counter

def find_duplicate_words(input_file, output_file):
    """
    Reads a text file, finds duplicate words (case-insensitive) and their frequencies,
    and saves the result to a CSV file.
    """
    try:
        with open(input_file, 'r') as f:
            # Convert to lowercase and strip whitespace
            words = [line.strip().lower() for line in f]
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
        return

    word_counts = Counter(words)
    # Filter for words that appear more than once
    duplicates = {word: count for word, count in word_counts.items() if count > 1}

    if not duplicates:
        print("No duplicate words found.")
        return

    try:
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['word', 'frequency'])
            # Sort by frequency (descending), then by word (ascending)
            for word, count in sorted(duplicates.items(), key=lambda item: (-item[1], item[0])):
                writer.writerow([word, count])
        print(f"Duplicate words and their frequencies have been saved to '{output_file}'")
    except IOError:
        print(f"Error: Could not write to the file '{output_file}'.")

if __name__ == '__main__':
    find_duplicate_words('word.txt', 'duplicated_words.csv')
