import socket
import logging
import signal
import threading
from .utils import  Bet, recv_all
from .gambler_protocol import  GamblerProtocol

CHUNK_SIZE = 79

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._server_is_shutting_down = threading.Event()

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        signal.signal(signal.SIGTERM, self.__signal_handler)

        while not self._server_is_shutting_down.is_set():
            self._server_socket.settimeout(1.0)
            try:
                client_sock = self.__accept_new_connection()
                self.__handle_client_connection(client_sock)
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
            data = recv_all(client_sock, CHUNK_SIZE)            
            gambler_protocol = GamblerProtocol.deserialize(data)
            gambler_protocol.store_bets()                        
            client_sock.sendall(gambler_protocol.return_gamble_status())
        
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
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

