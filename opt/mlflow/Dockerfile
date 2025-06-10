FROM python:3.11-slim

RUN pip install --no-cache-dir mlflow[boto3]

RUN mkdir -p /opt/mlflow/mlruns /opt/mlflow/artifacts

ENTRYPOINT ["mlflow", "ui", \
  "--backend-store-uri", "/opt/mlflow/mlruns", \
  "--default-artifact-root", "/opt/mlflow/artifacts", \
  "--host", "0.0.0.0", \
  "--port", "5000"]
