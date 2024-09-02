package common

import (
	"encoding/csv"
	"fmt"
	"os"
)

func ParseCSV(filename string) ([][]string, error) {
	// Open the CSV file
	file, err := os.Open(filename)
	if err != nil {
		return nil, fmt.Errorf("could not open file: %v", err)
	}
	defer file.Close()

	// Create a new CSV reader
	reader := csv.NewReader(file)

	// Read all records from the file
	records, err := reader.ReadAll()
	if err != nil {
		return nil, fmt.Errorf("could not read csv: %v", err)
	}

	return records, nil
}
