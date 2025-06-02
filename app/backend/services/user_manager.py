from typing import Optional
from sqlmodel import Session, select
from db.models.user import User
from services.balance_manager import BalanceManager
from services.prediction_manager import PredictionManager
from datetime import date, timedelta


STATUS_PRICES = {
    'bronze': 0.0,
    'silver': 100.0,
    'gold': 200.0,
    'diamond': 500.0,
}
STATUS_DURATION_DAYS = 30


class UserManager:
    def __init__(self, session: Session, user_id: Optional[int] = None):
        self.session = session
        self.__user = self.__get_by_id(user_id) if user_id else None
        self.balance = BalanceManager(session, self)
        self.prediction = PredictionManager(session, self)

    @property
    def user(self):
        return self.__user

    @user.setter
    def user(self, value: User):
        self.__user = value

    def register(self, username: str, raw_password: str) -> User:
        existing = self.get_by_username(username)
        if existing:
            return existing
        from services.core.security import get_password_hash
        pw_hash = get_password_hash(raw_password)
        user = User(username=username, password_hash=pw_hash)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def authenticate(self, username: str, raw_password: str) -> Optional[User]:
        from services.core.security import verify_password
        stmt = select(User).where(User.username == username)
        user = self.session.exec(stmt).first()
        if user and verify_password(raw_password, user.password_hash):
            return user
        return None

    def purchase_status(self, level: str) -> User:
        user = self.user
        lvl = level.lower()

        if STATUS_PRICES[self.user.status] > STATUS_PRICES[lvl]:
            raise ValueError('Невозможно понизить статус')

        price = STATUS_PRICES[lvl]
        if user.balance < price:
            raise ValueError('Недостаточно средств')

        self.balance.withdraw(price, description=f'Покупка статуса {lvl}')

        today = date.today()
        if user.status == lvl and user.status_date_end and user.status_date_end >= today:
            new_end = user.status_date_end + timedelta(days=STATUS_DURATION_DAYS)
        else:
            new_end = today + timedelta(days=STATUS_DURATION_DAYS)

        user.status = lvl
        user.status_date_end = new_end

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    @classmethod
    def reset_expired_statuses(cls, session: Session):

        today = date.today()
        stmt = select(User).where(
            User.status_date_end != None,  # noqa: E711
            User.status_date_end < today,
            User.status != 'bronze'
        )
        expired_users = session.exec(stmt).all()
        for user in expired_users:
            user.status = 'bronze'
            user.status_date_end = None
            session.add(user)
        session.commit()

    def get_by_username(self, username: str,) -> Optional[User]:
        return self.session.exec(select(User).where(User.username == username)).first()

    def __get_by_id(self, user_id: int) -> Optional[User]:
        return self.session.exec(select(User).where(User.id == user_id)).first()
