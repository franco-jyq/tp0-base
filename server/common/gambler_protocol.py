import struct
import logging
from .utils import store_bets, Bet
from .gambler import Gambler


class GamblerProtocol:
    def __init__(self, batch_size, packet_size, client_end_message, ack_end_message):
        self.batch_size = batch_size
        self.packet_size = packet_size
        self.client_end_message = client_end_message
        self.ack_end_message = ack_end_message
    
    def deserialize_packets(self, data):
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
            packets.append(gambler)
        
        return packets        
        
        
    def store_bets(self, gamblers):
        """
        Store the bet in the CSV file.
        """
        for gambler in gamblers:
            store_bets([Bet(gambler.house_id, gambler.name, gambler.last_name, gambler.dni, gambler.birth, gambler.bet_number)])
            logging.info(f'action: apuesta_almacenada | result: success | dni: {gambler.dni} | numero: {gambler.bet_number}')
            gambler.status_code = 1
        
        return gamblers
        

    def send_packets_ack(self, sock, gamblers):
        """
        Send an acknowledgment message of the stored bets to the client.
        """
        data = b''
        for gambler in gamblers:
            data += gambler.serialize_gamble_status()

        # If the number of gamblers is less than the ack batch size, send the end message        
        if(len(gamblers) < self.batch_size / self.packet_size):
            data += self.ack_end_message

        sock.sendall(data)



    def receieve_batch_packets(self, sock):
        """
        Calls the function recv until <lentgh> amount of data is received.
        """
        data = b''
        
        while len(data) < self.batch_size:
                
            packet = sock.recv(self.batch_size - len(data))
                
            if not packet:
        
                raise ConnectionError("Connection closed prematurely")
            data += packet
            
            # Check if the end message is received                    
            if (len(data) >= int(self.packet_size)) and (len(data) % int(self.packet_size) == 0)  and (data[-int(self.packet_size):] == self.client_end_message):
                
                return data, True
    
        return data, False

