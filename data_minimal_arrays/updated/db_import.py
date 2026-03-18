import os
import json
import psycopg2
import psycopg2.extras # Needed for batch execution

from pathlib import Path

DB_CONNECTION_STRING = os.environ.get("DATABASE_URL")

def process_examples(json_file):
    conn = None
    cursor = None # FIX 1: Prevent UnboundLocalError for cursor
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()

        # FIX 2: Added a UNIQUE constraint to prevent duplicate examples
        create_table_query = """
            CREATE TABLE IF NOT EXISTS examples (
                id SERIAL PRIMARY KEY,
                definition_id INTEGER NOT NULL,
                sentence TEXT,
                translation TEXT,
                CONSTRAINT unique_example UNIQUE(definition_id, sentence)
            );
        """
        cursor.execute(create_table_query)

        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file) 

        # We will collect all examples in a list to insert them at once
        examples_to_insert = []

        for entry in data:
            word = entry.get('word')
            definitions = entry.get('definitions', [])

            for def_item in definitions:
                part_of_speech = def_item.get('partOfSpeech')
                definition_text = def_item.get('definition')
                examples = def_item.get('examples', [])

                if not examples:
                    continue

                lookup_query = """
                    SELECT d.id 
                    FROM definitions d
                    JOIN headwords h ON d.headword_id = h.id
                    WHERE h.word = %s 
                      AND d.part_of_speech = %s 
                      AND d.definition = %s;
                """
                cursor.execute(lookup_query, (word, part_of_speech, definition_text))
                result = cursor.fetchone()

                if result:
                    definition_id = result[0]
                    # Add to our batch list instead of inserting immediately
                    for ex in examples:
                        examples_to_insert.append((
                            definition_id, 
                            ex.get('sentence'), 
                            ex.get('translation')
                        ))
                else:
                    print(f"WARNING: Could not find definition in DB for: {word} - '{definition_text}'")

        # FIX 3: Batch execution & ON CONFLICT DO NOTHING
        if examples_to_insert:
            insert_query = """
                INSERT INTO examples (definition_id, sentence, translation)
                VALUES (%s, %s, %s)
                ON CONFLICT (definition_id, sentence) DO NOTHING;
            """
            # execute_batch is much faster than running cursor.execute() in a loop
            psycopg2.extras.execute_batch(cursor, insert_query, examples_to_insert)
            print(f"Processed {len(examples_to_insert)} examples for {json_file.name}.")

        conn.commit()
        print(f"Data import completed successfully for {json_file.name}.")
        return True

    except Exception as e:
        print(f"An error occurred while processing {json_file.name}: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        # Safely close cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    processed_folder = Path('processed')
    processed_folder.mkdir(exist_ok=True)

    all_json_files = Path.cwd().glob('*.json')
    
    for json_file in all_json_files:
        success = process_examples(json_file)
        
        if success:
            try:
                destination = processed_folder / json_file.name
                json_file.rename(destination)
            except Exception as e:
                print(f"Failed to move file {json_file.name} to processed folder: {e}")
        else:
            print(f"Skipping move for {json_file.name} due to database errors.")
