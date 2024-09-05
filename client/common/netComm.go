package common

import (
	"fmt"
	"io"
	"net"
)

type NetComm struct {
	conn          net.Conn
	serverAddress string
	clientId      string
}

// NewNetComm Creates a new NetComm object with the given parameters.
func NewNetComm(serverAddress string, clientId string) *NetComm {

	return &NetComm{
		conn:          nil,
		serverAddress: serverAddress,
		clientId:      clientId,
	}
}

// CreateConnection Creates a connection to the server.
func (nc *NetComm) createConnection() error {
	conn, err := net.Dial("tcp", nc.serverAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			nc.clientId,
			err,
		)
	}
	nc.conn = conn
	return nil
}

// SendAll Sends the given data using the connection.
func (nc *NetComm) sendAll(data []byte) error {
	totalSent := 0
	for totalSent < len(data) {
		n, err := nc.conn.Write(data[totalSent:])
		if err != nil {
			return err
		}
		if n == 0 {
			return fmt.Errorf("connection closed prematurely")
		}
		totalSent += n
	}
	return nil
}

// ReadAll Reads the given amount of bytes from the connection.
func (nc *NetComm) readAll(length int) ([]byte, error) {
	buffer := make([]byte, length)
	totalRead := 0

	for totalRead < length {
		n, err := nc.conn.Read(buffer[totalRead:])
		if err != nil {
			if err == io.EOF {
				break
			}
			return nil, err
		}
		if n == 0 {
			break
		}
		totalRead += n
	}

	if totalRead < length {
		return nil, fmt.Errorf("connection closed before receiving full message")
	}

	return buffer, nil
}

// CloseConnection Closes the connection.
func (nc *NetComm) CloseConnection() {
	nc.conn.Close()
}
