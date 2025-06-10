FROM apache/airflow:2.10.5-python3.11

WORKDIR /airflow

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY dags          /opt/airflow/dags
