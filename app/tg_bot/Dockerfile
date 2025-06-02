FROM python:3.11-slim

WORKDIR /app/tg_bot

COPY ./app/tg_bot/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "bot.py"]