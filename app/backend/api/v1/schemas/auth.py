from datetime import date
from typing import Optional

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    bot_token: str


class UserStatusResponse(BaseModel):
    username: str
    balance: float
    status: str
    status_date_end: Optional[date]
