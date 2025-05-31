from __future__ import annotations
from typing import TYPE_CHECKING

from sqlmodel import Session
from db.models.balance import Balance
from db.models.user import User
from datetime import datetime, UTC
if TYPE_CHECKING:
    from services.user_manager import UserManager

class BalanceManager:
    def __init__(self, session: Session, context: 'UserManager'):
        self.session = session
        self.ctx = context

    def deposit(self, amount: float, description: str = '') -> Balance:
        user = self.ctx.user
        if amount <= 0:
            raise ValueError('Сумма пополнения должна быть > 0')
        net = amount
        user.balance += net
        record = Balance(user_id=user.id, amount=net, timestamp=datetime.now(UTC))
        self.session.add_all([user, record])
        self.session.commit()
        return record

    def withdraw(self, amount: float, description: str = '') -> Balance:
        user = self.ctx.user
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

    def refund(self, amount: float) -> Balance:
        user = self.ctx.user
        user.balance += amount
        record = Balance(user_id=user.id, amount=amount, timestamp=datetime.now(UTC))
        self.session.add_all([user, record])
        self.session.commit()
        return record
