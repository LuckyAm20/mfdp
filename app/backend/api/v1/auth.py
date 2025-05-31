from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from db.db import get_session
from services.user_manager import UserManager
from core.security import create_access_token, verify_password
from core.security import oauth2_scheme
from schemas.token import Token, TokenData

router = APIRouter(prefix='/api/v1/auth', tags=['auth'])

@router.post('/register', status_code=status.HTTP_201_CREATED)
def register(username: str, password: str, session = Depends(get_session)):
    um = UserManager(session)
    try:
        user = um.register(username, password)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    return {'username': user.username, 'role': user.role, 'status': user.status}

@router.post('/token', response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session = Depends(get_session)):
    um = UserManager(session)
    user = um.get_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    access_token = create_access_token({'sub': user.username})
    return {'access_token': access_token, 'token_type': 'bearer'}
