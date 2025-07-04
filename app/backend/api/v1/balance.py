from api.v1.schemas.balance import (BalanceHistoryResponse, HistoryRequest,
                                    PurchaseStatusRequest,
                                    PurchaseStatusResponse, TopUpRequest,
                                    TopUpResponse)
from fastapi import APIRouter, Body, Depends, HTTPException, status
from services.core.security import get_current_user
from services.user_manager import UserManager

router = APIRouter(
    prefix='/api/v1/balance',
    tags=['balance'],
)


@router.post(
    '/top_up',
    response_model=TopUpResponse,
    summary='Пополнить баланс пользователя',
)
def top_up_balance(
    req: TopUpRequest,
    user_manager: UserManager = Depends(get_current_user),
) -> TopUpResponse:
    try:
        record = user_manager.balance.deposit(req.amount, description='Пополнение счёта')
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return TopUpResponse(
        new_balance=user_manager.user.balance,
        amount=record.amount,
    )


@router.post(
    '/purchase',
    response_model=PurchaseStatusResponse,
    summary='Купить или продлить платный статус (silver, gold, diamond)',
)
def purchase_status(
    req: PurchaseStatusRequest,
    user_manager: UserManager = Depends(get_current_user),
) -> PurchaseStatusResponse:
    try:
        user = user_manager.purchase_status(req.status)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return PurchaseStatusResponse(
        status=user.status,
        status_date_end=user.status_date_end,
        remaining_balance=user.balance,
    )

@router.post(
    '/history',
    response_model=BalanceHistoryResponse,
    summary='Получить историю операций с балансом',
)
def get_balance_history(
    req: HistoryRequest = Body(HistoryRequest()),
    user_manager: UserManager = Depends(get_current_user),
) -> BalanceHistoryResponse:
    try:
        limit = req.amount or 5
        history_records = user_manager.balance.get_history(limit=limit)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Ошибка при получении истории'
        )

    return BalanceHistoryResponse(history=history_records)
