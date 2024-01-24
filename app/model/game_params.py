from app.model.base_model import BaseModel
from sqlmodel import Column, Field, ForeignKey, Integer, String


class GamesParams(BaseModel, table=True):
    paramKey: str = Field(sa_column=Column(String))
    value: str = Field(sa_column=Column(String))
    gameId: int = Field(sa_column=Column(Integer, ForeignKey("games.id")))

    def __str__(self):
        return f"GameParams: {self.paramKey}, {self.value}, {self.gameId}"

    def __repr__(self):
        return f"GameParams: {self.paramKey}, {self.value}, {self.gameId}"

    def __eq__(self, other):
        return (
            self.paramKey == other.paramKey and
            self.value == other.value and
            self.gameId == other.gameId
        )

    def __hash__(self):
        return hash((self.paramKey, self.value, self.gameId))

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.gameId < other.gameId
