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
	clientId    uint16
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(gambler GamblerProtocol, netComm NetComm, clientId uint16) *Client {
	client := &Client{
		gamblerProt: gambler,
		netComm:     netComm,
		clientId:    clientId,
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

		// Create connection with the server
		err := c.netComm.createConnection()

		// Close connection when function ends
		defer c.netComm.CloseConnection()

		if err != nil {
			log.Errorf("action: connect | result: fail | client_id: %v | error: %v",
				c.netComm.clientId,
				err,
			)
			return
		}

		// Send batch size
		metadataBytes, _ := c.gamblerProt.GetMetadata(c.clientId)
		if err := c.netComm.sendAll(metadataBytes); err != nil {
			log.Errorf("action: send_message | result: fail | client_id: %v | error: %v", c.netComm.clientId, err)
			return
		}

		for done_sending, done_receiving := false, false; !done_sending && !done_receiving; {

			// Get the next batch
			batch, err := c.gamblerProt.GetBatch()

			if err != nil {
				log.Errorf("action: get_batch | result: fail | client_id: %v | error: %v", c.netComm.clientId, err)
				return
			}

			if len(batch) == 0 {
				done_sending = true
			}

			// Send batch to server
			err = c.netComm.sendAll(batch)

			if err != nil {
				log.Errorf("action: send_message | result: fail | client_id: %v | error: %v")
				return
			}

			// Receive ack batch from server
			ack_batch, is_ended, err := c.gamblerProt.ReceiveAckBatch(c.netComm.conn)

			if err != nil {
				log.Errorf("error: %v", err)
				return
			}

			done_receiving = is_ended

			// Deserialize ack batch
			err = c.gamblerProt.DeserializeAckBatch(ack_batch)

			if err != nil {
				log.Errorf("error: %v", err)
				return
			}
		}

		// Receive winners list
		winnerCounter, err := c.gamblerProt.ReceiveWinnersList(c.netComm)

		if err != nil {
			log.Errorf("Error receiving winner list: %v", err)
			return
		}

		log.Infof(`action: consulta_ganadores | result: success | cant_ganadores: %v`, winnerCounter)

		return
	}
}
