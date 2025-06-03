import os
import sys
import types

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

APP_BACKEND_DIR = os.path.join(PROJECT_ROOT, 'app', 'backend')

if APP_BACKEND_DIR not in sys.path:
    sys.path.insert(0, APP_BACKEND_DIR)

fake_db_db = types.ModuleType('db.db')

def fake_get_session():
    """
    Этот генератор «мокает» реальный get_session из app/backend/db/db.py.
    Мы создаем in-memory SQLite, возвращаем новый Session и закрываем его
    при выходе из генератора.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine('sqlite:///:memory:')
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

fake_db_db.get_session = fake_get_session
sys.modules['db.db'] = fake_db_db

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite:///testing.db", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()
    if os.path.exists("testing.db"):
        os.remove("testing.db")

@pytest.fixture(scope="function")
def session(db_engine):
    session = Session(db_engine)
    yield session
    session.close()

@pytest.fixture(scope="function")
def db_session(db_engine):
    SQLModel.metadata.drop_all(db_engine)
    SQLModel.metadata.create_all(db_engine)
    session = Session(db_engine)
    yield session
    session.close()

@pytest.fixture(autouse=True)
def fake_security(monkeypatch):
    mod = types.ModuleType('services.core.security')
    mod.get_password_hash = lambda pw: f'hash-{pw}'
    mod.verify_password = lambda raw, stored: stored == f'hash-{raw}'
    sys.modules['services.core.security'] = mod
    yield
    sys.modules.pop('services.core.security', None)


# @pytest.fixture(name="client")
# def client_fixture(session: Session):
#     def get_session_override():
#         return session
#
#     app.dependency_overrides[get_session] = get_session_override
#
#     client = TestClient(app)
#     yield client
#     app.dependency_overrides.clear()
