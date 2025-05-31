FROM python:3.11-slim

WORKDIR /app/backend
ENV PYTHONPATH=/app/backend

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "workers/worker.py"]
