package common

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"strconv"
)

type Gambler struct {
	Name      string
	LastName  string
	DNI       uint32
	Birth     string
	BetNumber uint32
}

// NewGambler Creates a new gambler with the given parameters
// and returns a pointer to the created gambler
func NewGambler(name string, lastName string, dni string, birth string, betNumber string) (*Gambler, error) {

	dniInt, err := strconv.Atoi(dni)
	if err != nil {
		return nil, err
	}

	betNumberInt, err := strconv.Atoi(betNumber)
	if err != nil {
		return nil, err
	}

	return &Gambler{name, lastName, uint32(dniInt), birth, uint32(betNumberInt)}, nil
}

// SerializeBet Serializes the bet of the gambler and returns the serialized
// bet as a byte slice. The serialized bet is in the following format:
// HouseID (1 byte) | Name (20 bytes) | LastName (20 bytes) | DNI (4 bytes) | Birth (10 bytes) | BetNumber (4 bytes)
func (g *Gambler) SerializeBet(houseId uint8) ([]byte, error) {
	buffer := new(bytes.Buffer)

	if err := binary.Write(buffer, binary.BigEndian, houseId); err != nil {
		log.Debugf("Error writing HouseID: %v", err)
		return nil, err
	}

	if err := writeStringAndPadd(buffer, g.Name, NameMaxLenght); err != nil {
		log.Debugf("Error writing Name: %v", err)
		return nil, err
	}

	if err := writeStringAndPadd(buffer, g.LastName, LastNameMaxLenght); err != nil {
		log.Debugf("Error writing LastName: %v", err)
		return nil, err
	}

	if err := binary.Write(buffer, binary.BigEndian, g.DNI); err != nil {
		log.Debugf("Error writing DNI: %v", err)
		return nil, err
	}

	if err := writeStringAndPadd(buffer, g.Birth, BirthMaxLenght); err != nil {
		log.Debugf("Error writing Birth: %v", err)
		return nil, err
	}

	if err := binary.Write(buffer, binary.BigEndian, g.BetNumber); err != nil {
		log.Debugf("Error writing BetNumber: %v", err)
		return nil, err
	}

	return buffer.Bytes(), nil
}

// DeserializeGambleStatus Deserializes the response from the server and returns
// the DNI, bet number and success status of the gamble. The response is in the
// following format: DNI (4 bytes) | BetNumber (4 bytes) | StatusCode (1 byte)
func DeserializeGambleStatus(response []byte) (uint32, uint32, bool, error) {

	var dni uint32
	var betNumber uint32
	var statusCode uint8

	buffer := bytes.NewBuffer(response)
	if err := binary.Read(buffer, binary.BigEndian, &dni); err != nil {
		return 0, 0, false, err
	}
	if err := binary.Read(buffer, binary.BigEndian, &betNumber); err != nil {
		return 0, 0, false, err
	}
	if err := binary.Read(buffer, binary.BigEndian, &statusCode); err != nil {
		return 0, 0, false, err
	}

	success := statusCode == 1
	return dni, betNumber, success, nil
}

// writeStringAndPadd Writes a string to the buffer and fills the remaining space
// with zeros. The length parameter indicates the maximum length of the string.
// If the string is longer than the maximum length, an error is returned.
func writeStringAndPadd(buffer *bytes.Buffer, str string, length int) error {
	data := []byte(str)
	if len(data) > length {
		return fmt.Errorf("string length exceeds maximum allowed length")
	}
	// Write data an fill with zeros
	buffer.Write(data)
	buffer.Write(make([]byte, length-len(data)))
	return nil
}
