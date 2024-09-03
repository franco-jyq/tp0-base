import struct


class Gambler:
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

    def __str__(self):
        return f'Gambler(house_id={self.house_id}, name={self.name}, last_name={self.last_name}, dni={self.dni}, birth={self.birth}, bet_number={self.bet_number}, status_code={self.status_code})'

    def __repr__(self):
        return str(self)
