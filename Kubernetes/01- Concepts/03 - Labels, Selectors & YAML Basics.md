# What are Labels?

Labels are **key-value pairs** attached to Kubernetes objects.

They help identify, organize, and group resources.

Think of labels as **tags** attached to an object.

Example

```yaml
metadata:
  labels:
    app: nginx
    environment: production
    tier: frontend
```

Here,

- `app` → nginx
- `environment` → production
- `tier` → frontend

---

# Why do we use Labels?

Labels help Kubernetes:

- Group resources
- Select Pods
- Connect Services to Pods
- Organize applications
- Filter resources

Example

```
Pod 1
app=nginx
env=prod

Pod 2
app=nginx
env=prod

Pod 3
app=mysql
env=prod
```

A Service can select only Pods where:

```
app=nginx
```

---

# Label Best Practices

Common labels

```yaml
labels:
  app: nginx
  version: v1
  environment: production
  tier: frontend
```

Frequently used keys

- app
- version
- environment
- tier
- component

---

# What are Selectors?

Selectors are used to **find Kubernetes objects based on Labels**.

Think of it like filtering rows in SQL.

```
Labels
↓

Selector

↓

Matching Pods
```

Example

Pods

```
Pod A
app=nginx

Pod B
app=nginx

Pod C
app=mysql
```

Selector

```yaml
selector:
  app: nginx
```

Result

```
Pod A
Pod B
```

---

# Types of Selectors

## Equality-based Selector

Matches exact values.

Example

```yaml
selector:
  matchLabels:
    app: nginx
```

Matches only

```
app=nginx
```

---

## Set-based Selector

Matches multiple values.

Example

```
environment in (dev, qa)
```

or

```
environment notin (production)
```

Useful for advanced filtering.

---

# Labels vs Selectors

| Labels | Selectors |
|---------|-----------|
| Added to objects | Used to search objects |
| Key-value pairs | Query over labels |
| Identify resources | Select resources |

Think of it like:

```
Labels = Name Tag

Selectors = Search Filter
```

---

# Configuration File (YAML)

In Kubernetes, resources are created using **YAML configuration files**.

A YAML file describes the desired state of an object.

Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx
```

---

# Why YAML?

Instead of running many commands,

```bash
kubectl run ...
kubectl expose ...
kubectl scale ...
```

we simply write one configuration file.

Benefits

- Version Control
- Easy Updates
- Reusable
- Infrastructure as Code
- Declarative Management

---

# Structure of a Kubernetes YAML File

Almost every Kubernetes object follows this structure.

```yaml
apiVersion:
kind:
metadata:
spec:
status:
```

---

# 1. apiVersion

Specifies which Kubernetes API version should be used.

Examples

```yaml
apiVersion: v1
```

```yaml
apiVersion: apps/v1
```

Common API versions

| Resource | API Version |
|----------|-------------|
| Pod | v1 |
| Service | v1 |
| ConfigMap | v1 |
| Deployment | apps/v1 |
| ReplicaSet | apps/v1 |

---

# 2. kind

Defines the type of Kubernetes object.

Examples

```yaml
kind: Pod
```

```yaml
kind: Deployment
```

```yaml
kind: Service
```

Examples of kinds

- Pod
- Deployment
- ReplicaSet
- Service
- ConfigMap
- Secret
- StatefulSet
- Job
- CronJob

---

# 3. metadata

Stores information about the object.

Example

```yaml
metadata:
  name: nginx
  namespace: production
  labels:
    app: nginx
```

Metadata commonly includes

- name
- namespace
- labels
- annotations

---

# 4. spec

The **Specification** section describes the desired state.

This is the most important part of every Kubernetes resource.

Example

```yaml
spec:
  containers:
  - name: nginx
    image: nginx
```

Examples of what goes inside spec

- Image
- Containers
- Ports
- Replicas
- Resources
- Volumes
- Environment Variables

---

# 5. status

The Status section is generated automatically by Kubernetes.

Users generally do not edit it.

Example

```yaml
status:
  phase: Running
```

Status includes

- Running
- Pending
- Failed
- Succeeded
- CrashLoopBackOff

---

# Blueprint of a Pod

A Pod YAML acts as a **blueprint** for creating Pods.

It defines:

- Pod Name
- Image
- Labels
- Ports
- Volumes
- Environment Variables

Example

```yaml
apiVersion: v1
kind: Pod

metadata:
  name: nginx-pod
  labels:
    app: nginx

spec:
  containers:
    - name: nginx
      image: nginx
      ports:
      - containerPort: 80
```

Kubernetes reads this blueprint and creates the Pod.

---

# YAML Workflow

```
Developer

↓

Writes YAML

↓

kubectl apply

↓

API Server

↓

Scheduler

↓

Worker Node

↓

Pod Created
```

---

# Imperative vs Declarative

## Imperative

You tell Kubernetes **how** to do something.

Example

```bash
kubectl run nginx --image=nginx
```

---

## Declarative

You describe **what** you want.

Example

```bash
kubectl apply -f pod.yaml
```

Production environments almost always use the declarative approach.

---

# Interview Questions

## What are Labels?

Labels are key-value pairs attached to Kubernetes objects for identification and organization.

---

## What are Selectors?

Selectors are used to find and group Kubernetes objects based on Labels.

---

## Why are Labels important?

Labels allow Services, ReplicaSets, and Deployments to identify and manage the correct Pods.

---

## What is YAML?

YAML is a human-readable configuration language used to define Kubernetes resources.

---

## What are the main sections of a Kubernetes YAML file?

- apiVersion
- kind
- metadata
- spec
- status

---

## Which section contains the desired state?

The `spec` section contains the desired configuration of the resource.

---

## Which section is automatically maintained by Kubernetes?

The `status` section is automatically updated by Kubernetes to reflect the current state.

---

# Key Takeaways

- Labels are key-value pairs used to identify resources.
- Selectors filter resources using Labels.
- Services and Deployments rely on Labels and Selectors.
- Kubernetes resources are defined using YAML files.
- Every YAML file generally contains:
  - apiVersion
  - kind
  - metadata
  - spec
  - status
- The `spec` defines the desired state.
- The `status` reflects the current state.
- YAML files act as blueprints for Kubernetes resources.
- Declarative configuration (`kubectl apply -f`) is the recommended approach for production.