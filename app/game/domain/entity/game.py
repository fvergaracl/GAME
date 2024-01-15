from sqlalchemy import String, Integer, TIMESTAMP, Column
from sqlalchemy.orm import Mapped, mapped_column
from core.db import Base
from core.db.mixins import TimestampMixin

class Game(Base, TimestampMixin):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_game_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    platform: Mapped[str] = mapped_column(String(255), nullable=False)
    end_date_time: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    strategy_id: Mapped[int] = mapped_column(Integer, nullable=True)

    @classmethod
    def create(
        cls, *, external_game_id: str, platform: str, end_date_time: datetime, strategy_id: int = None
    ) -> "Game":
        return cls(
            external_game_id=external_game_id,
            platform=platform,
            end_date_time=end_date_time,
            strategy_id=strategy_id
        )
