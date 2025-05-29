from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship


class Balance(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='user.id')
    amount: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
