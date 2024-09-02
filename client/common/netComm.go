package common

import (
	"fmt"
	"net"
)

type NetComm struct {
	conn          net.Conn
	serverAddress string
	clientId      string
}

func NewNetComm(serverAddress string, clientId string) *NetComm {

	return &NetComm{
		conn:          nil,
		serverAddress: serverAddress,
		clientId:      clientId,
	}
}

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

func (nc *NetComm) CloseConnection() {
	nc.conn.Close()
}
