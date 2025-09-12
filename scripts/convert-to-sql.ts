import * as fs from 'fs';
import * as path from 'path';

const dataDir = path.join(__dirname, '../data');
const sqlFilePath = path.join(__dirname, '../dump.sql');

interface Definition {
  partOfSpeech: string;
  definition: string;
  chineseTranslation: string;
  level: string;
  frequency: string;
  register: string;
}

interface HeadwordData {
  word: string;
  definitions?: Definition[];
  syllables?: {
    count: number;
    list: string[];
  };
  pronunciation?: {
    all: string;
  };
  frequency?: number;
}

const writeStream = fs.createWriteStream(sqlFilePath);

const writeSql = (sql: string) => {
  writeStream.write(sql + '\n');
};

const escapeSql = (str: string | number | null | undefined): string => {
    if (str === null || str === undefined) {
        return 'NULL';
    }
    if (typeof str === 'number') {
        return str.toString();
    }
    return "'" + str.toString().replace(/'/g, "''") + "'";
};

const main = async () => {
  // Schema
  writeSql('DROP TABLE IF EXISTS vocabularies CASCADE;');
  writeSql('DROP TABLE IF EXISTS headword_vocabs CASCADE;');
  writeSql('DROP TABLE IF EXISTS headwords CASCADE;');
  writeSql('DROP TABLE IF EXISTS entries CASCADE;');

  writeSql(`
    CREATE TABLE headwords (
      id SERIAL PRIMARY KEY,
      word VARCHAR(255) UNIQUE NOT NULL,
      syllables_count INTEGER,
      syllables_list TEXT[],
      pronunciation VARCHAR(255),
      frequency REAL
    );
  `);

  writeSql(`
    CREATE TABLE vocabularies (
      id SERIAL PRIMARY KEY,
      name VARCHAR(255) UNIQUE NOT NULL,
      description TEXT DEFAULT ''
    );
  `);

  writeSql(`
    CREATE TABLE entries (
      id SERIAL PRIMARY KEY,
      headword_id INTEGER REFERENCES headwords(id),
      part_of_speech VARCHAR(255),
      definition TEXT,
      chinese_translation TEXT,
      level VARCHAR(255),
      frequency VARCHAR(255),
      register VARCHAR(255)
    );
  `);

  writeSql(`
    CREATE TABLE headword_vocabs (
      headword_id INTEGER REFERENCES headwords(id) ON DELETE CASCADE,
      vocabulary_id INTEGER REFERENCES vocabularies(id) ON DELETE CASCADE,
      PRIMARY KEY (headword_id, vocabulary_id)
    );
  `);

  writeSql(`INSERT INTO vocabularies (id, name, description) VALUES (1, 'Default', 'Default vocabulary');`);

  const files = fs.readdirSync(dataDir);
  let headwordId = 1;
  let entryId = 1;

  for (const file of files) {
    if (path.extname(file) === '.json') {
      const filePath = path.join(dataDir, file);
      const content = fs.readFileSync(filePath, 'utf-8');
      const data: HeadwordData = JSON.parse(content);

      const syllablesList = data.syllables ? `{${data.syllables.list.map((s: string) => `"${s.replace(/'/g, "''")}"`).join(',')}}` : 'NULL';

      writeSql(`INSERT INTO headwords (id, word, syllables_count, syllables_list, pronunciation, frequency) VALUES (${headwordId}, ${escapeSql(data.word)}, ${data.syllables ? data.syllables.count : 'NULL'}, ${syllablesList}, ${escapeSql(data.pronunciation?.all)}, ${escapeSql(data.frequency)});`);
      writeSql(`INSERT INTO headword_vocabs (headword_id, vocabulary_id) VALUES (${headwordId}, 1);`);

      if (data.definitions) {
        for (const definition of data.definitions) {
          writeSql(`INSERT INTO entries (id, headword_id, part_of_speech, definition, chinese_translation, level, frequency, register) VALUES (${entryId}, ${headwordId}, ${escapeSql(definition.partOfSpeech)}, ${escapeSql(definition.definition)}, ${escapeSql(definition.chineseTranslation)}, ${escapeSql(definition.level)}, ${escapeSql(definition.frequency)}, ${escapeSql(definition.register)});`);
          entryId++;
        }
      }
      headwordId++;
    }
  }

  writeStream.end();
  console.log('SQL dump created at dump.sql');
};

main().catch(console.error);
