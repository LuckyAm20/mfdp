from __future__ import annotations
from typing import List, TYPE_CHECKING
from sqlmodel import Session, select
from db.models.prediction import Prediction
from db.models.user import User
from services.core.enums import TaskStatus
from datetime import datetime, UTC

if TYPE_CHECKING:
    from services.user_manager import UserManager

class PredictionManager:
    def __init__(self, session: Session, context: 'UserManager'):
        self.session = session
        self.ctx = context

    def create_prediction(
            self, model: str, city: str,
            cost: float, district: int, hour: int) -> Prediction:
        user = self.ctx.user
        bal = self.ctx.balance

        if user.status == 'bronze':
            today = datetime.now(UTC).date()
            stmt = select(Prediction).where(
                Prediction.user_id == user.id,
                Prediction.timestamp >= datetime.combine(today, datetime.min.time())
            )
            count = self.session.exec(stmt).all()
            if len(count) >= 100000:
                raise PermissionError('Лимит бронзового плана — 10 задач в день')

        initial_pred = Prediction(
            user_id=user.id,
            model=model,
            hour=hour,
            district=district,
            city=city,
            cost=cost,
            status=TaskStatus.PENDING,
            timestamp=datetime.now(UTC)
        )
        self.session.add(initial_pred)
        self.session.commit()
        self.session.refresh(initial_pred)

        bal.withdraw(initial_pred.cost, description='Оплата ML-задачи')

        return initial_pred

    def list_by_user(self) -> List[Prediction]:
        stmt = select(Prediction).where(Prediction.user_id == self.ctx.user.id)
        return self.session.exec(stmt).all()

    def get_by_id(self, pred_id) -> List[Prediction]:
        stmt = select(Prediction).where(Prediction.user_id == self.ctx.user.id and Prediction.id == pred_id)
        return self.session.exec(stmt).first()
