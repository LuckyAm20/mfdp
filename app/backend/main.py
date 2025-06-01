from fastapi import FastAPI
from db.db import init_db
from api.v1.auth import router as auth_router



from api.v1 import balance, predictions # Убрать


app = FastAPI(
    title='OpenTaxiForecast API',
    version='0.1.0',
)


@app.on_event('startup')
def on_startup():
    init_db()

app.include_router(auth_router)
# app.include_router(balance.router)
# app.include_router(predictions.router)
