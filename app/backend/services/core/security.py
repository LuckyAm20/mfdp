import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from db.db import get_session
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from services.user_manager import UserManager
from sqlmodel import Session

SECRET_KEY = os.getenv('SECRET_KEY', 'my_key')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 15))

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')
BOT_SECRET = os.environ.get('BOT_SECRET', '')

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    to_encode.update({'scope': 'frontend'})
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_bot_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    to_encode.update({'scope': 'bot'})
    expire = datetime.now(timezone.utc) + timedelta(days=365 * 100)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str, verify_exp: bool = True) -> dict[str, Any]:
    options = {'verify_exp': verify_exp}
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options=options)
    return payload


def get_username_from_token(token: str, verify_exp: bool = True) -> Optional[str]:
    try:
        payload = decode_token(token, verify_exp=verify_exp)
        username: str = payload.get('sub')
        return username
    except JWTError:
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
    x_bot_secret: Optional[str] = Header(None)
) -> UserManager:
    try:
        payload = decode_token(token, verify_exp=True)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Невалидный токен или истёк',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    username: Optional[str] = payload.get('sub')
    token_scope: Optional[str] = payload.get('scope')

    if username is None or token_scope is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Неполный payload в токене',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    if token_scope == 'bot':
        if x_bot_secret is None or x_bot_secret != BOT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Бот-токен принят, но X-Bot-Secret не передан или неверен',
            )
    elif token_scope != 'frontend':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='У вас нет прав на этот ресурс',
        )

    user_manager = UserManager(session)
    user_obj = user_manager.get_by_username(username)
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Пользователь не найден',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    user_manager.user = user_obj
    return user_manager
