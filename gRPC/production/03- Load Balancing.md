# Overview

As applications grow, a single gRPC server is rarely enough to handle all incoming requests. Production systems typically run multiple instances of the same service to improve scalability, availability, and fault tolerance.

Consider an Order Service handling thousands of requests per second. Running only one instance creates a single point of failure and limits the system's capacity. By deploying multiple instances behind a load balancer, requests can be distributed efficiently across all available servers.

This process is known as **Load Balancing**.

Load balancing is one of the most important concepts in distributed systems. It ensures that no single server becomes overloaded while others remain idle. Combined with Service Discovery and Health Checks, load balancing enables highly available and scalable gRPC applications.

This chapter explains how load balancing works in gRPC, the different load balancing strategies, and best practices for deploying production-ready services.

---

# What is Load Balancing?

Load balancing is the process of distributing incoming requests across multiple service instances.

Instead of sending every request to a single server:

```text
          Client
             │
             ▼
      Order Service
```

Requests are distributed among multiple servers.

```text
                Client
                   │
                   ▼
            Load Balancer
          ┌──────┼──────┐
          ▼      ▼      ▼
      Server 1 Server 2 Server 3
```

Each server processes a portion of the total workload.

---

# Why Load Balancing is Needed

Imagine an Order Service deployed on a single server.

```text
1000 Requests

        │

        ▼

Single Server
```

If the server becomes overloaded:

- Response times increase
- Requests begin timing out
- CPU utilization reaches 100%
- Memory consumption grows
- The service may crash

Now consider three servers.

```text
1000 Requests

        │

        ▼

Load Balancer

   ┌────┼────┐

   ▼    ▼    ▼

333  333  334
```

Each server handles approximately one-third of the workload.

---

# Benefits of Load Balancing

Load balancing provides several advantages:

- Better scalability
- High availability
- Improved fault tolerance
- Reduced latency
- Better resource utilization
- Easier horizontal scaling
- Automatic traffic distribution

It is a fundamental building block of modern distributed systems.

---

# Load Balancing Workflow

A typical request flow looks like this.

```text
Client

    │

Request

    ▼

Load Balancer

    │

Choose Healthy Server

    │

    ▼

Service Instance
```

The client communicates with the load balancer instead of a specific server.

---

# Load Balancer Responsibilities

A load balancer is responsible for:

- Receiving client requests
- Selecting a healthy instance
- Distributing traffic
- Detecting failed servers
- Routing around unhealthy instances
- Supporting horizontal scaling

It acts as the traffic controller for the application.

---

# Load Balancing Strategies

Different algorithms determine how requests are distributed.

Common strategies include:

- Round Robin
- Least Connections
- Random
- Weighted Round Robin
- Consistent Hashing

Each strategy is suitable for different workloads.

---

# Round Robin

Round Robin sends each new request to the next available server.

Example:

```text
Request 1 → Server A

Request 2 → Server B

Request 3 → Server C

Request 4 → Server A

Request 5 → Server B
```

Advantages:

- Simple
- Fair distribution
- Easy to implement

It works well when servers have similar capacity.

---

# Least Connections

This strategy selects the server with the fewest active connections.

Example:

```text
Server A

15 Connections

Server B

4 Connections

Server C

8 Connections
```

The next request goes to:

```text
Server B
```

This approach works well when request durations vary significantly.

---

# Weighted Round Robin

Sometimes servers have different hardware specifications.

Example:

```text
Server A

Weight: 3

Server B

Weight: 2

Server C

Weight: 1
```

Traffic distribution becomes:

```text
A

A

A

B

B

C
```

More powerful servers receive more requests.

---

# Random Selection

The load balancer randomly selects a server.

```text
Client

↓

Random Choice

↓

Server
```

Although simple, this approach usually provides a reasonably even distribution over time.

---

# Consistent Hashing

Some applications need related requests to reach the same server.

Example:

```text
User ID

↓

Hash Function

↓

Server
```

This approach is useful for:

- Session affinity
- Caching
- Stateful applications

---

# Client-Side Load Balancing

