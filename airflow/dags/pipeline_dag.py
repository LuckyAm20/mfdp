import glob
import os
from datetime import datetime, timedelta

import boto3
import holidays
import joblib
import mlflow
import numpy as np
import pandas as pd
import tensorflow as tf
from airflow.operators.python import PythonOperator
from huggingface_hub import HfApi, hf_hub_download
from meteostat import Hourly, Stations

from airflow import DAG

# Пути внутри контейнера
SHARED_DIR = '/opt/airflow/worker_shared'
RAW_DIR = os.path.join(SHARED_DIR, 'raw_data')
PROC_DIR = os.path.join(SHARED_DIR, 'dataset')
HF_CLONE_DIR = os.path.join(SHARED_DIR, 'hf_repo')
MODEL_DIR = '/opt/airflow/models/lstm_v2'
# Параметры
BUCKET = 'mfdpproject'
REPO_ID = 'Lucky239/mfdp'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 6, 9),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def download_from_s3() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('YANDEX_S3_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('YANDEX_S3_SECRET_KEY'),
        region_name=os.getenv('YANDEX_S3_REGION'),
        endpoint_url=os.getenv('YANDEX_S3_ENDPOINT'),
    )

    bucket = 'mfdpproject'
    prefix = 'data/'
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    for obj in response.get('Contents', []):
        key = obj['Key']

        if key.endswith('/') or any(part.startswith('.') for part in key.split('/')):
            continue

        local_path = os.path.join('/tmp', key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        s3.download_file(bucket, key, local_path)

def load_and_clean() -> str:
    os.makedirs(PROC_DIR, exist_ok=True)
    dfs = []
    for f in glob.glob(f'{RAW_DIR}/*.parquet'):
        df = pd.read_parquet(f)
        fname = f.lower()
        if 'yellow' in fname:
            df = df.rename(columns={'tpep_pickup_datetime': 'pickup_datetime', 'PULocationID': 'location_id'})
        elif 'green' in fname:
            df = df.rename(columns={'lpep_pickup_datetime': 'pickup_datetime', 'PULocationID': 'location_id'})
        elif 'fhvhv' in fname:
            df = df.rename(columns={'pickup_datetime': 'pickup_datetime', 'PULocationID': 'location_id'})
        if 'pickup_datetime' in df.columns and 'location_id' in df.columns:
            df = df[['pickup_datetime', 'location_id']]
            df['pickup_datetime'] = pd.to_datetime(df['pickup_datetime'], errors='coerce')
            df = df.dropna().drop_duplicates()
            dfs.append(df)
    combined = pd.concat(dfs, ignore_index=True)
    mask = (
            (combined.pickup_datetime >= '2024-01-01') &
            (combined.pickup_datetime < '2025-05-01')
    )
    combined = combined.loc[mask]
    combined['date'] = combined.pickup_datetime.dt.date
    combined['hour'] = combined.pickup_datetime.dt.hour
    combined = combined.drop(columns=['pickup_datetime'])
    combined.to_csv(f'{PROC_DIR}/combined.csv', index=False)
    return f'{PROC_DIR}/combined.csv'


def aggregate_trips_file(input_path: str) -> str:
    df = pd.read_csv(input_path)
    agg = df.groupby(['date', 'hour', 'location_id']).size().reset_index(name='trips_count')
    output_path = os.path.join(PROC_DIR, 'aggregated.csv')
    agg.to_csv(output_path, index=False)
    return output_path

def engineer_features_file(input_path: str) -> str:
    df = pd.read_csv(input_path)
    us_holidays = holidays.US()
    non_working = {'New Year\'s Day', 'MLK Day', 'Washington\'s Birthday', 'Memorial Day',
                   'Juneteenth', 'Independence Day', 'Labor Day', 'Thanksgiving', 'Christmas Day'}
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['is_holiday'] = (
        df['date']
        .apply(lambda d: (us_holidays.get(d.date()) in non_working) if pd.notnull(d) else False)
        .astype(int)
    )
    df['is_month_start'] = df['date'].dt.is_month_start.astype(int)
    df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
    df['day_of_year'] = df['date'].dt.dayofyear
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
    df['is_pre_holiday'] = (
        df['date']
        .shift(-1)
        .apply(lambda d: (us_holidays.get(d.date()) in non_working) if pd.notnull(d) else False)
        .astype(int)
    )

    df['is_post_holiday'] = (
        df['date']
        .shift(1)
        .apply(lambda d: (us_holidays.get(d.date()) in non_working) if pd.notnull(d) else False)
        .astype(int)
    )
    df['lag_1h'] = df.groupby('location_id')['trips_count'].shift(1).fillna(0)
    df['lag_24h'] = df.groupby('location_id')['trips_count'].shift(24).fillna(0)
    df['lag_168h'] = df.groupby('location_id')['trips_count'].shift(168).fillna(0)
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    roll = df.groupby('location_id')['trips_count'].rolling(168, min_periods=1)
    df['roll_168h_mean'] = roll.mean().reset_index(level=0, drop=True)
    df['roll_168h_median'] = roll.median().reset_index(level=0, drop=True)
    df['roll_168h_std'] = roll.std().reset_index(level=0, drop=True).fillna(0)
    df['time_idx'] = df.groupby('location_id').cumcount()
    output_path = os.path.join(PROC_DIR, 'features.csv')
    df.to_csv(output_path, index=False)
    return output_path

def merge_weather_file(input_path: str) -> str:
    df = pd.read_csv(input_path)
    df['date'] = pd.to_datetime(df['date']).dt.date
    df['hour'] = df['hour'].astype(int)

    start = datetime(2024, 1, 1)
    end = datetime(2025, 5, 1)
    station_id = Stations().nearby(40.7128, -74.0060).fetch(1).index[0]
    weather = Hourly(station_id, start, end).fetch().reset_index()

    weather['date'] = weather['time'].dt.date
    weather['hour'] = weather['time'].dt.hour.astype(int)
    weather = weather[['date', 'hour', 'temp', 'prcp', 'wspd']]

    merged = df.merge(
        weather,
        on=['date', 'hour'],
        how='left'
    )

    output_path = os.path.join(PROC_DIR, 'with_weather.csv')
    merged.to_csv(output_path, index=False)
    return output_path

def _sorting(df: pd.DataFrame) -> pd.DataFrame:
    df['datetime'] = pd.to_datetime(df['date'].dt.strftime('%Y-%m-%d') + ' ' + df['hour'].astype(str) + ':00')
    df = df.sort_values(['location_id', 'datetime']).reset_index(drop=True)
    df = df.drop(['datetime'], axis=1)
    return df

def saving(path: str) -> str:
    df = pd.read_csv(path, parse_dates=['date'])
    df = _sorting(df)
    df.to_csv(os.path.join(PROC_DIR, 'dataset_new.csv'), index=False)
    return os.path.join(PROC_DIR, 'dataset_new.csv')

def push_to_hf(path: str) -> None:
    token = os.getenv('HUGGINGFACE_TOKEN')
    api = HfApi(token=token)
    existing_path = hf_hub_download(repo_id=REPO_ID, filename='dataset.csv', repo_type='dataset', token=token)
    df_existing = pd.read_csv(existing_path, parse_dates=['date'])
    new_path = os.path.join(PROC_DIR, 'dataset_new.csv')
    df_new = pd.read_csv(new_path, parse_dates=['date'])
    df = pd.concat([df_existing, df_new], ignore_index=True)

    df = _sorting(df)
    path = os.path.join(PROC_DIR, 'dataset.csv')
    df.to_csv(path, index=False)
    api.upload_file(
        path_or_fileobj=path,
        repo_id=REPO_ID,
        path_in_repo='dataset.csv',
        repo_type='dataset',
        commit_message='Обновление dataset.csv — добавлены новые строки'
    )


def create_sequences(
    df: pd.DataFrame,
    past_steps: int = 72,
    future_steps: int = 24
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[int, int]]:
    locs = df['location_id'].unique()
    loc2idx = {loc: idx for idx, loc in enumerate(locs)}
    seqs, tars, regions = [], [], []
    features_cols = [
        'trips_count', 'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos',
        'is_holiday', 'month', 'is_weekend', 'is_month_start', 'is_month_end',
        'day_of_year', 'week_of_year', 'is_pre_holiday', 'is_post_holiday',
        'lag_1h', 'lag_24h', 'lag_168h', 'roll_168h_mean', 'roll_168h_median', 'roll_168h_std',
        'time_idx', 'temp', 'prcp', 'wspd'
    ]
    for loc in locs:
        sub = df[df['location_id'] == loc]
        features = np.stack([sub[c].values for c in features_cols], axis=1)
        rides = sub['trips_count'].values
        for i in range(past_steps, len(features) - future_steps + 1):
            seqs.append(features[i - past_steps:i])
            tars.append(rides[i:i + future_steps])
            regions.append(loc2idx[loc])
    return np.array(seqs, dtype='float32'), np.array(tars, dtype='float32'), np.array(regions), loc2idx


def train_and_save_model():
    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("daily_retraining")
    os.makedirs(MODEL_DIR, exist_ok=True)

    df = pd.read_csv(os.path.join(PROC_DIR, 'dataset_new.csv'))

    X, y, regions, loc2idx = create_sequences(df)
    n = len(X)
    cut1, cut2 = int(0.8 * n), int(n)
    X_tr, X_val = X[:cut1], X[cut1:cut2]
    y_tr, y_val = y[:cut1], y[cut1:cut2]

    scaler_X_path = os.path.join('/opt/airflow/models/lstm_v1', 'scaler_X.joblib')
    flat_X_tr = X_tr.reshape(-1, X_tr.shape[-1])
    if os.path.exists(scaler_X_path):
        scaler_X = joblib.load(scaler_X_path)
        scaler_X.partial_fit(flat_X_tr)

    scaler_y_path = os.path.join('/opt/airflow/models/lstm_v1', 'scaler_y.joblib')
    flat_y_tr = y_tr.reshape(-1, 1)
    if os.path.exists(scaler_y_path):
        scaler_y = joblib.load(scaler_y_path)
        scaler_y.partial_fit(flat_y_tr)

    X_tr_s = scaler_X.transform(flat_X_tr).reshape(X_tr.shape)
    X_val_s = scaler_X.transform(X_val.reshape(-1, X_val.shape[-1])).reshape(X_val.shape)
    y_tr_s = scaler_y.transform(flat_y_tr).reshape(y_tr.shape)
    y_val_s = scaler_y.transform(y_val.reshape(-1, 1)).reshape(y_val.shape)

    mlflow.set_experiment('mfdp_continuous_training')
    mlflow.keras.autolog()

    with mlflow.start_run():
        model_path = os.path.join('/opt/airflow/models/lstm_v1', 'lstm.keras')
        if os.path.exists(model_path):
            model = tf.keras.models.load_model(model_path)

        es = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss', patience=3, restore_best_weights=True
        )
        model.fit(
            X_tr_s, y_tr_s,
            validation_data=(X_val_s, y_val_s),
            epochs=2,
            batch_size=64,
            callbacks=[es],
            verbose=1
        )
        model_path = os.path.join('/opt/airflow/models/lstm_v2', 'lstm.keras')
        scaler_X_path = os.path.join('/opt/airflow/models/lstm_v2', 'scaler_X.joblib')
        scaler_y_path = os.path.join('/opt/airflow/models/lstm_v2', 'scaler_y.joblib')

        model.save(model_path)
        mlflow.log_artifact(model_path, artifact_path='models')
        joblib.dump(scaler_X, scaler_X_path)
        joblib.dump(scaler_y, scaler_y_path)
        mlflow.log_artifact(scaler_X_path, artifact_path='scalers')
        mlflow.log_artifact(scaler_y_path, artifact_path='scalers')

