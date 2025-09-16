package models

import "github.com/lib/pq"

// Vocab corresponds to the "vocabularies" table
type Vocabulary struct {
    ID          int         `gorm:"primaryKey"`
    Name        string      `gorm:"unique;not null"`
    Description string      `gorm:"default:''"`
    Headwords   []*Headword `gorm:"many2many:headword_vocabularies;"`
}

// Headword corresponds to the 'headwords' table
type Headword struct {
    ID                 int             `json:"id" gorm:"primaryKey"`
    Word               string          `json:"word" gorm:"unique;not null"`
    AmericanPhonetics  *string         `json:"american_phonetics"`
    BritishPhonetics   *string         `json:"british_phonetics"`
    Entries            []Definition    `json:"entries" gorm:"foreignKey:HeadwordID"`
    Vocabularies       []*Vocabulary   `gorm:"many2many:headword_vocabularies;"`
}

// Definition corresponds to the 'definitions' table
type Definition struct {
	ID                 int     `json:"id" gorm:"primaryKey"`
	HeadwordID         int     `json:"headword_id"`
	PartOfSpeech       *string `json:"part_of_speech"`
	Definition         *string `json:"definition"`
	ChineseTranslation *string `json:"chinese_translation"`
}

func (Definition) TableName() string {
	return "definitions"
}
