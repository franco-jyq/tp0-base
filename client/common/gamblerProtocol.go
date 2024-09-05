package common

import (
	"bytes"
	"encoding/binary"
	"fmt"
)

const (
	HouseIDLenght        = 1
	NameMaxLenght        = 30
	LastNameMaxLenght    = 30
	DNIMaxLenght         = 4
	BirthMaxLenght       = 10
	BetNumberMaxLenght   = 4
	ServerResponseLength = 9
)

type GamblerProtocol struct {
	HouseID   uint8
	Name      string
	LastName  string
	DNI       uint32
	Birth     string
	BetNumber uint32
}

// NewGamblerProtocol creates a new gambler protocol with the given parameters.
// It returns a pointer to the created gambler protocol.
func NewGamblerProtocol(houseId uint8, name string, lastName string, dni uint32, birth string, betNum uint32) *GamblerProtocol {
	gamblerProtocol := &GamblerProtocol{
		HouseID:   houseId,
		Name:      name,
		LastName:  lastName,
		DNI:       dni,
		Birth:     birth,
		BetNumber: betNum,
	}
	return gamblerProtocol
}

// SerializeBet serializes the gambler protocol into a byte array.
func (g *GamblerProtocol) SerializeBet() ([]byte, error) {
	buffer := new(bytes.Buffer)

	if err := binary.Write(buffer, binary.BigEndian, g.HouseID); err != nil {
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

// DeserializeResponse deserializes the response from the server into the
// corresponding fields of the response message.
func (g *GamblerProtocol) DeserializeResponse(response []byte) (uint32, uint32, bool, error) {

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

// writeStringAndPadd writes a string to a buffer and fills the remaining space
// with zeros.
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
