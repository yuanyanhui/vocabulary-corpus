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
DROP TABLE IF EXISTS vocabularies;
DROP TABLE IF EXISTS definitions;
DROP TABLE IF EXISTS headwords;
DROP TABLE IF EXISTS headword_vocabularies;
DROP INDEX IF EXISTS idx_headword_vocabularies_headword_id;
DROP INDEX IF EXISTS idx_headword_vocabularies_vocabulary_id;

CREATE TABLE vocabularies (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(255)
);

CREATE TABLE headwords (
    id SERIAL PRIMARY KEY,
    word VARCHAR(255) UNIQUE NOT NULL,
    american_phonetics VARCHAR(255),
    british_phonetics VARCHAR(255)
);

CREATE TABLE headword_vocabularies (
    id INTEGER PRIMARY KEY,
    headword_id INTEGER NOT NULL,
    vocabulary_id INTEGER NOT NULL,
    FOREIGN KEY (headword_id) REFERENCES headwords(id) ON DELETE CASCADE,
    FOREIGN KEY (vocabulary_id) REFERENCES vocabularies(id) ON DELETE CASCADE,
    UNIQUE(headword_id, vocabulary_id)  -- Prevents duplicate relationships
);

CREATE INDEX idx_headword_vocabularies_headword_id ON headword_vocabularies(headword_id);
CREATE INDEX idx_headword_vocabularies_vocabulary_id ON headword_vocabularies(vocabulary_id);

CREATE TABLE definitions (
    id SERIAL PRIMARY KEY,
    headword_id INTEGER REFERENCES headwords(id) ON DELETE CASCADE,
    part_of_speech VARCHAR(255),
    definition TEXT,
    chinese_translation TEXT
);
\n\n"""

def main():
    data_dir = 'data'
    dump_file = 'dump_simple.sql'

    json_files = sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.json')])

    with open(dump_file, 'w', encoding='utf-8') as f:
        f.write("--\n-- PostgreSQL database dump\n--\n\n")
        f.write(get_table_definitions())

        # populate vocabularies table
        f.write('''INSERT INTO vocabularies (id, name, description) VALUES
                (1, 'high_school', 'high school'),
                (2, 'cet6', 'CET6'),
                (3, 'middle_school', 'middle school'),
                (4, 'toefl', 'TOEFL'),
                (5, 'grad_entrance', 'graduate entrance exam'),
                (6, 'sat', 'SAT'),
                (7, 'cet4', 'CET4'),
                (8, 'middle_school_1600', 'middle school 1600');\n'''
        )

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
                    'british_phonetics': escape_sql_string(data.get('phonetics', {}).get('british')),
                }
                f.write(f"INSERT INTO headwords (id, word, american_phonetics, british_phonetics) VALUES ({headword_id}, {word_data['word']}, {word_data['american_phonetics']}, {word_data['british_phonetics']});\n")

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
