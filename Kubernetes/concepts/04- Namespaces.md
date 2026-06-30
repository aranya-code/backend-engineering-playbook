# What is a Namespace?

A Namespace is a logical partition inside a Kubernetes cluster.

It allows multiple users, teams, or applications to share the same Kubernetes cluster while keeping their resources isolated.

Think of a Namespace as a **virtual cluster inside a physical Kubernetes cluster**.

```
Kubernetes Cluster
│
├── default
├── kube-system
├── kube-public
├── dev
├── testing
└── production
```

---

# Why do we need Namespaces?

Without Namespaces

- All resources exist together.
- Resource names must be unique.
- Difficult to organize applications.

With Namespaces

- Better organization
- Resource isolation
- Team separation
- Environment separation
- Security boundaries
- Resource quotas

Example

```
Cluster

├── Development Namespace
│      ├── Frontend
│      ├── Backend
│      └── Database
│
├── Testing Namespace
│      ├── Frontend
│      ├── Backend
│      └── Database
│
└── Production Namespace
       ├── Frontend
       ├── Backend
       └── Database
```

---

# Default Namespaces

Every Kubernetes cluster comes with several built-in namespaces.

## 1. default

If you don't specify a namespace, Kubernetes creates resources here.

Example

```bash
kubectl get pods
```

This command retrieves Pods from the `default` namespace.

---

## 2. kube-system

Contains Kubernetes system components.

Examples

- API Server
- Scheduler
- Controller Manager
- CoreDNS
- kube-proxy
- etcd

**Do not modify resources in this namespace unless you know what you're doing.**

Example

```bash
kubectl get pods -n kube-system
```

---

## 3. kube-public

Contains publicly readable resources.

Typically stores information that any authenticated user can access.

Example

- Cluster information
- Public ConfigMaps

---

## 4. kube-node-lease

Stores Lease objects for each Node.

Each Node periodically renews its lease to indicate that it is healthy.

This acts as a **heartbeat mechanism**.

```
Worker Node

↓

Updates Lease

↓

Control Plane knows
Node is Alive
```

Benefits

- Faster node health detection
- Lower API Server load
- Efficient heartbeat management

---

# Creating a Namespace

```bash
kubectl create namespace development
```

Verify

```bash
kubectl get namespaces
```

or

```bash
kubectl get ns
```

---

# Creating Resources in a Namespace

Example

```bash
kubectl create deployment nginx \
--image=nginx \
-n development
```

---

# Switching Namespace

Set the default namespace for the current context.

```bash
kubectl config set-context --current --namespace=development
```

Check current namespace

```bash
kubectl config view --minify
```

---

# Deleting a Namespace

```bash
kubectl delete namespace development
```

Deleting a namespace deletes all resources inside it.

---

# Common Use Cases

## Environment Isolation

```
dev
testing
staging
production
```

---

## Team Isolation

```
Frontend Team

Backend Team

DevOps Team

QA Team
```

---

## Multi-Tenant Clusters

One Kubernetes cluster can host applications for multiple customers or business units.

Each tenant receives its own Namespace.

---

## Resource Management

Namespaces work with

- Resource Quotas
- Limit Ranges
- RBAC

to control resource usage and permissions.

---

# Namespace Best Practices

✔ Use separate namespaces for different environments.

✔ Do not deploy applications into `kube-system`.

✔ Use meaningful namespace names.

Examples

```
production

staging

development

monitoring

logging
```

✔ Apply RBAC at the namespace level whenever possible.

---

# Namespace vs Cluster

| Namespace | Cluster |
|------------|----------|
| Logical isolation | Physical/virtual infrastructure |
| Shares cluster resources | Contains all resources |
| Lightweight | Heavyweight |
| Easy to create | Expensive to create |

---

# Architecture

```
Kubernetes Cluster
│
├── default
│     ├── Pods
│     ├── Services
│     └── Deployments
│
├── development
│     ├── Pods
│     ├── Services
│     └── Deployments
│
├── testing
│     ├── Pods
│     ├── Services
│     └── Deployments
│
└── production
      ├── Pods
      ├── Services
      └── Deployments
```

---

# Useful Commands

List namespaces

```bash
kubectl get namespaces
```

Short form

```bash
kubectl get ns
```

Get Pods in a namespace

```bash
kubectl get pods -n kube-system
```

Create namespace

```bash
kubectl create namespace dev
```

Delete namespace

```bash
kubectl delete namespace dev
```

Describe namespace

```bash
kubectl describe namespace dev
```

---

# Interview Questions

## What is a Namespace?

A Namespace is a logical partition within a Kubernetes cluster that isolates resources and organizes workloads.

---

## Why are Namespaces used?

Namespaces are used for:

- Resource isolation
- Team separation
- Environment management
- Security
- Resource quotas

---

## What are the default namespaces?

- default
- kube-system
- kube-public
- kube-node-lease

---

## What is kube-system?

It contains Kubernetes system components such as the API Server, Scheduler, Controller Manager, CoreDNS, and etcd.

---

## What is kube-public?

A namespace intended for publicly readable cluster information.

---

## What is kube-node-lease?

It stores Lease objects used by Nodes to send heartbeats to the Control Plane.

---

# Key Takeaways

- A Namespace is a virtual cluster inside a Kubernetes cluster.
- It organizes and isolates Kubernetes resources.
- Built-in namespaces include:
  - default
  - kube-system
  - kube-public
  - kube-node-lease
- Namespaces are commonly used for development, testing, staging, and production environments.
- They improve organization, security, and resource management.