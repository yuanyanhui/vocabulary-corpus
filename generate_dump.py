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
DROP TABLE IF EXISTS examples;
DROP TABLE IF EXISTS phrases;
DROP TABLE IF EXISTS definitions;
DROP TABLE IF EXISTS headwords;

CREATE TABLE headwords (
    id INTEGER PRIMARY KEY,
    word VARCHAR(255) UNIQUE NOT NULL,
    british_phonetics VARCHAR(255),
    american_phonetics VARCHAR(255),
    etymology JSONB,
    difficulty_analysis JSONB,
    semantic_relations JSONB,
    cultural_context JSONB,
    memory_aids JSONB,
    grammatical_info JSONB,
    metadata JSONB
);

CREATE TABLE definitions (
    id SERIAL PRIMARY KEY,
    headword_id INTEGER REFERENCES headwords(id) ON DELETE CASCADE,
    part_of_speech VARCHAR(255),
    definition TEXT,
    chinese_translation TEXT,
    level VARCHAR(255),
    frequency VARCHAR(255),
    register VARCHAR(255)
);

CREATE TABLE phrases (
    id SERIAL PRIMARY KEY,
    headword_id INTEGER REFERENCES headwords(id) ON DELETE CASCADE,
    phrase TEXT,
    meaning TEXT,
    example TEXT,
    example_translation TEXT,
    frequency VARCHAR(255)
);

CREATE TABLE examples (
    id SERIAL PRIMARY KEY,
    headword_id INTEGER REFERENCES headwords(id) ON DELETE CASCADE,
    sentence TEXT,
    translation TEXT,
    source VARCHAR(255),
    difficulty VARCHAR(255)
);
\n\n"""

def main():
    data_dir = 'data'
    dump_dir = 'sql_dumps'
    max_file_size = 10 * 1024 * 1024 # 10 MB

    if not os.path.exists(dump_dir):
        os.makedirs(dump_dir)

    json_files = sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.json')])

    file_index = 1
    current_size = 0
    f = None

    def open_new_file():
        nonlocal file_index, current_size, f
        if f:
            f.close()

        dump_file_path = os.path.join(dump_dir, f'dump_{file_index}.sql')
        f = open(dump_file_path, 'w', encoding='utf-8')

        f.write(f"--\n-- PostgreSQL database dump (Part {file_index})\n--\n\n")

        if file_index == 1:
            f.write(get_table_definitions())

        current_size = f.tell()
        file_index += 1
        return f

    f = open_new_file()

    # Process each JSON file
    for headword_id, json_file in enumerate(json_files, 1):
        with open(json_file, 'r', encoding='utf-8') as jf:
            try:
                data = json.load(jf)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON file: {json_file}")
                continue

            lines = []
            # Insert into headwords table
            word_data = {
                'word': escape_sql_string(data.get('word')),
                'british_phonetics': escape_sql_string(data.get('phonetics', {}).get('british')),
                'american_phonetics': escape_sql_string(data.get('phonetics', {}).get('american')),
                'etymology': escape_sql_string(json.dumps(data.get('etymology'), ensure_ascii=False)),
                'difficulty_analysis': escape_sql_string(json.dumps(data.get('difficultyAnalysis'), ensure_ascii=False)),
                'semantic_relations': escape_sql_string(json.dumps(data.get('semanticRelations'), ensure_ascii=False)),
                'cultural_context': escape_sql_string(json.dumps(data.get('culturalContext'), ensure_ascii=False)),
                'memory_aids': escape_sql_string(json.dumps(data.get('memoryAids'), ensure_ascii=False)),
                'grammatical_info': escape_sql_string(json.dumps(data.get('grammaticalInfo'), ensure_ascii=False)),
                'metadata': escape_sql_string(json.dumps(data.get('metadata'), ensure_ascii=False))
            }
            lines.append(f"INSERT INTO headwords (id, word, british_phonetics, american_phonetics, etymology, difficulty_analysis, semantic_relations, cultural_context, memory_aids, grammatical_info, metadata) VALUES ({headword_id}, {word_data['word']}, {word_data['british_phonetics']}, {word_data['american_phonetics']}, {word_data['etymology']}, {word_data['difficulty_analysis']}, {word_data['semantic_relations']}, {word_data['cultural_context']}, {word_data['memory_aids']}, {word_data['grammatical_info']}, {word_data['metadata']});\n")

            # Insert into definitions table
            if data.get('definitions'):
                for definition in data['definitions']:
                    def_data = {
                        'part_of_speech': escape_sql_string(definition.get('partOfSpeech')),
                        'definition': escape_sql_string(definition.get('definition')),
                        'chinese_translation': escape_sql_string(definition.get('chineseTranslation')),
                        'level': escape_sql_string(definition.get('level')),
                        'frequency': escape_sql_string(definition.get('frequency')),
                        'register': escape_sql_string(definition.get('register'))
                    }
                    lines.append(f"INSERT INTO definitions (headword_id, part_of_speech, definition, chinese_translation, level, frequency, register) VALUES ({headword_id}, {def_data['part_of_speech']}, {def_data['definition']}, {def_data['chinese_translation']}, {def_data['level']}, {def_data['frequency']}, {def_data['register']});\n")

            # Insert into phrases table
            if data.get('phrases'):
                for phrase in data['phrases']:
                    phrase_data = {
                        'phrase': escape_sql_string(phrase.get('phrase')),
                        'meaning': escape_sql_string(phrase.get('meaning')),
                        'example': escape_sql_string(phrase.get('example')),
                        'example_translation': escape_sql_string(phrase.get('exampleTranslation')),
                        'frequency': escape_sql_string(phrase.get('frequency'))
                    }
                    lines.append(f"INSERT INTO phrases (headword_id, phrase, meaning, example, example_translation, frequency) VALUES ({headword_id}, {phrase_data['phrase']}, {phrase_data['meaning']}, {phrase_data['example']}, {phrase_data['example_translation']}, {phrase_data['frequency']});\n")

            # Insert into examples table
            if data.get('examples'):
                for example in data['examples']:
                    example_data = {
                        'sentence': escape_sql_string(example.get('sentence')),
                        'translation': escape_sql_string(example.get('translation')),
                        'source': escape_sql_string(example.get('source')),
                        'difficulty': escape_sql_string(example.get('difficulty'))
                    }
                    lines.append(f"INSERT INTO examples (headword_id, sentence, translation, source, difficulty) VALUES ({headword_id}, {example_data['sentence']}, {example_data['translation']}, {example_data['source']}, {example_data['difficulty']});\n")

            block = "".join(lines)
            block_size = len(block.encode('utf-8'))

            if current_size + block_size > max_file_size and headword_id > 1:
                f = open_new_file()

            f.write(block)
            current_size += block_size

    if f:
        f.close()

if __name__ == "__main__":
    main()
