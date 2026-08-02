# What is Kubernetes?

Kubernetes (also called **K8s**) is an open-source **container orchestration platform** developed by Google.

It automates the deployment, scaling, networking, and management of containerized applications.

Instead of manually managing hundreds of Docker containers, Kubernetes manages them automatically.

---

# Why Kubernetes?

Running a few Docker containers is easy.

Running hundreds or thousands of containers across multiple servers is difficult.

Kubernetes solves problems like:

- Automatic deployment
- High availability
- Self-healing
- Load balancing
- Auto scaling
- Rolling updates
- Resource management

---

# Basic Kubernetes Architecture

```
                Kubernetes Cluster
        +--------------------------------+
        |                                |
        |   Control Plane                |
        |        │                       |
        |        │                       |
        |   Schedules Workloads          |
        |        │                       |
        | ┌───────────────┐              |
        | │ Worker Node 1 │              |
        | └───────────────┘              |
        |        │                       |
        |      Pods                      |
        |                                |
        | ┌───────────────┐              |
        | │ Worker Node 2 │              |
        | └───────────────┘              |
        |        │                       |
        |      Pods                      |
        +--------------------------------+
```

---

# Kubernetes Terminology

## Kubernetes

Kubernetes is a **container orchestration system**.

Its primary job is to manage containerized applications.

Responsibilities include:

- Deploying applications
- Scaling applications
- Restarting failed containers
- Service discovery
- Load balancing
- Rolling updates

---

## kubectl

`kubectl` is the command-line interface (CLI) used to communicate with a Kubernetes cluster.

Think of it as the remote control for Kubernetes.

Example:

```bash
kubectl get pods
kubectl get nodes
kubectl apply -f deployment.yaml
```

Common Interview Question

**Q:** What is kubectl?

**Answer:**

> kubectl is the command-line tool used to interact with the Kubernetes API Server and manage Kubernetes resources.

---

## Cluster

A Kubernetes Cluster is a group of machines working together.

A cluster contains:

- Control Plane
- One or more Worker Nodes

```
Cluster
│
├── Control Plane
│
├── Worker Node
│
└── Worker Node
```

---

## Node

A Node is a physical or virtual machine inside the Kubernetes cluster.

It is where your applications actually run.

Every node contains:

- kubelet
- Container Runtime
- kube-proxy

Example:

```
Node
│
├── Pod
├── Pod
├── Pod
```

---

## kubelet

kubelet is the Kubernetes agent running on every worker node.

Its job is to ensure that the containers described in Kubernetes are actually running.

Responsibilities:

- Talks to Control Plane
- Starts Pods
- Stops Pods
- Reports Node status
- Monitors Pod health

Think of kubelet as the **manager of a worker node**.

---

## Control Plane

The Control Plane is the brain of Kubernetes.

It manages the entire cluster.

Responsibilities include:

- Scheduling Pods
- Monitoring Nodes
- Maintaining desired state
- Managing API requests

Main components:

- API Server
- Scheduler
- Controller Manager
- etcd

---

# What is a Pod?

A Pod is the **smallest deployable unit in Kubernetes**.

A Pod is a wrapper around one or more containers.

Usually,

**1 Pod = 1 Container**

although multiple tightly coupled containers can exist in a single Pod.

Example:

```
Pod
│
└── Docker Container
```

---

# Characteristics of a Pod

- Smallest Kubernetes object
- Contains one or more containers
- Shares storage
- Shares networking
- Has its own IP Address
- Runs on one Node

---

# Pod Networking

Every Pod gets its own IP address.

```
Node

├── Pod A
│     IP: 10.244.1.5
│
├── Pod B
│     IP: 10.244.1.6
│
└── Pod C
      IP: 10.244.1.7
```

Pods communicate with each other using their IP addresses.

---

# Kubernetes Flow

```
Developer
     │
     ▼
kubectl
     │
     ▼
API Server
     │
     ▼
Control Plane
     │
     ▼
Worker Node
     │
     ▼
Pod
     │
     ▼
Container
```

---

# Kubernetes vs Docker

| Docker | Kubernetes |
|----------|------------|
| Creates containers | Manages containers |
| Single machine | Multiple machines |
| Manual scaling | Automatic scaling |
| No self-healing | Self-healing |
| Basic networking | Advanced networking |

Think of it like this:

Docker builds the containers.

Kubernetes manages the containers.

---

# Interview Questions

## What is Kubernetes?

Kubernetes is an open-source container orchestration platform used to deploy, manage, scale, and monitor containerized applications.

---

## What is kubectl?

kubectl is the command-line tool used to interact with a Kubernetes cluster.

---

## What is a Node?

A Node is a machine in a Kubernetes cluster where Pods run.

---

## What is kubelet?

kubelet is the Kubernetes agent running on every worker node that ensures Pods are running correctly.

---

## What is the Control Plane?

The Control Plane is the management layer of Kubernetes that controls scheduling, monitoring, and maintaining the cluster state.

---

## What is a Pod?

A Pod is the smallest deployable unit in Kubernetes that contains one or more containers.

---

## Why does every Pod have its own IP?

Each Pod gets its own IP so that Pods can communicate directly without Network Address Translation (NAT).

---

# Key Takeaways

- Kubernetes is a container orchestration platform.
- kubectl is the CLI used to manage Kubernetes.
- A Cluster contains Control Plane and Worker Nodes.
- A Node is a machine that runs Pods.
- kubelet is the Kubernetes agent on every Node.
- The Control Plane manages the cluster.
- A Pod is the smallest deployable unit.
- Usually, one Pod runs one application container.
- Every Pod gets its own IP address.

---
