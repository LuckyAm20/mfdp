from __future__ import annotations
from typing import TYPE_CHECKING
from sqlmodel import Session, select
from db.models.prediction import Prediction
from services.core.enums import TaskStatus
from datetime import datetime, UTC

if TYPE_CHECKING:
    from services.user_manager import UserManager

class PredictionManager:
    def __init__(self, session: Session, context: 'UserManager'):
        self.session = session
        self.ctx = context

    def check_status(self):
        user = self.ctx.user
        if user.status == 'bronze':
            self.__check_limit(10000)
        elif user.status == 'silver':
            self.__check_limit(100)
        elif user.status == 'gold':
            self.__check_limit(1000)

    def __check_limit(self, num: int = 10):
        today = datetime.now(UTC).date()
        stmt = select(Prediction).where(
            Prediction.user_id == self.ctx.user.id,
            Prediction.timestamp >= datetime.combine(today, datetime.min.time())
        )
        count = self.session.exec(stmt).all()
        if len(count) >= num:
            raise PermissionError(f'Лимит {self.ctx.user.status} плана — {num} задач в день')

    def create_prediction(
            self, model: str, city: str,
            cost: float, district: int, hour: int) -> Prediction:
        user = self.ctx.user
        bal = self.ctx.balance

        self.check_status()

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

    def list_by_user(self) -> list[Prediction]:
        stmt = select(Prediction).where(Prediction.user_id == self.ctx.user.id)
        return self.session.exec(stmt).all()

    def get_by_id(self, pred_id) -> list[Prediction]:
        stmt = select(Prediction).where(Prediction.user_id == self.ctx.user.id and Prediction.id == pred_id)
        return self.session.exec(stmt).first()
