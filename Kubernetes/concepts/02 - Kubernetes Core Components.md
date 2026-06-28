# Kubernetes Layers of Abstraction

Kubernetes uses multiple layers of abstraction to simplify container management.

```

Deployment
↓
ReplicaSet
↓
Pod
↓
Container

```

Think of it like a company hierarchy.

```

CEO → Manager → Employee → Work

Deployment → ReplicaSet → Pod → Container

```

---

# Container

A **Container** is the smallest executable unit.

It contains:

- Application Code
- Runtime
- Libraries
- Dependencies

Example

```

Python Application
+
Python Runtime
+
Required Packages

```

Containers are created using Docker or any OCI-compatible runtime.

---

# Pod

A Pod is the smallest deployable object in Kubernetes.

A Pod wraps one or more containers.

```

Pod
│
└── Container

```

Characteristics

- Smallest Kubernetes object
- Shares networking
- Shares storage
- Gets one IP Address
- Usually contains one application

Pods are **ephemeral**.

If a Pod dies, Kubernetes creates another one.

---

# ReplicaSet

A ReplicaSet ensures that a specified number of Pod replicas are always running.

Example

Desired Pods = 3

```

Pod 1 ✅
Pod 2 ❌
Pod 3 ✅

↓

ReplicaSet creates a new Pod

↓

Pod 4 ✅

```

Responsibilities

- Maintains desired number of Pods
- Recreates failed Pods
- Monitors Pod availability

Usually, developers don't create ReplicaSets directly.

Deployments manage ReplicaSets automatically.

---

# Deployment

A Deployment is the highest-level object for deploying stateless applications.

Think of it as a blueprint.

```

Deployment

↓

ReplicaSet

↓

Pods

↓

Containers

```

Deployment provides

- Rolling Updates
- Rollbacks
- Scaling
- Self Healing
- Replica Management

Example

```

Deployment

replicas: 3

↓

ReplicaSet

↓

Pod
Pod
Pod

```

---

# Why Deployment Instead of Pods?

If you create Pods directly

- No automatic recovery
- No rolling updates
- No scaling

If you create Deployments

- Automatic Pod recreation
- Scaling
- Rollbacks
- Updates

In production we almost always create **Deployments**, not Pods.

---

# Worker Node Components

Every Worker Node contains three important processes.

```

Worker Node

├── kubelet
├── kube-proxy
└── Container Runtime

```

---

# kubelet

kubelet is the Kubernetes agent.

Responsibilities

- Talks to Control Plane
- Starts Pods
- Stops Pods
- Reports Node Health
- Ensures desired state

Without kubelet, Pods cannot run.

---

# kube-proxy

kube-proxy handles networking.

Responsibilities

- Service Networking
- Load Balancing
- Packet Forwarding
- Network Rules

Think of kube-proxy as the network manager of the node.

---

# Container Runtime

The Container Runtime actually runs containers.

Examples

- containerd (default)
- CRI-O
- Docker Engine (older clusters)

Responsibilities

- Pull Images
- Start Containers
- Stop Containers
- Delete Containers

```

Container Runtime

↓

Docker Image

↓

Running Container

```

---

# Control Plane Components

The Control Plane is the brain of Kubernetes.

```

Control Plane

├── API Server
├── Scheduler
├── Controller Manager
└── etcd

```

---

# API Server

The API Server is the front door of Kubernetes.

Every request goes through it.

Example

```

kubectl get pods

↓

API Server

↓

Returns Pod Information

```

Responsibilities

- Authentication
- Authorization
- Resource Validation
- REST API

---

# Scheduler

The Scheduler decides where Pods should run.

It considers

- CPU
- Memory
- Node Availability
- Taints
- Affinity Rules

Example

```

Pod

↓

Scheduler

↓

Node 3 Selected

```

---

# Controller Manager

Controller Manager continuously watches the cluster.

If something changes, it fixes it.

Example

Desired Pods = 3

Running Pods = 2

↓

Controller Manager

↓

Creates one new Pod

Controllers include

- Deployment Controller
- ReplicaSet Controller
- Node Controller
- Job Controller

---

# etcd

etcd is Kubernetes' database.

It stores

- Cluster State
- Deployments
- Pods
- Secrets
- Configurations
- Nodes

Example

```

Cluster

↓

API Server

↓

etcd

```

Important

If etcd is lost, the cluster configuration is lost.

Always back up etcd.

---

# Service

Pods are temporary.

When Pods restart, their IP addresses change.

A Service provides a stable endpoint.

