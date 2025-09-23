package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
)

// This struct is for the final output
type WordExample struct {
	Word     string   `json:"word"`
	Examples []string `json:"examples"`
}

// This struct is for parsing the input JSON files
type InputExample struct {
	Sentence string `json:"sentence"`
}

type WordData struct {
	Word     string         `json:"word"`
	Examples []InputExample `json:"examples"`
}

func main() {
	wordsFile, err := os.Open("words_5000.txt")
	if err != nil {
		fmt.Printf("Error opening words file: %v\n", err)
		return
	}
	defer wordsFile.Close()

	var words []string
	scanner := bufio.NewScanner(wordsFile)
	for scanner.Scan() {
		words = append(words, scanner.Text())
	}

	if err := scanner.Err(); err != nil {
		fmt.Printf("Error reading words file: %v\n", err)
		return
	}

	var wordExamples []WordExample
	var missingWords []string

	dataDir := "data"

	for _, word := range words {
		jsonPath := filepath.Join(dataDir, word+".json")
		if _, err := os.Stat(jsonPath); os.IsNotExist(err) {
			missingWords = append(missingWords, word)
			continue
		}

		jsonData, err := ioutil.ReadFile(jsonPath)
		if err != nil {
			fmt.Printf("Error reading json file %s: %v\n", jsonPath, err)
			continue
		}

		var data WordData
		err = json.Unmarshal(jsonData, &data)
		if err != nil {
			fmt.Printf("Error unmarshalling json file %s: %v\n", jsonPath, err)
			continue
		}

		var sentences []string
		if data.Examples != nil {
			for _, example := range data.Examples {
				sentences = append(sentences, example.Sentence)
			}
		}

		wordExamples = append(wordExamples, WordExample{
			Word:     data.Word,
			Examples: sentences,
		})
	}

	// Write word_examples.json
	outputJson, err := json.MarshalIndent(wordExamples, "", "  ")
	if err != nil {
		fmt.Printf("Error marshalling output json: %v\n", err)
		return
	}
	err = ioutil.WriteFile("word_examples.json", outputJson, 0644)
	if err != nil {
		fmt.Printf("Error writing word_examples.json: %v\n", err)
		return
	}

	// Write missing_words.txt
	missingFile, err := os.Create("missing_words.txt")
	if err != nil {
		fmt.Printf("Error creating missing_words.txt: %v\n", err)
		return
	}
	defer missingFile.Close()

	writer := bufio.NewWriter(missingFile)
	for _, word := range missingWords {
		_, err := writer.WriteString(word + "\n")
		if err != nil {
			fmt.Printf("Error writing to missing_words.txt: %v\n", err)
			return
		}
	}
	writer.Flush()

	fmt.Println("Processing complete.")
}
