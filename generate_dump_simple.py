import json
import os

def escape_sql_string(value):
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    # Escape single quotes for SQL
    return "'" + str(value).replace("'", "''") + "'"

def get_table_definitions():
    return """
DROP TABLE IF EXISTS definitions;
DROP TABLE IF EXISTS headwords;

CREATE TABLE headwords (
    id INTEGER PRIMARY KEY,
    word VARCHAR(255) UNIQUE NOT NULL,
    american_phonetics VARCHAR(255),
);

CREATE TABLE definitions (
    id SERIAL PRIMARY KEY,
    headword_id INTEGER REFERENCES headwords(id) ON DELETE CASCADE,
    part_of_speech VARCHAR(255),
    definition TEXT,
    chinese_translation TEXT,
);
\n\n"""

def main():
    data_dir = 'data'
    dump_file = 'dump_simple.sql'

    json_files = sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.json')])

    with open(dump_file, 'w', encoding='utf-8') as f:
        f.write("--\n-- PostgreSQL database dump\n--\n\n")
        f.write(get_table_definitions())

        # Process each JSON file
        for headword_id, json_file in enumerate(json_files, 1):
            with open(json_file, 'r', encoding='utf-8') as jf:
                try:
                    data = json.load(jf)
                except json.JSONDecodeError:
                    print(f"Skipping invalid JSON file: {json_file}")
                    continue

                # Insert into headwords table
                word_data = {
                    'word': escape_sql_string(data.get('word')),
                    'american_phonetics': escape_sql_string(data.get('phonetics', {}).get('american')),
                }
                f.write(f"INSERT INTO headwords (id, word, american_phonetics) VALUES ({headword_id}, {word_data['word']}, {word_data['american_phonetics']});\n")

                # Insert into definitions table
                if data.get('definitions'):
                    for definition in data['definitions']:
                        def_data = {
                            'part_of_speech': escape_sql_string(definition.get('partOfSpeech')),
                            'definition': escape_sql_string(definition.get('definition')),
                            'chinese_translation': escape_sql_string(definition.get('chineseTranslation')),
                        }
                        f.write(f"INSERT INTO definitions (headword_id, part_of_speech, definition, chinese_translation) VALUES ({headword_id}, {def_data['part_of_speech']}, {def_data['definition']}, {def_data['chinese_translation']});\n")

if __name__ == "__main__":
    main()
