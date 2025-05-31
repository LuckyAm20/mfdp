import pika

import json
from workers.connection import get_rabbitmq_connection, QUEUE_NAME
from db.db import get_session
from services.user_manager import UserManager


def publish_prediction_task(user_id: int, model: str, city: str, cost: float, district: int, hour: int):
    with next(get_session()) as session:
        um = UserManager(session, user_id)
        pred = um.prediction.create_prediction(
            model=model,
            city=city,
            cost=cost,
            district=district,
            hour=hour,
        )

        payload = {
            'prediction_id': pred.id,
            'user_id': user_id,
            'model': model,
            'district': district,
            'hour': hour,
            'city': city,
            'cost': cost,
        }

    conn, chan, name = get_rabbitmq_connection()
    chan.basic_publish(
        exchange='',
        routing_key=QUEUE_NAME,
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    conn.close()
    print(f'[x] Задача предсказания отправлена: {payload}')

    return pred
