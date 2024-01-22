from pydantic import BaseModel
from typing import Optional


class BaseWalletOnlyUserId(BaseModel):
   userId: int
   pointsBalance: Optional[float]


