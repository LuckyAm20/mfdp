import os
import pika

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
QUEUE_NAME = os.getenv('RABBITMQ_QUEUE', 'ml_tasks')


def get_rabbitmq_connection(queue_name: str = None):
    name = queue_name or QUEUE_NAME
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    ch = conn.channel()
    ch.queue_declare(queue=name, durable=True)
    return conn, ch, name
