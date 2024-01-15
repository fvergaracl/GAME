from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class GameRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., title="Game ID")
    external_game_id: str = Field(..., title="External Game ID")
    platform: str = Field(..., title="Platform")
    end_date_time: datetime = Field(None, title="End Date Time")
    strategy_id: int = Field(None, title="Strategy ID")
