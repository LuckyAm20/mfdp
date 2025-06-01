import threading

from fastapi import FastAPI
from db.db import init_db, get_session
from api.v1.auth import router as auth_router
from api.v1.balance import router as balance_router
from services.user_manager import UserManager
from datetime import timezone, datetime, timedelta
import time

app = FastAPI(
    title='OpenTaxiForecast API',
    version='0.1.0',
)


@app.on_event('startup')
def on_startup():
    init_db()

    thread = threading.Thread(target=daily_status_reset, daemon=True)
    thread.start()

def daily_status_reset():
    while True:
        now = datetime.now(timezone.utc)
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        delay = (tomorrow - now).total_seconds()
        time.sleep(delay)

        with next(get_session()) as session:
            UserManager.reset_expired_statuses(session)

app.include_router(auth_router)
app.include_router(balance_router)
# app.include_router(predictions.router)
