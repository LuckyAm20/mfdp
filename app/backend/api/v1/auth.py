from datetime import timedelta

from api.v1.schemas.auth import (LoginRequest, RegisterRequest, TokenResponse,
                                 UserStatusResponse)
from db.db import get_session
from fastapi import APIRouter, Depends, HTTPException, status
from services.core.security import (create_access_token, create_bot_token,
                                    get_current_user)
from services.user_manager import UserManager
from sqlmodel import Session

router = APIRouter(
    prefix='/api/v1/auth',
    tags=['auth'],
)


@router.post(
    '/register',
    response_model=TokenResponse,
    summary='Зарегистрировать нового пользователя и выдать токены',
)
def register(
    req: RegisterRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    user_manager = UserManager(session)
    user = user_manager.register(req.username, req.password)

    data = {'sub': user.username}

    access_token = create_access_token(
        data,
        expires_delta=timedelta(minutes=15),
    )
    bot_token = create_bot_token(data)

    return TokenResponse(
        access_token=access_token,
        token_type='bearer',
        bot_token=bot_token,
    )


@router.post(
    '/login',
    response_model=TokenResponse,
    summary='Аутентификация: проверить логин/пароль, выдать токены',
)
def login(
    req: LoginRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:

    user_manager = UserManager(session)
    user = user_manager.authenticate(req.username, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Неверное имя пользователя или пароль',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    data = {'sub': user.username}
    access_token = create_access_token(
        data,
        expires_delta=timedelta(minutes=15),
    )
    bot_token = create_bot_token(data)

    return TokenResponse(
        access_token=access_token,
        token_type='bearer',
        bot_token=bot_token,
    )


@router.get(
    '/me',
    response_model=UserStatusResponse,
    summary='Информация о текущем пользователе',
)
def read_current_user(
    user_manager: UserManager = Depends(get_current_user),
) -> UserStatusResponse:
    user = user_manager.user
    return UserStatusResponse(
        username=user.username, status=user.status,
        balance=user.balance, status_date_end=user.status_date_end
    )

