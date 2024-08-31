import struct
import logging
from .utils import store_bets, Bet

class GamblerProtocol:
    def __init__(self, house_id, name, last_name, dni, birth, bet_number):
        self.house_id = house_id  # Already an integer, no need to decode
        self.name = name.decode('utf-8').strip('\x00')
        self.last_name = last_name.decode('utf-8').strip('\x00')
        self.dni = dni  # Already an integer, no need to decode
        self.birth = birth.decode('utf-8').strip('\x00')
        self.bet_number = bet_number  # Already an integer, no need to decode
        self.status_code = 0

    @classmethod
    def deserialize(cls, data):
        # Big-endian format, matching the Go client's serialization
        # HouseID (1 byte), Name (30 bytes), LastName (30 bytes), Birth (10 bytes), DNI (4 bytes), BetNumber (4 bytes)
        format_string = '>B30s30sI10sI'
        unpacked_data = struct.unpack(format_string, data)
        return cls(*unpacked_data)

    def store_bets(self):
        """
        Store the bet in the CSV file.
        """
        store_bets([Bet(self.house_id,self.name, self.last_name, self.dni, self.birth, self.bet_number)])
        self.status_code = 1
        logging.info(f'action: apuesta_almacenada | result: success | dni: {self.dni} | numero: {self.bet_number}')
        

    def return_gamble_status(self):
        """
        Create a response message indicating success or failure.
        """
        response_format = '>IIB'
        return struct.pack(response_format, self.dni, self.bet_number, self.status_code)