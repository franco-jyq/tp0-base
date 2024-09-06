import struct
import logging
from .gambler import Gambler
from .utils import  Bet, load_bets, has_won, store_bets, read_all
import multiprocessing


class GamblerProtocol:
    """
    Class that handles the communication protocol between the server and the client.
    """
    def __init__(self, max_batch_size, packet_size, ack_size):          
        # self.winners = multiprocessing.Manager().dict()
        # self.store_and_load_bet_lock = multiprocessing.Lock()
        self.batch_size = max_batch_size
        self.packet_size = packet_size
        self.client_end_message = b'END_MESSAGE' + b'\x00' * (packet_size - len(b'END_MESSAGE'))
        self.ack_end_message = b'END' + b'\x00' * (ack_size - len(b'END'))
        self.metadata_size = 4
    
    def receive_metadata(self, sock):
        """
        Receives the batch size and id from the client.
        """        
        data = read_all(sock, self.metadata_size)
        self.batch_size, id = struct.unpack('>HH', data)  
        return  id
        
    def receieve_batch_packets(self, sock):
        """
        Calls the function recv until <lentgh> amount of data is received.
        Or until the end message is received.
        """
        data = b''
        while len(data) < self.batch_size:
                
            packet = sock.recv(self.batch_size - len(data))
                
            if not packet:
                raise ConnectionError("Connection closed prematurely")
            
            data += packet
            
            # Check if the end message is received                    
            if len(data) >= self.packet_size and data[-self.packet_size:] == self.client_end_message:
                return data, True  
    
        return data, False
        
    def deserialize_packets(self, data):
        """
        Deserialize the packets received from the client.
        """
        packets = []
        total_data_length = len(data)
        packet_size = self.packet_size

        for i in range(0, total_data_length, packet_size):
            packet_data = data[i:i+packet_size]
            
            # Check if the packet is the end message
            if packet_data == self.client_end_message:
                break

            # Deserialize the packet and add it to the list
            gambler = Gambler.deserialize(packet_data)

            if not gambler:
                logging.error(f'action: deserializacion_fallida | result: failed | packet_data: {packet_data}')
                return None

            packets.append(gambler)
        
        return packets        
            

    def send_packets_ack(self, sock, gamblers):
        """
        Send an acknowledgment message of the stored bets to the client.
        """
        data = b''
        for gambler in gamblers:
            
            gambler_status = gambler.serialize_gamble_status()

            if not gambler_status:
                continue

            data += gambler.serialize_gamble_status()

        # If the number of gamblers is less than the ack batch size, send the end message.       
        if(len(gamblers) < self.batch_size / self.packet_size):
            data += self.ack_end_message

        sock.sendall(data)





    