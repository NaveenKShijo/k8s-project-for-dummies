# Microservices on Kubernetes — A Hands-On Learning Project

A practical, beginner-friendly project that builds **two Python (FastAPI) microservices** and deploys them with a full production-style infrastructure stack — first with **Docker Compose** (for local dev), then on a **Kubernetes cluster** (for orchestration).

> **What you'll learn by exploring this repo:**
> - How microservices communicate with each other
> - Service Discovery with **Consul**
> - Asynchronous messaging with **RabbitMQ**
> - Metrics & monitoring with **Prometheus**
> - Containerisation with **Docker**
> - Container orchestration with **Kubernetes**

---

##  Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                        │
│                                                                  │
│   ┌──────────────┐        ┌──────────────┐                       │
│   │ Order Service │◄──────►│ User Service  │                      │
│   │  (FastAPI)    │  HTTP  │  (FastAPI)    │                      │
│   │  Port: 8000   │        │  Port: 8000   │                      │
│   └──────┬───────┘        └──────┬───────┘                       │
│          │                       │                                │
│          │  ┌────────────────────┘                                │
│          │  │                                                     │
│          ▼  ▼                                                     │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│   │   Consul      │    │  RabbitMQ     │    │  Prometheus   │      │
│   │  (Discovery)  │    │  (Messaging)  │    │ (Monitoring)  │      │
│   │  Port: 8500   │    │  Port: 5672   │    │  Port: 9090   │      │
│   └──────────────┘    │  UI:   15672  │    └──────────────┘       │
│                        └──────────────┘                           │
└──────────────────────────────────────────────────────────────────┘
```

### How the services interact

| Flow | Description |
|------|-------------|
| **Order → User** | Order Service calls `GET /hello` on User Service via Consul service discovery |
| **Order → RabbitMQ** | Order Service publishes order events to the `order_exchange` (topic exchange) |
| **RabbitMQ → User** | User Service consumes messages from `users_queue` bound to `order.*` routing key |
| **Both → Consul** | Both services register themselves on startup and deregister on shutdown |
| **Prometheus → Both** | Prometheus scrapes `/metrics` endpoints on both services every 15 seconds |

---

## 📁 Project Structure

```
├── order-service/              # Order microservice
│   ├── orders.py               # FastAPI app — endpoints & RabbitMQ publisher
│   ├── consul_helper.py        # Consul register / deregister / discover helpers
│   ├── metrics.py              # Custom Prometheus counters & histograms
│   ├── Dockerfile              # Container image definition
│   └── requirements.txt        # Python dependencies
│
├── user-service/               # User microservice
│   ├── users.py                # FastAPI app — endpoints & RabbitMQ consumer
│   ├── consul_helper.py        # Consul register / deregister / discover helpers
│   ├── Dockerfile              # Container image definition
│   └── requirements.txt        # Python dependencies
│
├── k8s/                        # Kubernetes manifests (one sub-folder per component)
│   ├── order-service/
│   │   ├── deployment.yaml     # 5 replicas, image: order-k8s:v3
│   │   └── service.yaml        # NodePort 30800
│   ├── user-service/
│   │   ├── deployment.yaml     # 2 replicas, image: user-k8s:v2
│   │   └── service.yaml        # NodePort 30801
│   ├── consul/
│   │   ├── deployment.yaml     # 3 replicas, hashicorp/consul
│   │   └── service.yaml        # NodePort 30150
│   ├── rabbitmq/
│   │   ├── deployment.yaml     # 3 replicas, rabbitmq:3-management
│   │   └── service.yaml        # NodePort 30250 (UI), 30300 (AMQP)
│   └── prometheus/
│       ├── configmap.yaml      # Prometheus scrape config (replaces prometheus.yml)
│       ├── deployment.yaml     # 3 replicas, prom/prometheus
│       └── service.yaml        # NodePort 30200
│
├── docker-compose.yaml         # Docker Compose deployment (local dev)
├── prometheus.yml              # Prometheus config (used ONLY by Docker Compose)
└── readme.md                   # ← You are here
```

---

## 🛠 Prerequisites

Make sure you have these installed before starting:

| Tool | Purpose | Install Guide |
|------|---------|---------------|
| **Docker** | Build container images | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) |
| **kubectl** | Interact with K8s cluster | [kubernetes.io/docs/tasks/tools](https://kubernetes.io/docs/tasks/tools/) |
| **kind** | Run a local K8s cluster in Docker | [kind.sigs.k8s.io/docs/user/quick-start](https://kind.sigs.k8s.io/docs/user/quick-start/) |

> **Note:** This project uses [kind](https://kind.sigs.k8s.io/) (Kubernetes IN Docker) to create a local cluster. You can also use **minikube** or **Docker Desktop's built-in Kubernetes** — the manifests work the same way.

---

## 🐳 Option 1 — Run with Docker Compose (Quick Start)

This is the fastest way to get everything running locally. Docker Compose handles building images, creating a shared network, and starting all containers.

### 1. Start all services

```bash
docker compose up -d
```

This launches 5 containers: `order-service`, `user-service`, `consul`, `rabbitmq`, and `prometheus`.

### 2. Test the endpoints

```bash
# Order Service — homepage
curl http://localhost:8000/hello
# → {"Message": "This is Orders page"}

