# What is Ingress?

An **Ingress** is a Kubernetes API object that manages **external HTTP and HTTPS traffic** to services inside a Kubernetes cluster.

It acts as a **single entry point** for all incoming web traffic.

Instead of exposing every application using its own IP address or LoadBalancer, Ingress routes requests to the correct Service based on rules.

---

# Why Do We Need Ingress?

Suppose you have three applications running in Kubernetes.

- Frontend
- Backend API
- Admin Portal

Without Ingress

```
Internet
     │
     ├── LoadBalancer (Frontend)
     │
     ├── LoadBalancer (Backend)
     │
     └── LoadBalancer (Admin)
```

Problems

- Multiple public IPs
- Higher cloud cost
- Difficult SSL management
- Hard to manage routing

---

With Ingress

```
                Internet
                    │
            Ingress Controller
                    │
        ┌───────────┼───────────┐
        │           │           │
   Frontend     Backend      Admin
    Service      Service      Service
        │           │           │
      Pods        Pods        Pods
```

Advantages

- Single public IP
- Centralized routing
- SSL termination
- Reduced cloud cost
- Easier management

---

# What is an Ingress Controller?

An Ingress resource only contains routing rules.

Something must actually process those rules.

That component is called the **Ingress Controller**.

Without an Ingress Controller, an Ingress resource does nothing.

Popular Ingress Controllers

- NGINX Ingress Controller
- HAProxy Ingress
- Traefik
- AWS Load Balancer Controller
- Kong Ingress Controller

---

# Traffic Flow

```
User

↓

DNS

↓

Ingress Controller

↓

Service

↓

Pod
```

---

# Ingress vs Service

| Service | Ingress |
|----------|----------|
| Exposes Pods | Routes external traffic |
| Internal networking | External HTTP/HTTPS routing |
| Load balances Pods | Load balances multiple Services |
| Layer 4 (TCP/UDP) | Layer 7 (HTTP/HTTPS) |

---

# Path-Based Routing

Ingress can route traffic based on URL paths.

Example

```
example.com/

↓

Frontend Service
```

```
example.com/api

↓

Backend Service
```

```
example.com/admin

↓

Admin Service
```

Diagram

```
Internet

↓

example.com

│

├── /        → Frontend Service

├── /api     → Backend Service

└── /admin   → Admin Service
```

---

# Host-Based Routing

Ingress can also route traffic based on host names.

Example

```
api.example.com

↓

API Service
```

```
shop.example.com

↓

Shopping Service
```

```
admin.example.com

↓

Admin Service
```

Diagram

```
Internet

↓

Ingress

│

├── api.example.com

├── shop.example.com

└── admin.example.com
```

---

# SSL/TLS Termination

Ingress can manage HTTPS certificates.

```
Internet (HTTPS)

↓

Ingress

↓

HTTP

↓

Services

↓

Pods
```

Benefits

- Secure communication
- Centralized certificate management
- Easier HTTPS configuration

---

# Basic Ingress YAML

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress

metadata:
  name: app-ingress

spec:
  rules:
  - host: example.com

    http:
      paths:
      - path: /
        pathType: Prefix

        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

---

# Multiple Path Example

```yaml
spec:
  rules:
  - host: example.com

    http:

      paths:

      - path: /
        pathType: Prefix

        backend:
          service:
            name: frontend-service
            port:
              number: 80

      - path: /api
        pathType: Prefix

        backend:
          service:
            name: api-service
            port:
              number: 8080
```

---

# Host-Based Example

```yaml
spec:
  rules:

  - host: api.example.com

    http:
      paths:
      - path: /

        pathType: Prefix

        backend:
          service:
            name: api-service

            port:
              number: 80

  - host: shop.example.com

    http:
      paths:
      - path: /

        pathType: Prefix

        backend:
          service:
            name: shop-service

            port:
              number: 80
```

---

# Ingress Architecture

```
                   Internet
                       │
                 DNS Resolution
                       │
               Ingress Controller
                       │
        ┌──────────────┼──────────────┐
        │              │              │
Frontend Service   API Service   Admin Service
        │              │              │
      Pods           Pods          Pods
```

---

# Service vs Ingress Example

Without Ingress

```
Frontend

↓

LoadBalancer

↓

Public IP
```

```
Backend

↓

LoadBalancer

↓

Public IP
```

```
Admin

↓

LoadBalancer

↓

Public IP
```

Three applications require three LoadBalancers.

---

With Ingress

```
Internet

↓

Single LoadBalancer

↓

Ingress Controller

↓

Multiple Services

↓

Pods
```

Only one public entry point is required.

---

# Common Use Cases

## Microservices

```
/users

/orders

/payments

/products
```

Each path routes to a different service.

---

## Multi-Domain Applications

```
api.company.com

admin.company.com

shop.company.com
```

Each hostname routes independently.

---

## SSL Management

Instead of configuring SSL on every application,

Ingress manages certificates in one place.

---

## Cost Optimization

Cloud providers charge for LoadBalancers.

Using one Ingress reduces infrastructure cost.

---

# Advantages

- Single Entry Point
- HTTP Routing
- HTTPS Support
- SSL Termination
- Path Routing
- Host Routing
- Lower Cloud Cost
- Easy Management

---

# Limitations

- Works mainly with HTTP and HTTPS.
- Requires an Ingress Controller.
- Not suitable for every TCP/UDP protocol (Gateway API is becoming the modern alternative for advanced use cases).

---

# Useful Commands

View Ingresses

```bash
kubectl get ingress
```

Describe an Ingress

```bash
kubectl describe ingress app-ingress
```

Apply an Ingress

```bash
kubectl apply -f ingress.yaml
```

Delete an Ingress

```bash
kubectl delete ingress app-ingress
```

---

# Interview Questions

## What is Ingress?

Ingress is a Kubernetes resource that manages external HTTP/HTTPS access to Services inside a cluster.

---

## Why do we need Ingress?

Ingress provides a single entry point, supports path-based and host-based routing, SSL termination, and reduces the need for multiple LoadBalancers.

---

## What is an Ingress Controller?

An Ingress Controller is the component that watches Ingress resources and implements the routing rules.

---

## Can Ingress work without an Ingress Controller?

No.

The Ingress object only defines routing rules. An Ingress Controller is required to enforce those rules.

---

## Difference between Service and Ingress?

| Service | Ingress |
|----------|----------|
| Exposes Pods | Routes traffic to Services |
| Internal communication | External communication |
| Layer 4 | Layer 7 |
| Load balances Pods | Routes multiple Services |

---

## Name some popular Ingress Controllers.

- NGINX Ingress Controller
- Traefik
- HAProxy
- Kong
- AWS Load Balancer Controller

---

# Real-World Example

Suppose an e-commerce application has the following microservices:

```
shop.example.com           → Frontend

shop.example.com/api       → Backend API

shop.example.com/admin     → Admin Portal

shop.example.com/payment   → Payment Service
```

A single Ingress routes each request to the appropriate Service, simplifying networking, reducing cloud costs, and centralizing SSL management.

---

# Key Takeaways

- Ingress is the entry point for external HTTP/HTTPS traffic.
- It routes requests to Kubernetes Services.
- Ingress requires an Ingress Controller to function.
- Supports path-based and host-based routing.
- Can terminate SSL/TLS connections.
- Reduces the need for multiple cloud LoadBalancers.
- Commonly used in production Kubernetes environments for microservices.