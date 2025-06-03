import os
import sys

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import func
from sqlmodel import select

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
APP_BACKEND_DIR = os.path.join(PROJECT_ROOT, 'app', 'backend')
if APP_BACKEND_DIR not in sys.path:
    sys.path.insert(0, APP_BACKEND_DIR)

from db.models.prediction import Prediction
from services.user_manager import UserManager


def make_um(session, username='user', pwd='pwd'):
    um = UserManager(session)
    user = um.register(username=username, raw_password=pwd)
    um.user = user
    return um


def test_register_and_authenticate(db_session):
    um = make_um(db_session, 'alice', 'secret')
    assert um.authenticate('alice', 'secret').id == um.user.id
    assert um.authenticate('alice', 'wrong') is None


def test_balance_flow_and_history(db_session):
    um = make_um(db_session)
    bm = um.balance
    bm.deposit(150, description='top up')
    bm.withdraw(40, description='ride')
    history = bm.get_history(limit=2)
    assert [rec.amount for rec in history] == [-40, 150]
    assert um.user.balance == 110


def test_prediction_cost_by_status(db_session):
    um = make_um(db_session)
    assert um.prediction.get_cost() == 20
    um.balance.deposit(300)
    um.purchase_status('gold')
    assert um.prediction.get_cost() == 10


def test_purchase_status_and_balance(db_session):
    um = make_um(db_session)
    um.balance.deposit(300)
    updated = um.purchase_status('silver')
    assert updated.status == 'silver'
    assert updated.balance == 200
    assert updated.status_date_end == date.today() + timedelta(days=30)


def test_purchase_insufficient_funds(db_session):
    um = make_um(db_session)
    with pytest.raises(ValueError):
        um.purchase_status('diamond')


def test_reset_expired_statuses(db_session):
    um = make_um(db_session)
    um.balance.deposit(100)
    um.purchase_status('silver')
    um.user.status_date_end = date.today() - timedelta(days=1)
    db_session.commit()
    UserManager.reset_expired_statuses(db_session)
    db_session.refresh(um.user)
    assert um.user.status == 'bronze'
    assert um.user.status_date_end is None


def test_get_by_id_returns_prediction(db_session):
    um = make_um(db_session)

    now = datetime.now()
    pred = um.prediction.create_prediction(
        city='nyc',
        district=5,
        model='testmodel',
        hour=1,
        cost=10,
    )

    fetched = um.prediction.get_by_id(pred.id)
    assert fetched is not None
    assert fetched.id == pred.id
    assert fetched.user_id == um.user.id
    assert fetched.city == 'nyc'
    assert fetched.district == 5
    assert fetched.model == 'testmodel'
    assert fetched.hour == 1
    assert fetched.cost == 10


def test_create_prediction_record(db_session):
    um = make_um(db_session)

    initial_count = db_session.exec(select(func.count(Prediction.id))).one()
    assert initial_count == 0

    pred = um.prediction.create_prediction(
        city='la',
        district=5,
        model='lstm',
        hour=1,
        cost=10,
    )
    assert isinstance(pred, Prediction)
    after_count = db_session.exec(select(func.count(Prediction.id))).one()
    assert after_count == 1

    rec = db_session.exec(select(Prediction).where(Prediction.id == pred.id)).first()
    assert rec.city == 'la'
    assert rec.model == 'lstm'
    assert rec.user_id == um.user.id


def test_rate_limit_exceeded(db_session):
    um = make_um(db_session)

    for _ in range(10):
        um.prediction.create_prediction(
            city='la',
            district=5,
            model='lstm',
            hour=1,
            cost=10,
        )

    with pytest.raises(PermissionError):
        um.prediction.check_status()


def test_prediction_history(db_session):
    um = make_um(db_session)
    now = datetime.now()

    for _ in range(2):
        um.prediction.create_prediction(
            city='la',
            district=5,
            model='lstm',
            hour=1,
            cost=10,
        )

    history = um.prediction.list_by_user()

    assert len(history) == 2
    assert history[0].timestamp > history[1].timestamp
