package common

import (
	"fmt"
)

type Gambler struct {
	HouseID   string
	Name      string
	LastName  string
	DNI       string
	Birth     string
	BetNumber string
}

func NewGambler(houseId string, name string, lastName string, dni string, birth string, betNum string) *Gambler {
	gambler := &Gambler{
		HouseID:   houseId,
		Name:      name,
		LastName:  lastName,
		DNI:       dni,
		Birth:     birth,
		BetNumber: betNum,
	}
	return gambler
}

// Custom serialization of Gambler to a string
func (g *Gambler) Serialize() []byte {
	data := fmt.Sprintf("HouseId:%s|Name:%s|LastName:%s|DNI:%s|Birth:%s|BetNumber:%s",
		g.HouseID,
		g.Name,
		g.LastName,
		g.DNI,
		g.Birth,
		g.BetNumber,
	)
	return []byte(data)
}