In client-side load balancing, the client receives all available service instances and selects one.

Workflow:

```text
Client

↓

Service Discovery

↓

Instance List

↓

Select Server

↓

RPC
```

The client is responsible for choosing the destination.

---

# Server-Side Load Balancing

In server-side load balancing, the client sends requests to a proxy or gateway.

Workflow:

```text
Client

↓

Load Balancer

↓

Server A

Server B

Server C
```

The client does not know which server ultimately handles the request.

---

# Client-Side vs Server-Side

| Feature | Client-Side | Server-Side |
|---------|-------------|-------------|
| Server selection | Client | Load Balancer |
| Client complexity | Higher | Lower |
| Extra proxy required | No | Yes |
| Common with Kubernetes | Sometimes | Very Common |

Both approaches are widely used in production systems.

---

# Load Balancing in gRPC

gRPC supports both client-side and server-side load balancing.

Common deployment models include:

```text
Client

↓

Envoy

↓

gRPC Services
```

or

```text
Client

↓

Kubernetes Service

↓

Pods
```

The exact implementation depends on the infrastructure platform.

---

# Load Balancing with Kubernetes

In Kubernetes, traffic usually flows through a Service.

```text
Client

↓

Kubernetes Service

↓

Pod A

Pod B

Pod C
```

As Pods are added or removed, Kubernetes automatically updates the available endpoints.

---

# Relationship with Service Discovery

Load balancing depends on Service Discovery.

```text
Service Registry

↓

Healthy Instances

↓

Load Balancer

↓

Selected Server
```

Without Service Discovery, the load balancer would not know which servers are available.

---

# Relationship with Health Checks

Health checks ensure that traffic is only routed to healthy servers.

```text
Server A

Healthy

✔

Server B

Healthy

✔

Server C

Failed

✘
```

The failed instance is removed from the routing pool.

---

# Handling Server Failures

Suppose Server B crashes.

```text
Server B

↓

Failure

↓

Health Check Fails

↓

Removed

↓

Traffic Sent to

A and C
```

Clients continue to receive responses without interruption.

---

# Real-World Example

Consider an e-commerce application.

```text
Product Service

5 Instances

Order Service

8 Instances

Payment Service

3 Instances
```

During a holiday sale, the Order Service scales from 8 to 30 instances.

The load balancer automatically distributes requests across all 30 servers without requiring clients to change their configuration.

---

# Popular Load Balancers

Several technologies are commonly used with gRPC.

| Technology | Typical Use Case |
|------------|------------------|
| Envoy | Service mesh and gRPC proxy |
| NGINX | Reverse proxy and load balancer |
| HAProxy | High-performance TCP and HTTP load balancing |
| Kubernetes Service | Cluster-internal load balancing |
| AWS Application Load Balancer | Cloud-native HTTP/2 load balancing |
| Google Cloud Load Balancer | Managed global load balancing |

Each supports HTTP/2 and can route gRPC traffic.

---

# Best Practices

- Deploy multiple service instances.
- Combine load balancing with Service Discovery.
- Use health checks to remove unhealthy servers.
- Prefer stateless services whenever possible.
- Monitor request latency and server utilization.
- Scale horizontally as traffic increases.
- Select a load balancing strategy appropriate for your workload.

---

# Common Mistakes

Avoid the following mistakes:

- Running production services on a single instance.
- Sending traffic to unhealthy servers.
- Ignoring uneven server capacities.
- Hardcoding server addresses.
- Using sticky sessions unnecessarily.
- Neglecting to monitor load balancer performance.

---

# Key Takeaways

- Load balancing distributes requests across multiple service instances to improve scalability and availability.
- gRPC supports both client-side and server-side load balancing.
- Common load balancing algorithms include Round Robin, Least Connections, Weighted Round Robin, Random, and Consistent Hashing.
- Load balancing works closely with Service Discovery and Health Checks to ensure reliable request routing.
- Kubernetes, Envoy, NGINX, HAProxy, and cloud load balancers are commonly used to distribute gRPC traffic in production.
- Effective load balancing is essential for building resilient, scalable, and high-performance distributed systems.