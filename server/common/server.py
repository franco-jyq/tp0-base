import socket
import logging
import signal
import threading
from .utils import empty_storage_file
from .gambler_protocol import  GamblerProtocol
from .lottery import Lottery
import queue
import multiprocessing


class Server:
    """
    Server class that handles the communication with the clients
    """
    def __init__(self, port, listen_backlog, max_batch_size, packet_size, ack_size):
        empty_storage_file()
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._server_is_shutting_down = threading.Event()
        self._gambler_protocol = GamblerProtocol(max_batch_size, packet_size, ack_size)
        self._lottery = Lottery()
        self._client_queue = queue.Queue()
        self._clients_registered = {}
        self._clients_proccessed = 0
        self._clients_arrived = 0
        self._max_clients = listen_backlog

    def run(self):
        """
        Run the server which will accept 5 connections from clients, store the bets and then
        perform a lottery to select the winners. The server will then send the winners to the clients
        and close the connections.
        """   
        signal.signal(signal.SIGTERM, self.__signal_handler)
        barrier = multiprocessing.Barrier(self._max_clients + 1)
        cond = multiprocessing.Condition()

        while not self._server_is_shutting_down.is_set():
            
            # Set timeout for the server socket
            self._server_socket.settimeout(1.0)

            try:
                # Accept new connection
                client_sock = self.__accept_new_connection()
                
                # Handle client connection
                p = multiprocessing.Process(target=self.__handle_client_connection, args=(client_sock,barrier, cond))
                self._client_queue.put(p)
                p.start()
                self._clients_arrived += 1
            
                # Check if all clients have been processed
                if self._clients_arrived == self._max_clients:

                    # Wait for all clients to store the bets
                    barrier.wait()                                                                                            
                    
                    logging.info(f'action: sorteo | result: success')                    
                    
                    # Load winners                    
                    self._lottery.load_lottery_winners()
                                                                
                    # Notify all clients that the lottery has finished
                    with  cond:
                        cond.notify_all()
                    
                    # Join proccees
                    while not self._client_queue.empty():                        
                        client_p = self._client_queue.get()
                        client_p.join()                                            
            
                    break                
            
            except socket.timeout:
                continue             
        
        self._server_shutdown_gracefully()



    def __handle_client_connection(self, client_sock, barrier, cond):
        """
        Read client metadata and bets, store the bets and send acknowledgment to the client after storing the bets.
        Wait for all clients to finish storing the bets and then wait for the lottery to finish.
        Send the winners to the clients.
        """
        try:            
            id = self._gambler_protocol.receive_metadata(client_sock)
            logging.debug(f'action: metadata_recibida | result: success | id: {id}')
            end_msg_received = False
            bets_received = 0            
            
            # Receive batch from client until end message is received
            while not end_msg_received:                
                
                # Receive batch from client
                data, end_msg_received = self._gambler_protocol.receieve_batch_packets(client_sock)            
                
                # Deserialize batch
                gamblers = self._gambler_protocol.deserialize_packets(data)

                if not gamblers:
                    logging.error(f'action: apuesta_recibida | result: fail | cantidad: {bets_received}')
                    return

                # Store bets
                gamblers_stored = self._lottery.store_bets(gamblers)

                
                if not gamblers_stored:
                    logging.error(f'action: apuesta_almacenada | result: fail | cantidad: {bets_received}')
                    return

                bets_received += len(gamblers)                        
                
                # Send acknowledgment of the bets stored
                self._gambler_protocol.send_packets_ack(client_sock, gamblers_stored)                
            
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {bets_received}')    

            # Wait for all clients to finish
            barrier.wait()

            # Wait for the lottery to finish
            with cond:
                cond.wait()
                serialized_winners = self._lottery.serialize_client_winners(id)
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
        while not self._client_queue.empty():                        
            client_p = self._client_queue.get()
            client_p.join()                                            
        
        if self._server_socket:
            self._server_socket.close()
            logging.debug('action: close_socket | result: success')

