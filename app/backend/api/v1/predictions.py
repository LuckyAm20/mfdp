from fastapi import APIRouter, Depends, HTTPException, status

from db.db import get_session
from core.security import get_current_user
from services.prediction_manager import PredictionManager
from worker.publisher import publish_prediction_task
from schemas.prediction import PredictionIn, PredictionOut

router = APIRouter(prefix='/api/v1/predictions', tags=['predictions'])


@router.post('/', response_model=PredictionOut, status_code=status.HTTP_202_ACCEPTED)
def create_pred(body: PredictionIn, current_user=Depends(get_current_user)):

    publish_prediction_task(
        user_id=current_user.id,
        model_name=body.selected_model,
        city=body.selected_city,
        cost=body.cost,
    )

    return {'id': None, 'status': 'pending'}


@router.get('/', response_model=list[PredictionOut])
def list_preds(current_user=Depends(get_current_user)):
    pm = PredictionManager(get_session())
    return pm.list_by_user(current_user)


@router.get('/{pred_id}', response_model=PredictionOut)
def get_pred(pred_id: int, current_user=Depends(get_current_user)):
    pm = PredictionManager(get_session())
    pred = pm.get_by_id(pred_id)
    if not pred or pred.user_id != current_user.id:
        raise HTTPException(status_code=404, detail='Not found')
    return pred
