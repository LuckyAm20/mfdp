FROM python:3.12-slim

WORKDIR /app/backend
ENV PYTHONPATH=/app/backend

COPY requirements-worker.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements-worker.txt

COPY . .

CMD ["python3", "workers/worker.py"]
