import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from api.v1.auth import router as auth_router
from api.v1.balance import router as balance_router
from api.v1.prediction import router as prediction_router
from db.db import get_session, init_db
from fastapi import FastAPI
from services.user_manager import UserManager
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    thread = threading.Thread(target=daily_status_reset, daemon=True)
    thread.start()

    yield

app = FastAPI(
    title='OpenTaxiForecast API',
    version='0.1.0',
    lifespan=lifespan
)

def daily_status_reset():
    while True:
        now = datetime.now(timezone.utc)
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        delay = (tomorrow - now).total_seconds()
        time.sleep(delay)

        with next(get_session()) as session:
            UserManager.reset_expired_statuses(session)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(balance_router)
app.include_router(prediction_router)
