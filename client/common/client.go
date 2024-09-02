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

		defer c.netComm.CloseConnection()

		if err != nil {
			log.Errorf("action: connect | result: fail | client_id: %v | error: %v",
				c.netComm.clientId,
				err,
			)
			return
		}

		c.gamblerProt.SerializeRecords()

		for done_sending, done_receiving := false, false; !done_sending && !done_receiving; {

			batch, _ := c.gamblerProt.GetBatch()
			log.Debugf("Batch generated")

			if len(batch) == 0 {
				done_sending = true
			}

			err = c.netComm.sendAll(batch)
			log.Debugf("Batch sended")

			if err != nil {
				log.Errorf("action: send_message | result: fail | client_id: %v | error: %v")
				c.netComm.CloseConnection()
				return
			}

			ack_batch, is_ended, err := c.gamblerProt.ReceiveAckBatch(c.netComm.conn)

			if err != nil {
				log.Errorf("error: %v",
					err,
				)
				return
			}

			done_receiving = is_ended

			err = c.gamblerProt.DeserializeAckBatch(ack_batch)

			if err != nil {
				log.Errorf("error: %v",
					err,
				)
			}
		}

		c.netComm.CloseConnection()
		return
	}
}
