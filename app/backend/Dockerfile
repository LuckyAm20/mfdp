FROM python:3.11-slim

WORKDIR /app/backend


COPY requirements-backend.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements-backend.txt

Copy . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
#CMD ["python3", "main_test.py"]