import struct
import logging
from .gambler import Gambler
from .utils import  Bet, load_bets, has_won, store_bets
import multiprocessing


class Lottery:
    """
    Class that handles the communication protocol between the server and the client.
    """
    def __init__(self):          
        self.winners = {}
        
    def store_bets(self, gamblers):
        """
        Store the bet in the CSV file.
        """
        for gambler in gamblers:
            store_bets([Bet(gambler.house_id, gambler.name, gambler.last_name, gambler.dni, gambler.birth, gambler.bet_number)])
            logging.info(f'action: apuesta_almacenada | result: success | dni: {gambler.dni} | numero: {gambler.bet_number}')
            gambler.status_code = 1
        
        return gamblers

    def serialize_client_winners(self, id):
        """
        Serializes the winners documents.
        """
        client_winners = self.winners[id]
        data = b''
        for bet in client_winners:
            data += Gambler.serialize_document(bet)
        
        length = len(data)

        return struct.pack('>H', length) + data
    

    def load_lottery_winners(self):
        """
        Returns the lottery winners.
        """
        bets = load_bets()
        for bet in bets:
            
            if bet.agency not in self.winners:
                self.winners[bet.agency] = []

            if has_won(bet):
                logging.debug(f'action: ganador | result: success | dni: {bet.document} | numero: {bet.number}')
                self.winners[bet.agency].append(bet)


    