```

Without Service

Pod A
IP = 10.0.0.5

↓

Restart

↓

IP = 10.0.0.17

```

Clients lose connectivity.

Using Service

```

Client

↓

Service

↓

Pod 1
Pod 2
Pod 3

```

Advantages

- Permanent IP/DNS
- Load Balancing
- Service Discovery
- Decouples clients from Pods

---

# Ingress

Ingress exposes HTTP and HTTPS applications outside the cluster.

Without Ingress

```

Internet

↓

Service

```

With Ingress

```

Internet

↓

Ingress

↓

Service

↓

Pods

```

Benefits

- Single Entry Point
- SSL/TLS
- Path Routing
- Host Routing

---

# ConfigMap

ConfigMap stores non-sensitive configuration.

Examples

- Environment Variables
- URLs
- Feature Flags
- Port Numbers

Example

```

Database Host

API URL

Log Level

```

Never store passwords inside ConfigMaps.

---

# Secret

Secrets store sensitive information.

Examples

- Passwords
- API Keys
- Database Credentials
- Certificates
- Tokens

Secrets are Base64 encoded in Kubernetes.

Example

```

Database Password

JWT Secret

AWS Keys

```

---

# StatefulSet

StatefulSet manages stateful applications.

Examples

- MySQL
- PostgreSQL
- MongoDB
- Cassandra
- Kafka

Unlike Deployments

- Stable Network Identity
- Stable Storage
- Ordered Deployment
- Ordered Scaling

---

# Volume

Containers are temporary.

Their filesystem disappears when they restart.

Volumes provide persistent storage.

Without Volume

```

Container

↓

Restart

↓

Data Lost

```

With Volume

```

Container

↓

Volume

↓

Persistent Data

```

Examples

- Database Storage
- Uploaded Files
- Logs
- Shared Data

---

# Kubernetes Object Relationships

```

Deployment
│
├── ReplicaSet
│
├── ReplicaSet
│
└── ReplicaSet
      │
      ├── Pod
      │     └── Container
      │
      ├── Pod
      │     └── Container
      │
      └── Pod
            └── Container

```

---

# Complete Kubernetes Architecture

```

                User
                  │
              kubectl
                  │
             API Server
                  │
      ┌───────────┴───────────┐
      │                       │
 Scheduler          Controller Manager
      │                       │
      └───────────┬───────────┘
                  │
                etcd
                  │
      ┌───────────┴───────────┐
      │                       │
 Worker Node 1         Worker Node 2
      │                       │
 ┌───────────────┐     ┌───────────────┐
 │ kubelet       │     │ kubelet       │
 │ kube-proxy    │     │ kube-proxy    │
 │ containerd    │     │ containerd    │
 └───────┬───────┘     └───────┬───────┘
         │                     │
      Pods                  Pods

```

---

# Interview Questions

### What is the difference between Deployment and ReplicaSet?

Deployment manages ReplicaSets and provides rolling updates, rollbacks, and scaling. ReplicaSet only ensures the desired number of Pods are running.

---

### Why don't we create Pods directly?

Pods are temporary. Deployments automatically recreate failed Pods and support scaling and rolling updates.

---

### What is kube-proxy?

kube-proxy manages networking and load balancing between Services and Pods.

---

### What is etcd?

etcd is the distributed key-value database that stores the complete state of the Kubernetes cluster.

---

### What is the purpose of a Service?

A Service provides a stable network endpoint and load balances traffic to Pods.

---

### Difference between ConfigMap and Secret?

| ConfigMap | Secret |
|------------|---------|
| Non-sensitive configuration | Sensitive data |
| Plain text | Base64 encoded |
| Environment variables | Passwords, Tokens |

---

### When should StatefulSet be used?

Use StatefulSets for databases and other applications that require persistent storage and stable network identities.

---

# Key Takeaways

- **Deployment** manages application deployments.
- **ReplicaSet** maintains the desired number of Pods.
- **Pod** is the smallest deployable unit.
- **Container** runs the application.
- **kubelet** manages Pods on each node.
- **kube-proxy** handles networking and load balancing.
- **Container Runtime** runs containers.
- **API Server** is the entry point to the cluster.
- **Scheduler** selects the best node for Pods.
- **Controller Manager** keeps the cluster in its desired state.
- **etcd** stores the cluster's configuration and state.
- **Service** provides a stable network endpoint.
- **Ingress** exposes HTTP/HTTPS applications externally.
- **ConfigMap** stores non-sensitive configuration.
- **Secret** stores sensitive information securely.
- **StatefulSet** is used for stateful applications.
- **Volumes** provide persistent storage.