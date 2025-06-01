from datetime import date
from pydantic import BaseModel
from typing import Literal, Optional

class BalanceInfoResponse(BaseModel):
    balance: float
    status: str
    status_date_end: Optional[date]

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
