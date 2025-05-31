import json
import logging
import math
import os

from datetime import datetime, UTC

import numpy as np
from workers.connection import get_rabbitmq_connection
from db.db import get_session
from services.user_manager import UserManager
from services.core.enums import TaskStatus
from services.core.ml_model import ModelRegistry

LOGDIR = os.getenv('LOG_DIR', '/logs')
os.makedirs(LOGDIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOGDIR, 'worker.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)


def process_prediction(task_data):
    with next(get_session()) as session:
        um = UserManager(session, task_data['user_id'])
        pred = um.prediction.get_by_id(task_data['prediction_id'])
        try:
            pred.status = TaskStatus.PROCESSING
            pred.timestamp = datetime.now(UTC)
            session.commit()

            sequence = np.load('data/test.npy')
            model = ModelRegistry.get('lstm')
            result = model.predict(sequence)

            pred.result = str([0 if num < 0 else math.ceil(num) for num in result])
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
