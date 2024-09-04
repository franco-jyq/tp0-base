import socket
import logging
import signal
import threading
from .utils import empty_storage_file
from .gambler_protocol import  GamblerProtocol
import queue
import multiprocessing

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
        self._clients_arrived = 0
        self._max_clients = MAX_CLIENTS

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """   
        signal.signal(signal.SIGTERM, self.__signal_handler)
        barrier = multiprocessing.Barrier(self._max_clients + 1)
        store_and_load_bet_lock = multiprocessing.Lock()
        cond = multiprocessing.Condition()
        manager = multiprocessing.Manager()
        winners = manager.dict()

        while not self._server_is_shutting_down.is_set():
            
            # Set timeout for the server socket
            self._server_socket.settimeout(1.0)
            try:
                # Accept new connection
                client_sock = self.__accept_new_connection()
                
                # Handle client connection
                p = multiprocessing.Process(target=self.__handle_client_connection, args=(client_sock,barrier, winners, cond, store_and_load_bet_lock))
                self._client_queue.put(p)
                p.start()
                self._clients_arrived += 1
            
                # Check if all clients have been processed
                if self._clients_arrived == self._max_clients:

                    # Wait for all clients to store the bets
                    barrier.wait()                                                                                            
                    
                    logging.info(f'action: sorteo | result: success')                    
                    
                    # Load winners
                    with store_and_load_bet_lock:
                        self._gambler_protocol.load_lottery_winners(winners)
                                                                
                    # Notify all clients that the lottery has finished
                    with  cond:
                        cond.notify_all()
                    
                    # Send winners to clients
                    while not self._client_queue.empty():                        
                        client_p = self._client_queue.get()
                        client_p.join()                                            
            
                    break                
            
            except socket.timeout:
                continue             
        
        self._server_shutdown_gracefully()



    def __handle_client_connection(self, client_sock, barrier, winners, cond, store_bet_lock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:            
            id = self._gambler_protocol.receive_metadata(client_sock)
            logging.debug(f'action: metadata_recibida | result: success | id: {id}')
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
                with store_bet_lock:
                    gamblers_stored = self._gambler_protocol.store_bets(gamblers)

                
                if not gamblers_stored:
                    logging.error(f'action: apuesta_almacenada | result: fail | cantidad: {bets_received}')
                    return

                bets_received += len(gamblers)                        
                
                # TODO handle error
                # Send acknowledgment of the bets stored
                self._gambler_protocol.send_packets_ack(client_sock, gamblers_stored)                
            
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {bets_received}')    

            # Wait for all clients to finish
            barrier.wait()

            # Wait for the lottery to finish
            with cond:
                cond.wait()
                cli_winners = winners[id]
                serialized_winners = self._gambler_protocol.serialize_winners_documents(cli_winners)
                client_sock.sendall(serialized_winners)
                        

        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {}", e)
            client_sock.close()
        finally:
            client_sock.close()

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

