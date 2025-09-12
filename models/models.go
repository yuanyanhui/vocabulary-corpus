package models

import "github.com/lib/pq"

// Vocab corresponds to the "vocabularies" table
type Vocabulary struct {
    ID          int         `gorm:"primaryKey"`
    Name        string      `gorm:"unique;not null"`
    Description string      `gorm:"default:''"`
    Headwords   []*Headword `gorm:"many2many:headword_vocabs;"`
}

// Headword corresponds to the 'headwords' table
type Headword struct {
    ID             int             `json:"id" gorm:"primaryKey"`
    Word           string          `json:"word" gorm:"unique;not null"`
    SyllablesCount *int            `json:"syllables_count"`
    SyllablesList  pq.StringArray  `json:"syllables_list" gorm:"type:text[]"`
    Pronunciation  *string         `json:"pronunciation"`
    Frequency      *float64        `json:"frequency"`
    Entries        []Entry         `json:"entries" gorm:"foreignKey:HeadwordID"`
    Vocabularies   []*Vocabulary   `gorm:"many2many:headword_vocabs;"`
}

// Entry corresponds to the 'entries' table
type Entry struct {
	ID                 int     `json:"id" gorm:"primaryKey"`
	HeadwordID         int     `json:"headword_id"`
	PartOfSpeech       *string `json:"part_of_speech"`
	Definition         *string `json:"definition"`
	ChineseTranslation *string `json:"chinese_translation"`
	Level              *string `json:"level"`
	Frequency          *string `json:"frequency"`
	Register           *string `json:"register"`
}