with DAG(
    'daily_pipeline',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False
) as dag:
    t1 = PythonOperator(
        task_id='download_from_s3',
        python_callable=download_from_s3
    )
    t2 = PythonOperator(
        task_id='load_and_clean',
        python_callable=load_and_clean
    )
    t3 = PythonOperator(
        task_id='aggregate_trips',
        python_callable=aggregate_trips_file,
        op_args=['{{ ti.xcom_pull(task_ids="load_and_clean") }}']
    )
    t4 = PythonOperator(
        task_id='engineer_features',
        python_callable=engineer_features_file,
        op_args=['{{ ti.xcom_pull(task_ids="aggregate_trips") }}']
    )
    t5 = PythonOperator(
        task_id='merge_weather',
        python_callable=merge_weather_file,
        op_args=['{{ ti.xcom_pull(task_ids="engineer_features") }}']
    )
    t6 = PythonOperator(
        task_id='save',
        python_callable=saving,
        op_args=['{{ ti.xcom_pull(task_ids="merge_weather") }}']
    )
    t7 = PythonOperator(
        task_id='push_to_hf',
        python_callable=push_to_hf,
        op_args=['{{ ti.xcom_pull(task_ids="save") }}']
    )

    t8 = PythonOperator(
        task_id='train_and_save_model',
        python_callable=train_and_save_model
    )

    t1 >> t2 >> t3 >> t4 >> t5 >> t6 >> t7 >> t8
