from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from db.models.prediction import Prediction
from services.core.enums import TaskStatus
from sqlmodel import Session, select

if TYPE_CHECKING:
    from services.user_manager import UserManager

class PredictionManager:
    def __init__(self, session: Session, context: 'UserManager'):
        self.session = session
        self.ctx = context

    def check_status(self):
        user = self.ctx.user
        if user.status == 'bronze':
            self.__check_limit(10)
        elif user.status == 'silver':
            self.__check_limit(100)
        elif user.status == 'gold':
            self.__check_limit(1000)

    def __check_limit(self, num: int = 10) -> None:
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

        return initial_pred

    def get_cost(self) -> float:
        user = self.ctx.user
        if user.status == 'bronze':
            return 20
        elif user.status == 'silver':
            return 15
        elif user.status == 'gold':
            return 10
        return 5

    def check_balance(self, price: float) -> None:
        user = self.ctx.user
        if user.balance < price:
            raise ValueError('Недостаточно средств')

    def list_by_user(self) -> list[Prediction]:
        stmt = select(Prediction).where(Prediction.user_id == self.ctx.user.id)
        sorted_preds = sorted(self.session.exec(stmt).all(), key=lambda x: x.timestamp, reverse=True)
        return sorted_preds

    def get_by_id(self, pred_id) -> Prediction:
        stmt = select(Prediction).where((Prediction.user_id == self.ctx.user.id) & (Prediction.id == pred_id))
        return self.session.exec(stmt).first()
