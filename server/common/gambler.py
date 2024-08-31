


class Gambler:
    def __init__(self, houseId,name, lastName, dni, birth, betNum):
        self.houseId = houseId
        self.name = name
        self.lastName = lastName
        self.dni = dni
        self.birth = birth
        self.betNum = betNum
    
# "Name:%s|LastName:%s|DNI:%d|Birth:%s|BetNumber:%d"
def parse_gambler(data):
    
    data = data.split("|")
    houseId = data[0].split(":")[1]
    name = data[1].split(":")[1]
    lastName = data[2].split(":")[1]
    dni = data[3].split(":")[1]
    birth = data[4].split(":")[1]
    betNum = data[5].split(":")[1]
    
    return Gambler(houseId,name, lastName, dni, birth, betNum)
    