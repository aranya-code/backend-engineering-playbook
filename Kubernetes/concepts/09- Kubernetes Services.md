# What is a Kubernetes Service?

A **Service** is a Kubernetes object that provides a **stable network endpoint** for accessing one or more Pods.

Pods are temporary (ephemeral). When a Pod is recreated, its IP address changes.

A Service solves this problem by providing a **permanent IP address and DNS name**.

---

# Why Do We Need Services?

Suppose an application is running in a Pod.

```
Pod

IP = 10.244.1.10
```

The Pod crashes.

```
↓

New Pod Created

↓

IP = 10.244.2.15
```

The IP address changes, causing clients to lose connectivity.

A Service provides a stable endpoint that always routes traffic to the available Pods.

---

# Benefits of Services

- Stable IP Address
- Stable DNS Name
- Load Balancing
- Loose Coupling
- Service Discovery
- Internal Communication
- External Communication

---

# Loose Coupling

Applications should not communicate directly with Pod IP addresses.

Instead, they communicate with the Service.

```
Frontend

↓

Backend Service

↓

Backend Pods
```

If Backend Pods change, the Frontend does not need to know.

---

# Service Architecture

```
Client

↓

Service

↓

Pod 1

Pod 2

Pod 3
```

The Service automatically distributes traffic among healthy Pods.

---

# Service Discovery

Each Service gets a DNS name.

Example

```
backend.default.svc.cluster.local
```

Applications communicate using the Service name instead of IP addresses.

---

# Kubernetes Service Types

Kubernetes provides four primary Service types.

```
Service

├── ClusterIP
├── NodePort
├── LoadBalancer
└── Headless Service
```

---

# 1. ClusterIP

ClusterIP is the **default Service type**.

It exposes the application **only inside the Kubernetes cluster**.

```
Client

↓

ClusterIP Service

↓

Pods
```

Characteristics

- Internal communication only
- Default Service type
- Used between microservices

Example

Frontend API calls Backend API inside the cluster.

---

# ClusterIP YAML

```yaml
apiVersion: v1
kind: Service

metadata:
  name: backend-service

spec:
  selector:
    app: backend

  ports:
    - port: 80
      targetPort: 8000

  type: ClusterIP
```

---

# 2. NodePort

NodePort exposes an application outside the cluster.

Kubernetes opens the same port on every worker node.

```
Internet

↓

Node IP:30080

↓

Service

↓

Pods
```

Characteristics

- Accessible externally
- Uses ports between **30000–32767**
- Suitable for testing and development

Example

```
http://192.168.1.20:30080
```

---

# NodePort YAML

```yaml
spec:
  type: NodePort

  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080
```

---

# 3. LoadBalancer

LoadBalancer exposes an application using a cloud provider's load balancer.

Supported by

- AWS
- Azure
- Google Cloud

```
Internet

↓

Cloud Load Balancer

↓

Service

↓

Pods
```

Characteristics

- Public IP Address
- Cloud Managed
- High Availability
- Automatic Load Balancing

---

# LoadBalancer YAML

```yaml
spec:
  type: LoadBalancer

  ports:
  - port: 80
    targetPort: 8080
```

---

# 4. Headless Service

A Headless Service does **not** provide a Cluster IP.

Instead, it returns the individual DNS names of each Pod.

```
Headless Service

↓

mysql-0

mysql-1

mysql-2
```

Used mainly with

- StatefulSets
- Databases
- Distributed systems

---

# Service Types Comparison

| Service Type | Internal | External | Load Balancing | Use Case |
|--------------|----------|----------|----------------|----------|
| ClusterIP | ✅ | ❌ | ✅ | Internal microservices |
| NodePort | ✅ | ✅ | ✅ | Development & Testing |
| LoadBalancer | ✅ | ✅ | ✅ | Production applications |
| Headless | ✅ | DNS only | ❌ | Stateful applications |

---

# Service Flow

## ClusterIP

```
Frontend

↓

ClusterIP

↓

Backend Pods
```

---

## NodePort

```
Internet

↓

Worker Node

↓

NodePort

↓

Pods
```

---

## LoadBalancer

```
Internet

↓

Cloud Load Balancer

↓

Service

↓

Pods
```

---

## Headless Service

```
Application

↓

Headless Service

↓

Pod DNS Names

↓

Individual Pods
```

---

# Service Selectors

Services use **Labels and Selectors** to determine which Pods receive traffic.

Example

Pods

```yaml
labels:
  app: backend
```

Service

```yaml
selector:
  app: backend
```

Only matching Pods receive traffic.

---

# Endpoints

When a Service is created, Kubernetes automatically creates an **Endpoint** object.

Endpoints contain the IP addresses of the Pods selected by the Service.

```
Service

↓

Endpoints

↓

Pod IPs
```

---

# Real-World Example

Suppose you have an e-commerce application.

```
Frontend

↓

Backend Service

↓

Backend Pods

↓

Database Service

↓

PostgreSQL
```

The frontend communicates only with Services.

Pods can restart without affecting the application.

---

# Service vs Ingress

| Service | Ingress |
|----------|----------|
| Connects clients to Pods | Routes HTTP/HTTPS traffic |
| Internal and external communication | External entry point |
| Layer 4 | Layer 7 |
| One application | Multiple applications |

---

# Common Use Cases

## ClusterIP

- Backend APIs
- Database access
- Internal microservices

---

## NodePort

- Local development
- Testing
- Minikube

---

## LoadBalancer

- Public APIs
- Production web applications
- SaaS platforms

---

## Headless

- MySQL Cluster
- PostgreSQL
- MongoDB Replica Set
- Kafka
- Cassandra

---

# Useful Commands

List Services

```bash
kubectl get services
```

Short form

```bash
kubectl get svc
```

Describe a Service

```bash
kubectl describe service backend-service
```

Delete a Service

```bash
kubectl delete service backend-service
```

View Endpoints

```bash
kubectl get endpoints
```

---

# Interview Questions

## What is a Kubernetes Service?

A Service is a Kubernetes resource that provides a stable network endpoint for accessing one or more Pods.

---

## Why do we need Services?

Services provide stable IP addresses, load balancing, service discovery, and loose coupling between applications.

---

## What is ClusterIP?

ClusterIP is the default Service type that exposes an application only within the Kubernetes cluster.

---

## What is NodePort?

NodePort exposes an application externally by opening a port on every worker node.

---

## What is LoadBalancer?

LoadBalancer creates a cloud provider-managed load balancer to expose an application to the internet.

---

## What is a Headless Service?

A Headless Service does not allocate a Cluster IP. Instead, it provides direct DNS records for individual Pods and is commonly used with StatefulSets.

---

## Difference between ClusterIP and NodePort?

| ClusterIP | NodePort |
|------------|-----------|
| Internal only | Internal + External |
| Default Service | Requires NodePort |
| Used for microservices | Used for testing |

---

## Difference between NodePort and LoadBalancer?

NodePort exposes an application using a port on each worker node, while LoadBalancer provisions a cloud load balancer with a public IP.

---

# Key Takeaways

- Services provide stable networking for Pods.
- Services decouple clients from changing Pod IP addresses.
- Kubernetes supports four main Service types:
  - ClusterIP
  - NodePort
  - LoadBalancer
  - Headless Service
- Services use Labels and Selectors to route traffic.
- Endpoints store the IP addresses of matching Pods.
- ClusterIP is used for internal communication.
- NodePort is suitable for development and testing.
- LoadBalancer is preferred for production deployments on cloud platforms.
- Headless Services are commonly used with StatefulSets and databases.