# User Service — homepage
curl http://localhost:8001/hello
# → {"Message": "This is User page"}

# Order → User (via Consul discovery)
curl http://localhost:8000/users
# → {"User response": {"Message": "This is User page"}}

# Publish a message to RabbitMQ
curl http://localhost:8000/rabbitmq
# → {"Response": "Message published"}
```

### 3. Access the dashboards

| Dashboard | URL |
|-----------|-----|
| Prometheus | [http://localhost:9090](http://localhost:9090) |
| RabbitMQ Management UI | [http://localhost:15672](http://localhost:15672) (guest / guest) |
| Consul UI | [http://localhost:8500](http://localhost:8500) |

### 4. Shut everything down

```bash
docker compose down
```

> **⚠️ Important:** When switching between Docker Compose and Kubernetes, you need to change which `register_service()` line is active in both `orders.py` and `users.py`. The Docker Compose version uses container names (e.g., `order-kuber`), while K8s uses K8s service names (e.g., `order-service`). See the comments in the code.

---

## ☸️ Option 2 — Deploy on Kubernetes (Full Orchestration)

This is the real deal. You'll create a local Kubernetes cluster, build and load your images, and deploy everything using manifests.

### Step 1 — Create a kind cluster

```bash
kind create cluster --name firstcluster
```

Verify it's running:

```bash
kubectl cluster-info
kubectl get nodes
```

### Step 2 — Build Docker images

```bash
# Build the Order Service image
docker build -t order-k8s:v3 -f order-service/Dockerfile .

# Build the User Service image
docker build -t user-k8s:v2 -f user-service/Dockerfile .
```

### Step 3 — Load images into the kind cluster

Since kind runs inside Docker, it can't pull from your local Docker daemon by default. You must explicitly load images:

```bash
kind load docker-image order-k8s:v3 --name firstcluster
kind load docker-image user-k8s:v2 --name firstcluster
```

> **Why is this needed?** kind clusters run in their own Docker containers with a separate image store. `kind load` copies your locally built images into the cluster nodes so `imagePullPolicy: Never` works.

### Step 4 — Deploy all manifests

```bash
kubectl apply -R -f k8s/
```

The `-R` flag applies manifests **recursively** through all sub-folders — deploying order-service, user-service, consul, rabbitmq, and prometheus in one command.

### Step 5 — Verify the deployment

```bash
# Check all deployments are ready
kubectl get deployments

# Check all pods are running
kubectl get pods

# Check all services and their NodePorts
kubectl get services
```

You should see output similar to:

```
NAME            READY   UP-TO-DATE   AVAILABLE
consul          3/3     3            3
order-service   5/5     5            5
prometheus      3/3     3            3
rabbitmq        3/3     3            3
user-service    2/2     2            2
```

### Step 6 — Test the endpoints

Since kind doesn't expose NodePorts to `localhost` by default, use `docker exec` to curl from inside the cluster node:

```bash
# Order Service
docker exec -it firstcluster-control-plane curl http://localhost:30800/hello
# → {"Message":"This is Orders page"}

# User Service
docker exec -it firstcluster-control-plane curl http://localhost:30801/hello
# → {"Message":"This is User page"}

# Cross-service call (Order → User via Consul)
docker exec -it firstcluster-control-plane curl http://localhost:30800/users
# → {"User response": {"Message": "This is User page"}}

