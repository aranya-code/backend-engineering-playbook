# Overview

In a production environment, services can fail for many reasons, including application crashes, network failures, database outages, memory exhaustion, or deployment issues. Even though a service process may still be running, it does not necessarily mean that it is capable of serving requests correctly.

If clients continue sending requests to an unhealthy service instance, they may experience increased latency, timeouts, or failed RPC calls.

To solve this problem, gRPC provides **Health Checking**.

Health checks allow clients, load balancers, orchestration platforms, and service discovery systems to determine whether a gRPC service is healthy and ready to receive requests.

Health checking plays a vital role in production deployments by ensuring that traffic is routed only to healthy service instances, thereby improving reliability, fault tolerance, and availability.

This chapter explains how gRPC Health Checks work, the standard gRPC Health Checking Protocol, and how health checks integrate with load balancing, Kubernetes, and service discovery.

---

# Why Health Checks are Needed

Consider three instances of an Order Service.

```text
Order Service

├── Instance A

├── Instance B

└── Instance C
```

Suppose Instance B loses its database connection.

Although the process is still running, every request fails.

Without health checks:

```text
Load Balancer

↓

Instance A

Instance B ❌

Instance C
```

Traffic continues reaching the failed instance.

With health checks:

```text
Load Balancer

↓

Instance A

Instance C
```

Instance B is automatically removed until it becomes healthy again.

---

# What is a Health Check?

A health check is a mechanism that determines whether a service is capable of handling requests.

Instead of assuming that a server is healthy because it is running, health checks verify the service status.

Communication flow:

```text
Health Checker

        │

Health Request

        ▼

gRPC Server

        │

Health Status

        ▼

Health Checker
```

The returned status determines whether the service should receive traffic.

---

# The gRPC Health Checking Protocol

gRPC defines a standard Health Checking Protocol.

Instead of every application inventing its own API, all services can expose the same health interface.

Example:

```proto
service Health {

    rpc Check(HealthCheckRequest)
        returns (HealthCheckResponse);

}
```

Many gRPC libraries provide this implementation out of the box.

---

# Health Status Values

The standard protocol defines several health states.

| Status | Meaning |
|---------|---------|
| `SERVING` | Service is healthy and ready |
| `NOT_SERVING` | Service cannot process requests |
| `SERVICE_UNKNOWN` | Service name is unknown |

Clients and infrastructure components use these values to make routing decisions.

---

# Health Check Workflow

A typical workflow looks like this.

```text
Service Starts

        │

Registers Health Service

        │

Health Checker

        │

Periodic Check

        │

Healthy?

    ┌────┴────┐

   Yes        No

    │          │

Receive     Remove
Traffic      From Pool
```

Health checks are usually performed continuously throughout the lifetime of the service.

---

# Implementing Health Checks

Most Python gRPC applications use the built-in health checking library.

The server registers a Health service alongside the application services.

```text
gRPC Server

├── Employee Service

├── Order Service

└── Health Service
```

This allows infrastructure components to query the server's health without invoking business logic.

---

# Health Check Request

A health check request is very lightweight.

```text
Client

↓

Health Request

↓

Health Service

↓

SERVING
```

The response contains only the current health status.

---

# Service-Specific Health Checks

A single server may host multiple services.

Example:

```text
gRPC Server

├── User Service

├── Order Service

├── Payment Service
```

Each service can have its own health status.

Example:

```text
User Service

SERVING

Order Service

SERVING

Payment Service

NOT_SERVING
```

This allows traffic to continue reaching healthy services while isolating unhealthy ones.

---

# Readiness vs Liveness

Health checks generally fall into two categories.

## Liveness Check

Determines whether the application process is still running.

```text
Application Running?

↓

Yes

↓

Alive
```

If the liveness check fails, the application is usually restarted.

---

## Readiness Check

Determines whether the application is ready to serve requests.

Example checks include:

- Database connectivity
- Cache availability
- Message broker connection
- Required configuration loaded

If readiness fails:

```text
Application

↓

Running

↓

Not Ready

↓

No Traffic
```

The application remains running but is removed from the load balancer.

---

# Health Checks and Load Balancing

Health checks work closely with load balancing.

```text
Load Balancer

        │

Health Check

        │

Healthy Servers

        │

Route Traffic
```

Only healthy instances receive new requests.

---

# Health Checks and Service Discovery

Service discovery systems also rely on health information.

```text
Service Registry

↓

Health Checks

↓

Healthy Services

↓

Client Lookup
```

Unhealthy instances are removed from the registry until they recover.

---

# Health Checks in Kubernetes

Kubernetes uses probes to monitor applications.

Common probes include:

- Liveness Probe
- Readiness Probe
- Startup Probe

Example workflow:

```text
Pod

↓

Readiness Probe

↓

Ready?

↓

Receive Traffic
```

If the readiness probe fails, Kubernetes removes the Pod from the Service endpoints.

---

# Failure Detection

Suppose a service loses database connectivity.

```text
Database Failure

↓

Health Check Fails

↓

Status

NOT_SERVING

↓

Load Balancer Stops Routing
```

Once the database becomes available again:

```text
Database Restored

↓

Health Check

↓

SERVING

↓

Traffic Resumes
```

Recovery is automatic.

---

# Real-World Example

Consider a Payment Service.

The service depends on:

- PostgreSQL
- Redis
- Kafka

The readiness check verifies all dependencies.

```text
Database ✔

Redis ✔

Kafka ✘

↓

NOT_SERVING
```

The service remains online but does not receive traffic until Kafka becomes available.

---

# Advantages of Health Checks

Health checks provide several benefits.

- Improved reliability
- Automatic failure detection
- Better fault tolerance
- Reduced downtime
- Automatic recovery
- Improved load balancing
- Better service discovery
- Faster incident response

They are an essential part of production infrastructure.

---

# Best Practices

- Implement the standard gRPC Health Checking Protocol.
- Separate liveness and readiness checks.
- Keep health checks lightweight and fast.
- Verify critical dependencies during readiness checks.
- Return accurate health status.
- Integrate health checks with load balancers and orchestration platforms.
- Monitor health check failures and recovery events.

---

# Common Mistakes

Avoid the following mistakes:

- Assuming a running process is healthy.
- Performing expensive operations during health checks.
- Returning `SERVING` when critical dependencies are unavailable.
- Ignoring readiness checks.
- Performing health checks too frequently or too infrequently.
- Exposing sensitive system information through health endpoints.

---

# Key Takeaways

- Health checks determine whether a gRPC service is capable of processing requests.
- The gRPC Health Checking Protocol provides a standard interface for reporting service health.
- Health status values such as `SERVING` and `NOT_SERVING` enable infrastructure components to make routing decisions.
- Health checks work closely with load balancing, service discovery, and Kubernetes to ensure traffic reaches only healthy instances.
- Separating liveness and readiness checks improves application resilience and operational reliability.
- Properly implemented health checks are essential for building highly available and production-ready gRPC services.