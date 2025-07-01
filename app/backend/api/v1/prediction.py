from datetime import datetime

from api.v1.schemas.prediction import (HistoryRequest, NYCPredictionRequest,
                                       PredictionHistoryResponse,
                                       PredictionResponse)
from fastapi import APIRouter, Body, Depends, HTTPException, status
from services.core.security import get_current_user
from services.user_manager import UserManager
from workers.publisher import publish_prediction_task

router = APIRouter(
    prefix='/api/v1/prediction',
    tags=['prediction'],
)


def create_nyc_prediction(
    cost: int,
    district: int,
    user_manager: UserManager,
) -> PredictionResponse:
    user = user_manager.user

    now = datetime.now()
    next_hour = (now.hour + 1) % 24
    model_name = 'lstmv3'
    city_name = 'NYC'

    try:
        pred = publish_prediction_task(
            user_id=user.id,
            model=model_name,
            city=city_name,
            district=district,
            hour=next_hour,
            cost=cost,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Не удалось создать или отправить задачу'
        )

    return pred


@router.post(
    '/nyc_free',
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Отправить запрос на предсказание',
)
def create_nyc_prediction_free(
    req: NYCPredictionRequest,
    user_manager: UserManager = Depends(get_current_user),
) -> PredictionResponse:
    try:
        user_manager.prediction.check_status()
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail='Исчерпан лимит на количество предсказаний'
        )
    return create_nyc_prediction(0, req.district, user_manager)

@router.post(
    '/nyc_cost',
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Отправить платный запрос на предсказание',
)
def create_nyc_prediction_cost(
    req: NYCPredictionRequest,
    user_manager: UserManager = Depends(get_current_user),
) -> PredictionResponse:
    cost = user_manager.prediction.get_cost()
    try:
        user_manager.prediction.check_balance(cost)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail='Недостаточно средств для выполнения операции'
        )
    return create_nyc_prediction(cost, req.district, user_manager)

@router.post(
    '/history',
    response_model=PredictionHistoryResponse,
    summary='История предсказаний текущего пользователя',
)
def get_prediction_history(
    req: HistoryRequest = Body(HistoryRequest()),
    user_manager: UserManager = Depends(get_current_user),
) -> PredictionHistoryResponse:
    limit = req.amount or 5

    all_preds = user_manager.prediction.list_by_user()
    limited = all_preds[:limit]
    return PredictionHistoryResponse(history=limited)

@router.get(
    '/{prediction_id}',
    response_model=PredictionResponse,
    summary='Получить статус и результат конкретного предсказание по ID',
)
def get_prediction(
    prediction_id: int,
    user_manager: UserManager = Depends(get_current_user),
) -> PredictionResponse:
    pred = user_manager.prediction.get_by_id(prediction_id)
    if not pred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Предсказание не найдено')
    return pred