# Publish to RabbitMQ
docker exec -it firstcluster-control-plane curl http://localhost:30800/rabbitmq
# → {"Response": "Message published"}
```

### Step 7 — Access dashboards (port-forward)

To access the web UIs from your browser, use `kubectl port-forward`:

```bash
# Prometheus UI → http://localhost:9090
kubectl port-forward svc/prometheus 9090:9090

# RabbitMQ Management UI → http://localhost:15672
kubectl port-forward svc/rabbitmq 15672:15672

# Consul UI → http://localhost:8500
kubectl port-forward svc/consul 8500:8500
```

---

## 🔌 API Endpoints Reference

### Order Service (port 8000 / NodePort 30800)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/hello` | Returns a hello message from the order service |
| `GET` | `/health` | Health check endpoint |
| `GET` | `/users` | Discovers User Service via Consul and calls its `/hello` endpoint |
| `GET` | `/rabbitmq` | Publishes a sample order event to RabbitMQ |
| `GET` | `/metrics` | Prometheus metrics (auto-generated by `prometheus_fastapi_instrumentator`) |

### User Service (port 8000 / NodePort 30801)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/hello` | Returns a hello message from the user service |
| `GET` | `/health` | Health check endpoint |

> The User Service also runs a **background RabbitMQ consumer** thread that listens on the `users_queue` for messages matching the `order.*` routing key pattern.

---

## 🧩 NodePort Quick Reference (Kubernetes)

| Service | NodePort | Internal Port |
|---------|----------|---------------|
| Order Service | `30800` | `8000` |
| User Service | `30801` | `8000` |
| Consul | `30150` | `8500` |
| Prometheus | `30200` | `9090` |
| RabbitMQ UI | `30250` | `15672` |
| RabbitMQ AMQP | `30300` | `5672` |

---

## 🔑 Key Concepts Demonstrated

### 🔍 Service Discovery (Consul)

Instead of hardcoding service URLs, both services **register** themselves with Consul on startup. When Order Service needs to talk to User Service, it **discovers** the address at runtime:

```python
# consul_helper.py
def discover_service(service_name):
    _, services = client.health.service(service_name, passing=True)
    return f"http://{services[0]['Service']['Address']}:{services[0]['Service']['Port']}"
```

This makes the system resilient — services can move, scale, or restart without breaking communication.

### 📬 Asynchronous Messaging (RabbitMQ)

Order Service **publishes** order events to a topic exchange. User Service runs a **background consumer thread** that picks up these messages asynchronously:

```
Order Service  ──publish──►  order_exchange  ──route──►  users_queue  ──consume──►  User Service
                             (topic exchange)            (order.* key)              (background thread)
```

### 📊 Monitoring (Prometheus)

- `prometheus_fastapi_instrumentator` automatically exposes HTTP request metrics at `/metrics`
- Custom metrics are defined in `metrics.py` (counters for orders, failures; histogram for processing time)
- Prometheus scrapes both services every 15 seconds

### 🐳 → ☸️ Docker Compose vs Kubernetes

| Aspect | Docker Compose | Kubernetes |
|--------|---------------|------------|
| **Networking** | Containers share a Docker bridge network; use container names | Pods use K8s internal DNS; use Service names |
| **Config files** | `prometheus.yml` mounted as a volume | `ConfigMap` mounted into the pod |
| **Scaling** | Manual (`docker compose up --scale`) | Declarative (`replicas: 5` in deployment.yaml) |
| **Service discovery** | Container names resolve automatically | K8s Services + Consul for app-level discovery |
| **Health checks** | Restart policies only | Liveness/readiness probes (can be added) |

---

## 🧹 Cleanup

### Docker Compose

```bash
docker compose down
```

### Kubernetes (kind)

```bash
# Delete all deployed resources
kubectl delete -R -f k8s/

# Delete the entire cluster
kind delete cluster --name firstcluster
```

---

## 📚 Further Reading

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kubernetes Concepts](https://kubernetes.io/docs/concepts/)
- [kind — Quick Start](https://kind.sigs.k8s.io/docs/user/quick-start/)
- [Consul Service Discovery](https://developer.hashicorp.com/consul/docs/concepts/service-discovery)
- [RabbitMQ Tutorials](https://www.rabbitmq.com/tutorials)
- [Prometheus Getting Started](https://prometheus.io/docs/prometheus/latest/getting_started/)
