# Overview

In a distributed system, services are constantly being created, scaled, updated, and removed. Unlike traditional monolithic applications where the server address rarely changes, modern microservices often run inside platforms such as Kubernetes, Docker Swarm, or cloud environments where service instances are dynamic.

This creates a fundamental challenge:

**How does a client know where a service is located?**

Hardcoding IP addresses or hostnames is not practical because service instances may change frequently due to scaling, deployments, failures, or infrastructure updates.

To solve this problem, distributed systems use **Service Discovery**.

Service Discovery enables clients to locate available service instances dynamically without needing to know their physical addresses. It is a critical component of production-grade gRPC deployments and works closely with load balancing to ensure reliable communication.

This chapter explains how Service Discovery works, the different discovery models, common service registries, and best practices for implementing Service Discovery in production environments.

---

# Why Service Discovery is Needed

Consider an application with three services:

```text
User Service

Order Service

Payment Service
```

Initially:

```text
Order Service

↓

10.0.0.5:50051
```

After scaling:

```text
Order Service

↓

10.0.0.5:50051

10.0.0.8:50051

10.0.0.12:50051
```

If the client only knows one IP address, it cannot communicate with the newly created instances.

Service Discovery solves this problem by maintaining a continuously updated list of available service instances.

---

# What is Service Discovery?

Service Discovery is the process of locating available service instances at runtime.

Instead of connecting to a fixed IP address:

```text
Client

↓

10.0.0.5
```

The client asks a discovery system:

```text
Client

↓

Service Registry

↓

Available Instances

↓

Connect
```

The registry returns one or more healthy service instances.

---

# Service Discovery Workflow

A typical workflow looks like this:

```text
Service Starts

        │

Registers Itself

        │

Service Registry

        │

Client Queries Registry

        │

Available Endpoints

        │

Client Connects
```

The registry always knows which instances are currently available.

---

# Components of Service Discovery

A Service Discovery system generally consists of:

- Service Provider
- Service Registry
- Service Consumer

```text
Service

↓

Registers

↓

Registry

↓

Lookup

↓

Client
```

Each component has a specific responsibility.

---

# Service Registration

When a service starts, it registers itself.

Example:

```text
Order Service

↓

Host:
10.0.0.8

↓

Port:
50051

↓

Register
```

The registry stores this information.

When the service shuts down, it unregisters itself.

---

# Service Registry

A Service Registry maintains information about all available services.

Typical information includes:

- Service name
- Host
- Port
- Health status
- Metadata
- Version

Example:

```text
Order Service

↓

10.0.0.5

10.0.0.8

10.0.0.12
```

Clients query the registry instead of using fixed addresses.

---

# Client Lookup

Instead of connecting directly:

```text
Client

↓

10.0.0.5
```

The client performs:

```text
Client

↓

Registry

↓

Order Service

↓

10.0.0.8
```

The selected instance is then used for communication.

---

# Client-Side Service Discovery

In client-side discovery, the client is responsible for selecting a service instance.

Workflow:

```text
Client

↓

Registry

↓

Instance List

↓

Choose Instance

↓

RPC
```

The client typically combines Service Discovery with load balancing.

Examples:

- Consul
- etcd
- ZooKeeper

---

# Server-Side Service Discovery

In server-side discovery, the client communicates with a load balancer or proxy instead of querying the registry directly.

Workflow:

```text
Client

↓

Load Balancer

↓

Registry

↓

Service Instance
```

Examples include:

- Envoy
- NGINX
- HAProxy

The client does not need to know about the registry.

---

# Client-Side vs Server-Side Discovery

| Feature | Client-Side | Server-Side |
|---------|-------------|-------------|
| Client contacts registry | Yes | No |
| Client selects instance | Yes | No |
| Load balancer required | Optional | Yes |
| Client complexity | Higher | Lower |

Both approaches are widely used depending on the system architecture.

---

# Service Discovery in Kubernetes

Kubernetes provides built-in Service Discovery.

Example:

```text
Order Service

↓

order-service.default.svc.cluster.local
```

Clients communicate using the service name rather than individual Pod IP addresses.

Kubernetes automatically updates endpoints as Pods are added or removed.

---

# DNS-Based Discovery

Many environments use DNS for Service Discovery.

Example:

```text
Client

↓

order-service.company.internal

↓

DNS

↓

10.0.0.5
```

The client does not need to know the actual IP address.

---

# Popular Service Discovery Systems

Several platforms provide Service Discovery capabilities.

| Platform | Description |
|----------|-------------|
| Kubernetes | Built-in Service Discovery for Pods and Services |
| Consul | Distributed service registry with health checks |
| etcd | Distributed key-value store commonly used by Kubernetes |
| ZooKeeper | Coordination and discovery for distributed systems |
| Eureka | Service registry commonly used in Spring Cloud environments |

Each provides mechanisms for registering, discovering, and monitoring services.

---

# Service Discovery and Load Balancing

Service Discovery and Load Balancing work together.

```text
Client

↓

Registry

↓

Available Instances

↓

Load Balancer

↓

Selected Instance
```

Discovery finds available instances.

Load balancing chooses which instance should receive the request.

---

# Health Checks

Discovery systems usually monitor service health.

Example:

```text
Registry

↓

Instance A

Healthy

↓

Instance B

Healthy

↓

Instance C

Unhealthy

↓

Removed
```

Only healthy services are returned to clients.

---

# Failure Recovery

Suppose an instance crashes.

```text
Instance

↓

Failure

↓

Health Check Fails

↓

Registry Updates

↓

Clients Receive Updated List
```

Future requests are automatically routed to healthy instances.

---

# Real-World Example

Consider an e-commerce platform.

```text
User Service

Order Service

Inventory Service

Payment Service
```

The Order Service scales from two to ten instances during a sales event.

Instead of changing client configuration, the new instances register automatically with the Service Registry.

Clients immediately begin sending requests to the newly available instances without requiring any code changes.

---

# Advantages of Service Discovery

Service Discovery provides several benefits.

- Eliminates hardcoded addresses
- Supports automatic scaling
- Improves fault tolerance
- Simplifies deployments
- Enables rolling updates
- Supports dynamic infrastructure
- Works seamlessly with load balancing
- Reduces operational overhead

---

# Best Practices

- Register services automatically during startup.
- Remove services during shutdown.
- Perform regular health checks.
- Use DNS or Kubernetes Services whenever possible.
- Avoid hardcoding IP addresses.
- Keep service metadata up to date.
- Combine Service Discovery with load balancing for high availability.

---

# Common Mistakes

Avoid the following mistakes:

- Hardcoding service IP addresses.
- Returning unhealthy instances from the registry.
- Failing to unregister terminated services.
- Ignoring health check failures.
- Creating duplicate service registrations.
- Depending on manual configuration for dynamic environments.

---

# Key Takeaways

- Service Discovery enables clients to locate service instances dynamically at runtime.
- Services register themselves with a registry, allowing clients to discover available endpoints without hardcoded addresses.
- Client-side and server-side discovery are the two primary Service Discovery models.
- Kubernetes provides built-in Service Discovery using DNS-based service names.
- Service Discovery works closely with load balancing and health checks to ensure reliable communication.
- It is an essential component of scalable, resilient, and production-ready gRPC systems.