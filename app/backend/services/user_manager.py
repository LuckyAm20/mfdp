from typing import Optional
from sqlmodel import Session, select
from db.models.user import User
from services.balance_manager import BalanceManager
from services.prediction_manager import PredictionManager


class UserManager:
    def __init__(self, session: Session):
        self.session = session
        self.balance = BalanceManager(session)
        self.prediction = PredictionManager(session, self.balance)

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

    def get_profile(self, user: User) -> dict:
        history = self.prediction.list_by_user(user)
        return {
            'username': user.username,
            'status':   user.status,
            'balance':  user.balance,
            'last_predictions': history[-5:],
        }

    def get_by_username(self, username: str,) -> Optional[User]:
        return self.session.exec(select(User).where(User.username == username)).first()
