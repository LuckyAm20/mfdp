import json
import logging
import math
import os

from datetime import datetime, UTC

import numpy as np
from sklearn.preprocessing import StandardScaler
from workers.connection import get_rabbitmq_connection
from db.db import get_session
from services.user_manager import UserManager
from services.data_manager import DataManager
from services.core.enums import TaskStatus
from services.core.ml_model import ModelRegistry

LOGDIR = os.getenv('LOG_DIR', '/logs')
os.makedirs(LOGDIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOGDIR, 'worker.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

data = DataManager('data/lstm_data.csv')

def post_process(
    y_pred_s: np.ndarray,
    scaler_y: StandardScaler,
):
    y = y_pred_s.copy()
    y = scaler_y.inverse_transform(y.reshape(-1, 1)).reshape(y.shape)
    y = np.clip(y, 0, None)
    return [math.ceil(el) for el in y]

def process_prediction(task_data):
    with next(get_session()) as session:
        um = UserManager(session, task_data['user_id'])
        pred = um.prediction.get_by_id(task_data['prediction_id'])
        try:
            pred.status = TaskStatus.PROCESSING
            pred.timestamp = datetime.now(UTC)
            session.commit()

            model = ModelRegistry.get('lstm')
            target_datetime = datetime(2024, 5, 30, task_data['hour'])
            sequence = data.create_single_sequence(target_datetime, task_data['district'], model.scaler_X)

            result = model.predict(sequence)

            pred.result = str(post_process(result, model.scaler_y))
            pred.timestamp = datetime.now(UTC)
            pred.status = TaskStatus.COMPLETED
            session.commit()

            um.balance.withdraw(task_data['cost'], description='worker charge')

            logging.info(f'✅ Предсказание выполнено: ID {task_data["prediction_id"]}, результат: {pred.result}')

        except Exception as e:
            logging.exception(f'Ошибка обработки предсказания: {e}')
            pred.status = TaskStatus.FAILED
            pred.timestamp = datetime.now(UTC)
            session.commit()


def callback(ch, method, properties, body):
    task_data = json.loads(body)
    logging.info(f'📩 Получено сообщение: {task_data}')
    process_prediction(task_data)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_worker():
    try:
        connection, channel, queue = get_rabbitmq_connection()
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=queue, on_message_callback=callback)

        logging.info('[Worker запущен и ожидает сообщений...')
        channel.start_consuming()

    except Exception as e:
        logging.exception(f'Worker завершился с ошибкой: {e}')


if __name__ == '__main__':
    start_worker()
