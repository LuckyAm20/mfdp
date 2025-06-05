FROM python:3.11-slim

WORKDIR /app/tg_bot

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "bot.py"]