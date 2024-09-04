import socket
import logging
import signal
import threading
from .utils import empty_storage_file
from .gambler_protocol import  GamblerProtocol
import queue

MAX_BATCH_SIZE = 8137
PACKET_SIZE = 79
ACK_SIZE = 9
CLIENT_END_MESSAGE = b'END_MESSAGE' + b'\x00' * (PACKET_SIZE - len(b'END_MESSAGE'))
ACK_END_MESSAGE = b'END' + b'\x00' * (ACK_SIZE - len(b'END'))
MAX_CLIENTS = 5

class Server:
    """
    Server class that handles the communication with the clients
    """
    def __init__(self, port, listen_backlog):
        empty_storage_file()
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._server_is_shutting_down = threading.Event()
        self._gambler_protocol = GamblerProtocol(MAX_BATCH_SIZE, PACKET_SIZE, CLIENT_END_MESSAGE, ACK_END_MESSAGE)
        self._client_queue = queue.Queue()
        self._clients_registered = {}
        self._clients_proccessed = 0
        self._max_clients = MAX_CLIENTS

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """   
        signal.signal(signal.SIGTERM, self.__signal_handler)

        while not self._server_is_shutting_down.is_set():
            
            # Set timeout for the server socket
            self._server_socket.settimeout(1.0)
            try:
                # Accept new connection
                client_sock = self.__accept_new_connection()
                
                # Handle client connection
                client_sock = self.__handle_client_connection(client_sock)
                self._clients_proccessed += 1
                self._client_queue.put(client_sock)

                # Check if all clients have been processed
                if self._clients_proccessed == self._max_clients:
                    logging.info(f'action: sorteo | result: success')                    
                    
                    # Get winners
                    winners = self._gambler_protocol.get_lottery_winners()
                    
                    # Serialize winners
                    # serialized_winners = self._gambler_protocol.serialize_winners_documents(winners)
                    
                    # Send winners to clients
                    while not self._client_queue.empty():
                        client_sock = self._client_queue.get()
                        id = self._clients_registered[client_sock]
                        cli_winners = winners[id]
                        serialized_winners = self._gambler_protocol.serialize_winners_documents(cli_winners)
                        client_sock.sendall(serialized_winners)
                        client_sock.close()
                    
                    break
                

            except socket.timeout:
                continue             
        
        self._server_shutdown_gracefully()



    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:            
            id = self._gambler_protocol.receive_metadata(client_sock)
            logging.info(f'action: metadata_recibida | result: success | id: {id}')
            self._clients_registered[client_sock] = id
            end_msg_received = False
            bets_received = 0            
            
            while not end_msg_received:                
                
                # Receive batch from client
                data, end_msg_received = self._gambler_protocol.receieve_batch_packets(client_sock)            
                
                # Deserialize batch
                gamblers = self._gambler_protocol.deserialize_packets(data)

                if not gamblers:
                    logging.error(f'action: apuesta_recibida | result: fail | cantidad: {bets_received}')
                    return

                # Store bets
                gamblers_stored = self._gambler_protocol.store_bets(gamblers)

                if not gamblers_stored:
                    logging.error(f'action: apuesta_almacenada | result: fail | cantidad: {bets_received}')
                    return

                bets_received += len(gamblers)                        
                
                # TODO handle error
                # Send acknowledgment of the bets stored
                self._gambler_protocol.send_packets_ack(client_sock, gamblers_stored)                
            
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {bets_received}')    
            


        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {}", e)
            client_sock.close()
        finally:
            return client_sock

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c


    def __signal_handler(self, signum, frame):
        """
        Signal handler for SIGTERM
        """
        self._server_is_shutting_down.set() 


    def _server_shutdown_gracefully(self):
        """
        Shutdown socket

        Function close the server socket.
        """
        if self._server_socket:
            self._server_socket.close()
            logging.debug('action: close_socket | result: success')

