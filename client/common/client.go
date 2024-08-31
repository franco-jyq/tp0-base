package common

import (
	"os"
	"os/signal"
	"syscall"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// Client Entity that encapsulates networking and buiseness logic
type Client struct {
	gamblerProt GamblerProtocol
	netComm     NetComm
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(gambler GamblerProtocol, netComm NetComm) *Client {
	client := &Client{
		gamblerProt: gambler,
		netComm:     netComm,
	}
	return client
}

// Client = QuinielaClient
func (c *Client) StartClientLoop() {

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGTERM)

	select {

	case <-sigChan:
		c.netComm.CloseConnection()
		log.Debugf("action: close_socket | result: success | client_id: %v", c.netComm.clientId)
		return
	default:

		err := c.netComm.createConnection()

		if err != nil {
			log.Errorf("action: connect | result: fail | client_id: %v | error: %v",
				c.netComm.clientId,
				err,
			)
			return
		}

		bytes, err := c.gamblerProt.SerializeBet()

		if err != nil {
			log.Errorf("action: serialize | result: fail | client_id: %v | error: %v",
				c.netComm.clientId,
				err,
			)
			c.netComm.CloseConnection()
			return
		}

		err = c.netComm.sendAll(bytes)

		if err != nil {
			log.Errorf("action: send_message | result: fail | client_id: %v | error: %v")
			c.netComm.CloseConnection()
			return
		}

		log.Infof(`action: apuesta_enviada | result: success | dni: %v | numero: %v`,
			c.gamblerProt.DNI, c.gamblerProt.BetNumber,
		)

		response, err := c.netComm.readAll(ServerResponseLength)

		if err != nil {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
				c.netComm.clientId,
				err,
			)
			c.netComm.CloseConnection()
			return
		}

		dni, betNumber, success, err := c.gamblerProt.DeserializeResponse(response)

		if err != nil {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
				c.netComm.clientId,
				err,
			)
			return
		}

		if success {
			log.Debugf(`action: server_status | result: success | dni: %v | numero: %v`,
				dni, betNumber,
			)
		} else {
			log.Errorf(`action: server_status | result: fail | dni: %v | numero: %v`,
				dni, betNumber)
		}

		c.netComm.CloseConnection()

	}
}
