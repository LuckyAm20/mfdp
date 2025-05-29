from typing import List
from sqlmodel import Session, select
from db.models.prediction import Prediction
from db.models.user import User
from services.core.enums import TaskStatus
from datetime import datetime, UTC
from services.core.ml_model import load_model_by_name
from services.balance_manager import BalanceManager

class PredictionManager:
    def __init__(self, session: Session, balance: BalanceManager):
        self.session = session
        self.balance = balance

    def run_prediction(self, user: User, selected_model: str, cost: float, selected_city: str, sequence) -> Prediction:
        bal = self.balance

        if user.status == 'bronze':
            today = datetime.now(UTC).date()
            stmt = select(Prediction).where(
                Prediction.user_id == user.id,
                Prediction.timestamp >= datetime.combine(today, datetime.min.time())
            )
            count = self.session.exec(stmt).all()
            if len(count) >= 10:
                raise PermissionError('Лимит бронзового плана — 10 задач в день')

        initial_pred = Prediction(
            user_id=user.id,
            selected_model=selected_model,
            prediction_time=datetime.now(UTC).time(),
            selected_city=selected_city,
            cost=0.0,  # временно
            status=TaskStatus.PENDING.value,
            timestamp=datetime.now(UTC)
        )
        self.session.add(initial_pred)
        self.session.commit()
        self.session.refresh(initial_pred)

        bal.withdraw(user, initial_pred.cost, description='Оплата ML-задачи')

        initial_pred.status = TaskStatus.PROCESSING
        self.session.add(initial_pred)
        self.session.commit()

        model = load_model_by_name(selected_model)
        result = model.predict(sequence)

        initial_pred.result = str(result)
        initial_pred.status = TaskStatus.COMPLETED.value
        self.session.add(initial_pred)
        self.session.commit()
        return initial_pred

    def list_by_user(self, user: User) -> List[Prediction]:
        stmt = select(Prediction).where(Prediction.user_id == user.id)
        return self.session.exec(stmt).all()
