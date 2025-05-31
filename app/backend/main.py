import asyncio

from fastapi import FastAPI
from db.db import init_db
from api.v1 import auth, balance, predictions
from services.core.ml_model import ModelRegistry

app = FastAPI(title='OpenTaxiForecast API')


@app.on_event('startup')
def on_startup():
    init_db()

    ModelRegistry.reload_all()

    async def daily_reload():
        while True:
            now = asyncio.get_event_loop().time()

            import datetime
            t = datetime.datetime.now()
            tomorrow = (t + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
            delay = (tomorrow - t).total_seconds()
            await asyncio.sleep(delay)
            ModelRegistry.reload_all()

    asyncio.create_task(daily_reload())

app.include_router(auth.router)
app.include_router(balance.router)
app.include_router(predictions.router)
