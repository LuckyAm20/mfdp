from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class TopUpRequest(BaseModel):
    amount: float

class TopUpResponse(BaseModel):
    new_balance: float
    amount: float


class PurchaseStatusRequest(BaseModel):
    status: Literal['silver', 'gold', 'diamond']

class PurchaseStatusResponse(BaseModel):
    status: str
    status_date_end: date
    remaining_balance: float


class BalanceHistoryItem(BaseModel):
    amount: float
    description: str
    timestamp: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }
    )

class HistoryRequest(BaseModel):
    amount: Optional[int] = 5

class BalanceHistoryResponse(BaseModel):
    history: list[BalanceHistoryItem]

