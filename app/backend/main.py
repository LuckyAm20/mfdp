import asyncio

from fastapi import FastAPI
from db.db import init_db
from services.core.ml_model import ModelRegistry
from api.v1.auth import router as auth_router



from api.v1 import balance, predictions # Убрать


app = FastAPI(
    title='OpenTaxiForecast API',
    version='0.1.0',
)


@app.on_event('startup')
def on_startup():
    init_db()

    ModelRegistry.reload_all()

    async def daily_reload():
        while True:
            import datetime
            t = datetime.datetime.now()
            tomorrow = (t + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
            delay = (tomorrow - t).total_seconds()
            await asyncio.sleep(delay)
            ModelRegistry.reload_all()

    asyncio.create_task(daily_reload())

app.include_router(auth_router)
# app.include_router(balance.router)
# app.include_router(predictions.router)
