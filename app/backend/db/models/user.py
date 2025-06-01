from typing import Optional
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, nullable=False)
    password_hash: str = Field(nullable=False)
    role: str = Field(default='user')
    status: str = Field(default='bronze')
    balance: float = Field(default=0.0)
    tg_id: Optional[str] = Field(default=None, unique=True)
    selected_model: Optional[str] = Field(default=None)
