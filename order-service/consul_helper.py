import consul
import os

CONSUL_HOST = os.getenv("CONSUL_HOST", "consul")
client = consul.Consul(host=CONSUL_HOST, port=8500)

def register_service(service_name, service_id, host, port):
    client.agent.service.register(name = service_name, service_id = service_id,
    address = host, port = port
    )

def deregister_service(service_id):
    client.agent.service.deregister(service_id = service_id)

def discover_service(service_name):
    _, services = client.health.service(service_name, passing = True)
    # if not services:
    return f"http://{services[0]['Service']['Address']}:{services[0]['Service']['Port']}"