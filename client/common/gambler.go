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
