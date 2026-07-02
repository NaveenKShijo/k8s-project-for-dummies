from fastapi import FastAPI
from contextlib import asynccontextmanager
from consul_helper import register_service, deregister_service, discover_service
import requests
from metrics import order_total, order_fails, process_time
from prometheus_fastapi_instrumentator import Instrumentator
import pika
import json

SERVICE_ID = 'order-service-1'

@asynccontextmanager
async def lifespan(app: FastAPI):
    register_service('order_service', SERVICE_ID, 'order-kuber', '8000') # Running on compose file
    # register_service('order_service', SERVICE_ID, 'order-service', '8000') # running on kubernetes (service.yaml)
    yield
    deregister_service(SERVICE_ID)


app = FastAPI()

Instrumentator().instrument(app).expose(app)

@app.get("/hello")
def homepage():
    return {"Message": "This is Orders page"}

@app.get("/health")
def get_health():
    return {'Messagee': 'Healthy'}

@app.get("/users")    
def get_users():
    order_total.inc()
    USER_URL = discover_service('user_service')
    response = requests.get(f"{USER_URL}/hello").json()
    return {"User response": response}

@app.get("/rabbitmq")
def message_queues():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host = 'localhost'))
    channel = connection.channel()
    sample_order = {'order_id': 12, 'product': 'pen', 'price':10}
    channel.exchange_declare(exchange = 'order_exchange', exchange_type= 'topic', durable = True)
    channel.basic_publish(exchange = 'order_exchange', routing_key = 'order.created',
     body = json.dumps(sample_order))    
    connection.close()

    print("Message published")
    return {"Response": "Message published"}


