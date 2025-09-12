import * as fs from 'fs';
import * as path from 'path';

const dataDir = path.join(__dirname, '../data');
const sqlFilePath = path.join(__dirname, '../dump.sql');

interface Entry {
  definition: string;
  partOfSpeech?: string;
  synonyms?: string[];
  typeOf?: string[];
  hasParts?: string[];
  instanceOf?: string[];
  also?: string[];
  antonyms?: string[];
  attribute?: string[];
  derivation?: string[];
  examples?: string[];
  hasCategories?: string[];
  hasInstances?: string[];
  hasMembers?: string[];
  hasSubstances?: string[];
  hasTypes?: string[];
  inCategory?: string[];
  inRegion?: string[];
  memberOf?: string[];
  pertainsTo?: string[];
  regionOf?: string[];
  seeAlso?: string[];
  similarTo?: string[];
  substanceOf?: string[];
  usageOf?: string[];
  verbGroup?: string[];
}

interface HeadwordData {
  word: string;
  entries?: Entry[];
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
  writeSql('DROP TABLE IF EXISTS synonyms CASCADE;');
  writeSql('DROP TABLE IF EXISTS type_of CASCADE;');
  writeSql('DROP TABLE IF EXISTS has_parts CASCADE;');
  writeSql('DROP TABLE IF EXISTS instance_of CASCADE;');
  writeSql('DROP TABLE IF EXISTS also CASCADE;');
  writeSql('DROP TABLE IF EXISTS antonyms CASCADE;');
  writeSql('DROP TABLE IF EXISTS attribute CASCADE;');
  writeSql('DROP TABLE IF EXISTS derivation CASCADE;');
  writeSql('DROP TABLE IF EXISTS examples CASCADE;');
  writeSql('DROP TABLE IF EXISTS has_categories CASCADE;');
  writeSql('DROP TABLE IF EXISTS has_instances CASCADE;');
  writeSql('DROP TABLE IF EXISTS has_members CASCADE;');
  writeSql('DROP TABLE IF EXISTS has_substances CASCADE;');
  writeSql('DROP TABLE IF EXISTS has_types CASCADE;');
  writeSql('DROP TABLE IF EXISTS in_category CASCADE;');
  writeSql('DROP TABLE IF EXISTS in_region CASCADE;');
  writeSql('DROP TABLE IF EXISTS member_of CASCADE;');
  writeSql('DROP TABLE IF EXISTS pertains_to CASCADE;');
  writeSql('DROP TABLE IF EXISTS region_of CASCADE;');
  writeSql('DROP TABLE IF EXISTS see_also CASCADE;');
  writeSql('DROP TABLE IF EXISTS similar_to CASCADE;');
  writeSql('DROP TABLE IF EXISTS substance_of CASCADE;');
  writeSql('DROP TABLE IF EXISTS usage_of CASCADE;');
  writeSql('DROP TABLE IF EXISTS verb_group CASCADE;');


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
      definition TEXT,
      part_of_speech VARCHAR(255)
    );
  `);

  writeSql(`
    CREATE TABLE headword_vocabs (
      headword_id INTEGER REFERENCES headwords(id) ON DELETE CASCADE,
      vocabulary_id INTEGER REFERENCES vocabularies(id) ON DELETE CASCADE,
      PRIMARY KEY (headword_id, vocabulary_id)
    );
  `);

  const createJunctionTable = (tableName: string) => {
    writeSql(`
      CREATE TABLE ${tableName} (
        entry_id INTEGER REFERENCES entries(id),
        value TEXT
      );
    `);
  };

  createJunctionTable('synonyms');
  createJunctionTable('type_of');
  createJunctionTable('has_parts');
  createJunctionTable('instance_of');
  createJunctionTable('also');
  createJunctionTable('antonyms');
  createJunctionTable('attribute');
  createJunctionTable('derivation');
  createJunctionTable('examples');
  createJunctionTable('has_categories');
  createJunctionTable('has_instances');
  createJunctionTable('has_members');
  createJunctionTable('has_substances');
  createJunctionTable('has_types');
  createJunctionTable('in_category');
  createJunctionTable('in_region');
  createJunctionTable('member_of');
  createJunctionTable('pertains_to');
  createJunctionTable('region_of');
  createJunctionTable('see_also');
  createJunctionTable('similar_to');
  createJunctionTable('substance_of');
  createJunctionTable('usage_of');
  createJunctionTable('verb_group');

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

      if (data.entries) {
        for (const entry of data.entries) {
          writeSql(`INSERT INTO entries (id, headword_id, definition, part_of_speech) VALUES (${entryId}, ${headwordId}, ${escapeSql(entry.definition)}, ${escapeSql(entry.partOfSpeech)});`);

          const insertIntoJunction = (tableName: string, values: string[] | undefined) => {
            if (values) {
              for (const value of values) {
                writeSql(`INSERT INTO ${tableName} (entry_id, value) VALUES (${entryId}, ${escapeSql(value)});`);
              }
            }
          };

          insertIntoJunction('synonyms', entry.synonyms);
          insertIntoJunction('type_of', entry.typeOf);
          insertIntoJunction('has_parts', entry.hasParts);
          insertIntoJunction('instance_of', entry.instanceOf);
          insertIntoJunction('also', entry.also);
          insertIntoJunction('antonyms', entry.antonyms);
          insertIntoJunction('attribute', entry.attribute);
          insertIntoJunction('derivation', entry.derivation);
          insertIntoJunction('examples', entry.examples);
          insertIntoJunction('has_categories', entry.hasCategories);
          insertIntoJunction('has_instances', entry.hasInstances);
          insertIntoJunction('has_members', entry.hasMembers);
          insertIntoJunction('has_substances', entry.hasSubstances);
          insertIntoJunction('has_types', entry.hasTypes);
          insertIntoJunction('in_category', entry.inCategory);
          insertIntoJunction('in_region', entry.inRegion);
          insertIntoJunction('member_of', entry.memberOf);
          insertIntoJunction('pertains_to', entry.pertainsTo);
  
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
