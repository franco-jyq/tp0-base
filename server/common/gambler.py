import struct
from .utils import Bet



class Gambler:
    def __init__(self, house_id, name, last_name, dni, birth, bet_number):
        self.house_id = house_id  
        self.name = name.decode('utf-8').strip('\x00')
        self.last_name = last_name.decode('utf-8').strip('\x00')
        self.dni = dni  
        self.birth = birth.decode('utf-8').strip('\x00')
        self.bet_number = bet_number 
        self.status_code = 0

    @classmethod
    def deserialize(cls, data):
        """
        Deserialize the data received from the client. 
        With format house_id, name, last_name, dni, birth, bet_number matching the struct format.
        """
        format_string = '>B30s30sI10sI'
        try:
            unpacked_data = struct.unpack(format_string, data)
            return cls(*unpacked_data)
        except struct.error as e:
            print(f"Error deserializing data: {e}")
            return None

    def serialize_gamble_status(self):
        """
        Create a response message indicating success or failure.
        """
        response_format = '>IIB'
        return struct.pack(response_format, self.dni, self.bet_number, self.status_code)

    @classmethod
    def serialize_document(cls, bet):
        """
        Serialize the document of the bet.
        """
        return struct.pack('>I', int(bet.document))
    
    
    def __str__(self):
        return f'Gambler(house_id={self.house_id}, name={self.name}, last_name={self.last_name}, dni={self.dni}, birth={self.birth}, bet_number={self.bet_number}, status_code={self.status_code})'

    def __repr__(self):
        return str(self)
