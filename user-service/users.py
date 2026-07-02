from fastapi import FastAPI
from contextlib import asynccontextmanager

import pika
from consul_helper import register_service, deregister_service, discover_service
import threading
import json

SERVICE_ID = 'user-service-1'


def callback(ch, methods, properties, body):
    data = json.loads(body)
    print("Data received from the queue")
    print(data)
    ch.basic_ack(delivery_tag = methods.delivery_tag)

def consume():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host = "localhost"))
    channel = connection.channel()
    channel.exchange_declare(exchange = 'order_exchange', exchange_type= 'topic', durable = True)
    channel.queue_declare(queue = 'users_queue', durable = True)
    channel.queue_bind(exchange = 'order_exchange', queue = 'users_queue', routing_key='order.*')
    channel.basic_consume(queue = 'users_queue', on_message_callback=callback)
    channel.start_consuming()
    print("Waiting for messages in the queue")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # register_service('user_service', SERVICE_ID, 'user-kuber', 8000) # running on compose file
    register_service('user_service', SERVICE_ID, 'user-service', 8000) # running on kubernetes (service.yaml)
    # Because, in service.yaml, the name of service is 'order-service'

    thread = threading.Thread(target = consume, daemon= True)
    thread.start()
    yield
    deregister_service(SERVICE_ID)

app = FastAPI(lifespan = lifespan)

@app.get("/hello")
def homepage():
    return {"Message": "This is User page"}

@app.get("/health")
def get_health():
    return {'Message': "I'm healthy"}