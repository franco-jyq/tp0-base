package common

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"net"
)

const (
	HouseIDLenght      = 1
	NameMaxLenght      = 30
	LastNameMaxLenght  = 30
	DNIMaxLenght       = 4
	BirthMaxLenght     = 10
	BetNumberMaxLenght = 4
	PacketSize         = 79
	AckSize            = 9
	MaxBatchSize       = 8137
	WinnersMaxLenght   = 2
)

var END_MESSAGE = append([]byte("END_MESSAGE"), make([]byte, PacketSize-len("END_MESSAGE"))...)
var ACK_END_MESSAGE = append([]byte("END"), make([]byte, AckSize-len("END"))...)

type GamblerProtocol struct {
	HouseID           uint8
	BatchSize         uint16
	batchAmount       uint16
	AckSize           uint8
	Records           [][]string
	SerializedRecords []byte
	CurrentPosition   int
	Winners           []uint32
}

// NewGamblerProtocol Initializes a new gambler protocol
// receiving the house id, the records to send and the batch amount
func NewGamblerProtocol(houseId uint8, records [][]string, batchAmount uint16) (*GamblerProtocol, error) {

	batchSize := batchAmount * PacketSize

	// Check if the batch size is greater than the maximum allowed
	if batchSize > uint16(MaxBatchSize) {
		log.Debugf("Batch size is greater than the maximum allowed, setting to %d", MaxBatchSize)
		batchSize = uint16(MaxBatchSize)
		batchAmount = batchSize / PacketSize
	}

	gamblerProtocol := &GamblerProtocol{
		HouseID:         houseId,
		batchAmount:     batchAmount,
		BatchSize:       uint16(batchSize),
		AckSize:         uint8(AckSize),
		Records:         records,
		CurrentPosition: 0,
		Winners:         make([]uint32, 0),
	}

	// Serialize the records
	if err := gamblerProtocol.SerializeRecords(); err != nil {
		return nil, err
	}

	return gamblerProtocol, nil
}

func (g *GamblerProtocol) GetMetadata(houseId uint16) ([]byte, error) {

	// Serialize the batch size and house ID
	buffer := new(bytes.Buffer)
	if err := binary.Write(buffer, binary.BigEndian, g.BatchSize); err != nil {
		log.Debugf("Error writing batch size: %v", err)
		return nil, err
	}

	if err := binary.Write(buffer, binary.BigEndian, uint16(houseId)); err != nil {
		log.Debugf("Error writing house ID: %v", err)
		return nil, err
	}

	return buffer.Bytes(), nil
}

// SerilizeRecords Serializes the records to send
func (g *GamblerProtocol) SerializeRecords() error {
	var recordBuffer bytes.Buffer

	// Iterar sobre cada registro en el lote
	for _, record := range g.Records {

		gambler, err := NewGambler(record[0], record[1], record[2], record[3], record[4])

		if err != nil {
			log.Debugf("Error creating record: %v", err)
			continue
		}

		// Serializar el registro individual
		serializedBet, err := gambler.SerializeBet(g.HouseID)

		if err != nil {
			log.Debugf("Error serializing record: %v", err)
			continue
		}

		// Escribir los datos serializados en el buffer del lote
		recordBuffer.Write(serializedBet)
	}

	recordBuffer.Write(END_MESSAGE)

	g.SerializedRecords = recordBuffer.Bytes()
	// Retornar los datos serializados del lote
	return nil
}

// DeserializeAckBatch Deserializes the ack batch
func (g *GamblerProtocol) DeserializeAckBatch(ack_batch []byte) error {

	if len(ack_batch)%int(g.AckSize) != 0 {
		return errors.New("invalid ack batch length")
	}

	for i := 0; i < len(ack_batch); i += int(g.AckSize) {
		packet := ack_batch[i : i+int(g.AckSize)]

		// Check if the packet is the ACK_END_MESSAGE
		if bytes.Equal(packet, ACK_END_MESSAGE) {
			return nil
		}

		// Deserialize the response
		dni, betNumber, _, err := DeserializeGambleStatus(packet)

		if err != nil {
			return err
		}

		log.Infof(`action: apuesta_enviada | result: success | dni: %v | numero: %v`, dni, betNumber)

	}

	return nil
}

// GetBatch Returns the next batch to send. If there's no more data
// to send it returns an empty byte array
func (g *GamblerProtocol) GetBatch() ([]byte, error) {

	// Get the length of the serialized records
	dataLen := len(g.SerializedRecords)

	// Check if there's more data to send
	if g.CurrentPosition >= dataLen {
		log.Debugf("No more data to send")
		return []byte{}, nil
	}
	log.Debugf("Data length: %v", dataLen)

	// Calculate the end of the current chunk
	end := g.CurrentPosition + int(g.BatchSize) // Use g.BatchSize as an integer
	if end > dataLen {
		end = dataLen
	}

	// Get the current chunk
	chunk := g.SerializedRecords[g.CurrentPosition:end]

	// Update the current position
	startPosition := g.CurrentPosition
	g.CurrentPosition = end

	log.Debugf("Returned batch packet from position %d to %d", startPosition, g.CurrentPosition)

	return chunk, nil
}

// ReceiveAckBatch Receives the ack batch from the server
// and returns the data received. If the end message is received
// it returns true
func (g *GamblerProtocol) ReceiveAckBatch(s net.Conn) ([]byte, bool, error) {

	// Calculate the ack batch size
	ackBatchSize := AckSize * g.batchAmount
	data := make([]byte, 0, ackBatchSize)

	for len(data) < int(ackBatchSize) {
		remaining := int(ackBatchSize) - len(data)
		buffer := make([]byte, remaining)

		n, err := s.Read(buffer)

		if err != nil {
			return nil, false, err
		}

		if n == 0 {
			return nil, false, fmt.Errorf("no data read")
		}

		data = append(data, buffer[:n]...)

		// Check if the end message is received
		if len(data) >= AckSize && len(data)%AckSize == 0 {
			if bytes.Equal(data[len(data)-AckSize:], ACK_END_MESSAGE) {
				log.Debugf("End message received")
				return data, true, nil
			}
		}
	}

	return data, false, nil
}

// ReceiveWinnersList Receives the winners list from the server
// and returns the number of winners received.
func (g *GamblerProtocol) ReceiveWinnersList(nc NetComm) (uint16, error) {

	lengthBuf := make([]byte, WinnersMaxLenght)
	winnerCounter := uint16(0)

	// Read the message length from the connection
	if err := nc.receiveAll(lengthBuf); err != nil {
		log.Errorf("failed to read winner documents length: %v", err)
		return 0, err
	}

	// Convert the length to uint16
	length := binary.BigEndian.Uint16(lengthBuf)

	if length == 0 {
		log.Debugf("No winners received")
		return 0, nil
	}

	// Buffer for the winning documents
	dataBuf := make([]byte, length)

	// Read the data from the connection
	if err := nc.receiveAll(dataBuf); err != nil {
		log.Errorf("failed to read winner documents: %v", err)
		return 0, err
	}

	// Process the winning documents
	for i := 0; i < len(dataBuf); i += DNIMaxLenght {
		if i+DNIMaxLenght > len(dataBuf) {
			log.Errorf("invalid winner document length")
		}

		document := binary.BigEndian.Uint32(dataBuf[i : i+4])
		_ = append(g.Winners, document)
		winnerCounter++
	}

	return winnerCounter, nil
}
