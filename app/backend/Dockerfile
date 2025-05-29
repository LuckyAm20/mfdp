FROM python:3.11-slim

WORKDIR /app/backend


COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

Copy . .

EXPOSE 8000

CMD ["python3", "main_test.py"]