"""

CREATE TABLE GameParams (
  id SERIAL PRIMARY KEY,
  param VARCHAR(255),
  value VARCHAR(255),
  gameId INT,
  FOREIGN KEY (gameId) REFERENCES Games(id)
);

"""

from app.model.base_model import BaseModel
from sqlmodel import Column, Field, ForeignKey, Integer, String


class GameParams(BaseModel, table=True):
    param: str = Field(sa_column=Column(String))
    value: str = Field(sa_column=Column(String))
    gameId: int = Field(sa_column=Column(Integer, ForeignKey("games.id")))

    def __str__(self):
        return f"GameParams: {self.param}, {self.value}, {self.gameId}"

    def __repr__(self):
        return f"GameParams: {self.param}, {self.value}, {self.gameId}"

    def __eq__(self, other):
        return self.param == other.param and self.value == other.value and self.gameId == other.gameId

    def __hash__(self):
        return hash((self.param, self.value, self.gameId))

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.gameId < other.gameId
