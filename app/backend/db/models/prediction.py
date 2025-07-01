from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Prediction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='user.id')
    model: Optional[str] = Field(default=None)
    city: Optional[str] = Field(default=None)
    hour: int = Field(default=None)
    district: Optional[int] = Field(default=None)
    result: Optional[str] = Field(default=None)
    trip_costs: Optional[str] = Field(default=None)
    status: str = Field(default='pending')
    cost: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
