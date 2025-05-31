from fastapi import APIRouter, Depends, HTTPException, status

from db.db import get_session
from core.security import get_current_user
from services.balance_manager import BalanceManager
from schemas.balance import BalanceOut, DepositIn

router = APIRouter(prefix='/api/v1/balance', tags=['balance'])

@router.get('/', response_model=float)
def get_balance(current_user = Depends(get_current_user)):
    return current_user.balance

@router.post('/deposit', response_model=BalanceOut)
def deposit(body: DepositIn, current_user = Depends(get_current_user), session=Depends(get_session)):
    bm = BalanceManager(session)
    try:
        entry = bm.deposit(current_user, body.amount)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    return entry

@router.get('/history', response_model=list[BalanceOut])
def history(current_user = Depends(get_current_user)):
    return current_user.balance_history
