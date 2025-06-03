import json
import os
import sys
from types import SimpleNamespace

import numpy as np
from sklearn.preprocessing import StandardScaler
from unittest.mock import MagicMock, patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

APP_BACKEND_DIR = os.path.join(PROJECT_ROOT, 'app', 'backend')

if APP_BACKEND_DIR not in sys.path:
    sys.path.insert(0, APP_BACKEND_DIR)

import workers.worker as worker
import workers.publisher as publisher
from services.user_manager import UserManager


class DummyChannel:
    def __init__(self):
        self.published = None

    def basic_publish(self, exchange, routing_key, body, properties):
        self.published = SimpleNamespace(
            exchange=exchange,
            routing_key=routing_key,
            body=json.loads(body),
            properties=properties,
        )

    def basic_ack(self, delivery_tag):
        self.acked = delivery_tag


class DummyConnection:
    def __init__(self, channel):
        self._channel = channel
        self.closed = False

    def channel(self):
        return self._channel

    def close(self):
        self.closed = True


def test_post_process_returns_non_negative_ints():
    scaler = StandardScaler()
    scaler.fit(np.array([[0], [10], [20]]))
    result = worker.post_process(np.array([-2.4, 3.3, 0.0]), scaler)
    assert all(isinstance(x, int) for x in result)
    assert all(x >= 0 for x in result)


def test_callback_invokes_process_and_acks(monkeypatch):
    body_data = {'foo': 'bar'}
    body = json.dumps(body_data).encode()
    called = {'process': False}

    def fake_process(data):
        called['process'] = data == body_data

    dummy_ch = MagicMock()
    dummy_ch.basic_ack = MagicMock()
    monkeypatch.setattr(worker, 'process_prediction', fake_process)
    worker.callback(dummy_ch, MagicMock(delivery_tag=1), None, body)
    assert called['process']
    dummy_ch.basic_ack.assert_called_once_with(delivery_tag=1)


def _register_user(session):
    um = UserManager(session)
    user = um.register('publisher', 'pwd')
    um.user = user
    um.user.balance = 100
    session.commit()
    return um


def test_publish_prediction_creates_record_and_message(db_session, monkeypatch):
    um = _register_user(db_session)
    dummy_ch = DummyChannel()
    dummy_conn = DummyConnection(dummy_ch)

    def fake_session():
        yield db_session

    def fake_conn():
        return dummy_conn, dummy_ch, 'ml_tasks'

    monkeypatch.setattr(publisher, 'get_session', fake_session)
    monkeypatch.setattr(publisher, 'get_rabbitmq_connection', fake_conn)

    pred = publisher.publish_prediction_task(
        user_id=um.user.id,
        model='lstm',
        city='spb',
        cost=0,
        district=2,
        hour=3,
    )

    assert pred.id is not None
    assert dummy_ch.published.body['prediction_id'] == pred.id
    assert dummy_conn.closed is True
