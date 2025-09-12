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
    Vocabularies   []*Vocabulary    `gorm:"many2many:headword_vocabs;"`
}

// Entry corresponds to the 'entries' table
type Entry struct {
	ID            int      `json:"id" gorm:"primaryKey"`
	HeadwordID    int      `json:"headword_id"`
	Definition    *string  `json:"definition"`
	PartOfSpeech  *string  `json:"part_of_speech"`
	Synonyms      []StringValue `json:"synonyms" gorm:"foreignKey:EntryID"`
	TypeOf        []StringValue `json:"typeOf" gorm:"foreignKey:EntryID"`
	HasParts      []StringValue `json:"hasParts" gorm:"foreignKey:EntryID"`
	InstanceOf    []StringValue `json:"instanceOf" gorm:"foreignKey:EntryID"`
	Also          []StringValue `json:"also" gorm:"foreignKey:EntryID"`
	Antonyms      []StringValue `json:"antonyms" gorm:"foreignKey:EntryID"`
	Attribute     []StringValue `json:"attribute" gorm:"foreignKey:EntryID"`
	Derivation    []StringValue `json:"derivation" gorm:"foreignKey:EntryID"`
	Examples      []StringValue `json:"examples" gorm:"foreignKey:EntryID"`
	HasCategories []StringValue `json:"hasCategories" gorm:"foreignKey:EntryID"`
	HasInstances  []StringValue `json:"hasInstances" gorm:"foreignKey:EntryID"`
	HasMembers    []StringValue `json:"hasMembers" gorm:"foreignKey:EntryID"`
	HasSubstances []StringValue `json:"hasSubstances" gorm:"foreignKey:EntryID"`
	HasTypes      []StringValue `json:"hasTypes" gorm:"foreignKey:EntryID"`
	InCategory    []StringValue `json:"inCategory" gorm:"foreignKey:EntryID"`
	InRegion      []StringValue `json:"inRegion" gorm:"foreignKey:EntryID"`
	MemberOf      []StringValue `json:"memberOf" gorm:"foreignKey:EntryID"`
	PertainsTo    []StringValue `json:"pertainsTo" gorm:"foreignKey:EntryID"`
	RegionOf      []StringValue `json:"regionOf" gorm:"foreignKey:EntryID"`
	SeeAlso       []StringValue `json:"seeAlso" gorm:"foreignKey:EntryID"`
	SimilarTo     []StringValue `json:"similarTo" gorm:"foreignKey:EntryID"`
	SubstanceOf   []StringValue `json:"substanceOf" gorm:"foreignKey:EntryID"`
	UsageOf       []StringValue `json:"usageOf" gorm:"foreignKey:EntryID"`
	VerbGroup     []StringValue `json:"verbGroup" gorm:"foreignKey:EntryID"`
}

// StringValue is a generic struct for junction tables with a string value
type StringValue struct {
	ResultID int    `gorm:"primaryKey"`
	Value    string `gorm:"primaryKey"`
}

// TableName allows specifying table name dynamically for StringValue
func (s StringValue) TableName() string {
    // This is a placeholder. GORM's convention would be to name the table 'string_values'.
    // To use different tables like 'synonyms', 'antonyms', etc., you would need separate structs
    // or a more complex setup with dynamic table names, which GORM supports in various ways.
    // For simplicity, we'll assume a single table or that you'll create specific types for each junction table.
	return "string_values"
}
