from __future__ import annotations
from typing import TYPE_CHECKING

from sqlmodel import Session, select
from db.models.balance import Balance
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
        record = Balance(user_id=user.id, amount=net, timestamp=datetime.now(UTC), description=description)
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
        record = Balance(user_id=user.id, amount=-total, timestamp=datetime.now(UTC), description=description)
        self.session.add_all([user, record])
        self.session.commit()
        return record

    def get_history(self, limit: int = 5) -> list[Balance]:
        user = self.ctx.user
        stmt = (
            select(Balance)
            .where(Balance.user_id == user.id)
            .order_by(Balance.timestamp.desc())
            .limit(limit)
        )
        results = self.session.exec(stmt).all()
        return results
