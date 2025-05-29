from datetime import UTC, datetime, time
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship

class Prediction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='user.id')
    selected_model: Optional[str] = Field(default=None)
    selected_city: Optional[str] = Field(default=None)
    prediction_time: time = Field(default=None)
    result: Optional[str] = None
    status: str = Field(default='pending')
    cost: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
