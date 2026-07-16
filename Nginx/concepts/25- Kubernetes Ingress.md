# Overview

As applications grow, managing dozens or even hundreds of Docker containers manually becomes impractical.

Kubernetes automates:

- Container deployment
- Scaling
- Self-healing
- Service discovery
- Rolling updates

However, applications running inside a Kubernetes cluster still need a way to receive external traffic.

This is where **Ingress** comes into the picture.

An **Ingress Controller** (commonly Nginx Ingress Controller) acts as a reverse proxy and load balancer for Kubernetes applications.

---

# What is Kubernetes Ingress?

Ingress is a Kubernetes resource that defines how external HTTP and HTTPS traffic reaches services inside a cluster.

Instead of exposing every application individually, a single Ingress Controller manages incoming traffic.

```text
Internet

    │

    ▼

Nginx Ingress Controller

    │

    ▼

Kubernetes Services

    │

    ▼

Pods
```

---

# Why Ingress?

Without Ingress:

```text
Internet

│

├── Service A

├── Service B

├── Service C
```

Every service requires its own public IP or Load Balancer.

Problems:

- Expensive
- Difficult to manage
- Hard to secure
- Difficult to maintain SSL certificates

---

With Ingress:

```text
Internet

      │

      ▼

Nginx Ingress

      │

 ┌────┴────┐

 ▼         ▼

API      Frontend

      │

      ▼

 Kubernetes Services
```

Only one entry point is required.

---

# Kubernetes Networking

Typical request flow:

```text
Browser

      │

      ▼

Ingress Controller

      │

      ▼

Service

      │

      ▼

Pod
```

Each layer has a different responsibility.

---

# Understanding the Components

## Pod

A Pod contains one or more containers.

Example:

```text
Pod

↓

FastAPI Container
```

Pods are temporary.

If one fails, Kubernetes creates another.

---

## Service

A Service provides a stable network endpoint for Pods.

```text
Service

↓

Pod 1

Pod 2

Pod 3
```

The Service automatically forwards requests to healthy Pods.

---

## Ingress

Ingress routes external traffic to Services.

```text
Internet

↓

Ingress

↓

Service

↓

Pods
```

Ingress never communicates directly with Pods.

---

# What is an Ingress Controller?

Ingress rules are only configuration.

An **Ingress Controller** reads these rules and applies them.

Popular controllers include:

- Nginx Ingress Controller
- Traefik
- HAProxy
- Kong

The most widely used is:

```
Nginx Ingress Controller
```

---

# Request Flow

```text
Browser

      │

HTTPS

      │

      ▼

Nginx Ingress Controller

      │

Ingress Rules

      │

      ▼

Kubernetes Service

      │

      ▼

Application Pods
```

---

# Host-Based Routing

Different domains can route to different applications.

Example:

```text
api.example.com

↓

API Service

--------------------

admin.example.com

↓

Admin Service
```

---

Example Ingress:

```yaml
spec:

  rules:

  - host: api.example.com
```

---

# Path-Based Routing

Ingress can also route based on URL paths.

Example:

```text
example.com/api

↓

API Service

--------------------

example.com/admin

↓

Admin Service

--------------------

example.com

↓

Frontend
```

---

Example:

```yaml
paths:

- path: /api

- path: /admin
```

---

# Basic Ingress Example

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

            name: web-service

            port:

              number: 80
```

This forwards requests to:

```
web-service
```

---

# HTTPS with Ingress

Ingress can terminate TLS.

Example:

```yaml
tls:

- hosts:

  - example.com

  secretName: tls-secret
```

The certificate is stored as a Kubernetes Secret.

---

# TLS Secret

Certificate:

```
server.crt
```

Private Key:

```
server.key
```

Stored inside Kubernetes:

```text
TLS Secret

↓

Ingress

↓

HTTPS Enabled
```

---

# Load Balancing

Suppose three Pods exist.

```text
Service

│

├── Pod 1

├── Pod 2

└── Pod 3
```

Ingress forwards requests to the Service.

The Service distributes traffic across healthy Pods.

---

# Scaling

Initially:

```text
FastAPI

↓

1 Pod
```

Later:

```text
FastAPI

↓

Pod 1

Pod 2

Pod 3

Pod 4
```

Ingress configuration does not change.

Kubernetes automatically updates the Service.

---

# Microservices Example

```text
                 Internet

                     │

                     ▼

          Nginx Ingress Controller

       ┌─────────────┼─────────────┐

       ▼             ▼             ▼

 User Service   Order Service   Payment Service

       │             │             │

       ▼             ▼             ▼

     Pods          Pods          Pods
```

---

# Nginx vs Nginx Ingress

| Nginx | Nginx Ingress Controller |
|--------|--------------------------|
| Standalone Web Server | Runs inside Kubernetes |
| Manages Local Configuration | Reads Kubernetes Resources |
| Manual Reload | Automatic Configuration Updates |
| Used Outside Kubernetes | Designed for Kubernetes |

---

# Benefits

- Single entry point
- Automatic load balancing
- HTTPS termination
- Host-based routing
- Path-based routing
- Kubernetes-native configuration
- Automatic scaling support
- Centralized traffic management

---

# Real-World Example

Production architecture:

```text
                    Internet

                        │

                    HTTPS

                        │

                        ▼

            Nginx Ingress Controller

        ┌───────────────┼───────────────┐

        ▼               ▼               ▼

   Frontend        FastAPI API      Admin API

        │               │               │

        ▼               ▼               ▼

      Service        Service        Service

        │               │               │

        ▼               ▼               ▼

      Pods           Pods           Pods
```

Ingress handles:

- HTTPS
- Routing
- Load balancing
- SSL termination

Applications focus only on business logic.

---

# Best Practices

- Use a single Ingress Controller per cluster unless multiple controllers are required.
- Store certificates as Kubernetes Secrets.
- Use HTTPS for all production traffic.
- Keep Ingress rules simple and organized.
- Use host-based routing for multiple applications.
- Monitor Ingress logs and metrics.
- Apply rate limiting and security annotations where supported by the Ingress Controller.

---

# Common Mistakes

## Exposing Every Service

Creating a LoadBalancer Service for every application increases cost and complexity.

Use a single Ingress whenever possible.

---

## Bypassing the Ingress

Applications should generally be accessed through the Ingress Controller rather than exposing Pods directly.

---

## Forgetting TLS

Without HTTPS, client communication is unencrypted.

Always configure TLS for production deployments.

---

## Hardcoding Pod Addresses

Pods are temporary and their IP addresses change.

Always communicate through Kubernetes Services.

---

# Interview Notes

### Beginner Questions

- What is Kubernetes Ingress?
- Why do we need an Ingress Controller?
- What is the difference between a Service and an Ingress?
- What is host-based routing?

---

### Intermediate Questions

- Explain the request flow from Browser to Pod.
- What is the difference between Nginx and Nginx Ingress Controller?
- How does Ingress perform load balancing?
- Why should Services be used instead of Pod IPs?
- How is HTTPS configured in Kubernetes Ingress?

---

# Key Takeaways

- Kubernetes Ingress provides a centralized entry point for HTTP and HTTPS traffic into a cluster.
- The Nginx Ingress Controller acts as a reverse proxy, routing requests to Kubernetes Services based on hostnames and URL paths.
- Ingress supports TLS termination, load balancing, and scalable traffic management.
- Services provide stable endpoints for Pods, allowing applications to scale without changing Ingress configuration.
- Nginx Ingress is a foundational component of production Kubernetes deployments and is widely used in cloud-native architectures.