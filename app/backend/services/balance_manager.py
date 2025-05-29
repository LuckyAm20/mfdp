from sqlmodel import Session
from db.models.balance import Balance
from db.models.user import User
from datetime import datetime, UTC

class BalanceManager:
    def __init__(self, session: Session):
        self.session = session

    def deposit(self, user: User, amount: float, description: str = '') -> Balance:
        if amount <= 0:
            raise ValueError('Сумма пополнения должна быть > 0')
        net = amount
        user.balance += net
        record = Balance(user_id=user.id, amount=net, timestamp=datetime.now(UTC))
        self.session.add_all([user, record])
        self.session.commit()
        return record

    def withdraw(self, user: User, amount: float, description: str = '') -> Balance:
        if amount < 0:
            raise ValueError('Сумма списания должна быть >= 0')
        total = amount
        if user.balance < total:
            raise ValueError('Недостаточно средств')
        user.balance -= total
        record = Balance(user_id=user.id, amount=-total, timestamp=datetime.now(UTC))
        self.session.add_all([user, record])
        self.session.commit()
        return record

    def refund(self, user: User, amount: float) -> Balance:
        user.balance += amount
        record = Balance(user_id=user.id, amount=amount, timestamp=datetime.now(UTC))
        self.session.add_all([user, record])
        self.session.commit()
        return record
