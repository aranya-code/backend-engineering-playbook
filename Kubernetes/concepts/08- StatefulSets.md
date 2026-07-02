# What is a StatefulSet?

A **StatefulSet** is a Kubernetes workload resource used to manage **stateful applications**.

Unlike Deployments, StatefulSets provide:

- Stable Pod names
- Stable network identity
- Persistent storage
- Ordered deployment
- Ordered scaling
- Ordered termination

StatefulSets are mainly used for databases and distributed systems.

---

# Stateless vs Stateful Applications

## Stateless Application

A stateless application does not store data inside the application instance.

Examples

- Nginx
- React Frontend
- Django REST API
- FastAPI
- Spring Boot APIs

These applications can be replaced at any time without affecting users.

```
Client

↓

Pod A

↓

Pod Deleted

↓

Pod B

Application still works
```

Deploy using **Deployment**.

---

## Stateful Application

A stateful application stores important data.

Examples

- MySQL
- PostgreSQL
- MongoDB
- Cassandra
- Redis
- Kafka
- Elasticsearch

If the Pod changes, the data must still remain available.

Deploy using **StatefulSet**.

---

# Deployment vs StatefulSet

| Deployment | StatefulSet |
|------------|-------------|
| Stateless applications | Stateful applications |
| Random Pod names | Predictable Pod names |
| Pods are interchangeable | Pods have unique identities |
| No stable storage by default | Persistent storage |
| No ordered deployment | Ordered deployment |
| No ordered deletion | Ordered deletion |

---

# Why Not Use Deployment for Databases?

Suppose MySQL is deployed using a Deployment.

```
mysql-6fd8f76d4-jlm2x
```

Pod crashes.

```
↓

New Pod Created

↓

mysql-7a98cfd89-kd82m
```

Problems

- New Pod name
- Different network identity
- Possible storage issues
- Database replication becomes difficult

---

# StatefulSet Solution

StatefulSet guarantees predictable identities.

```
mysql-0

mysql-1

mysql-2
```

If `mysql-1` crashes,

```
Old Pod

mysql-1

↓

Restart

↓

New Pod

mysql-1
```

The Pod keeps the same identity.

---

# Pod Identity

Every StatefulSet Pod has

- Stable name
- Stable hostname
- Stable DNS
- Stable storage

Example

```
mysql-0

mysql-1

mysql-2
```

Names never change.

---

# Stable DNS

Each Pod gets its own DNS entry.

Example

```
mysql-0.mysql.default.svc.cluster.local

mysql-1.mysql.default.svc.cluster.local

mysql-2.mysql.default.svc.cluster.local
```

Applications can reliably communicate with specific Pods.

---

# Persistent Storage

Each StatefulSet Pod gets its own Persistent Volume.

```
mysql-0

↓

PVC

↓

PV

↓

Disk
```

```
mysql-1

↓

PVC

↓

PV

↓

Disk
```

If a Pod is recreated, it reconnects to the same storage.

---

# Ordered Deployment

Pods are created one at a time.

```
mysql-0

↓

mysql-1

↓

mysql-2
```

The next Pod starts only after the previous one becomes healthy.

---

# Ordered Scaling

Scaling follows a predictable order.

Scaling Up

```
mysql-0

↓

mysql-1

↓

mysql-2

↓

mysql-3
```

Scaling Down

```
mysql-3

↓

mysql-2

↓

mysql-1

↓

mysql-0
```

---

# Ordered Termination

Pods are terminated in reverse order.

```
mysql-2

↓

mysql-1

↓

mysql-0
```

This prevents data corruption.

---

# StatefulSet Architecture

```
Application

↓

StatefulSet

↓

mysql-0

↓

PVC

↓

PV

↓

Disk

------------------------

mysql-1

↓

PVC

↓

PV

↓

Disk

------------------------

mysql-2

↓

PVC

↓

PV

↓

Disk
```

---

# StatefulSet YAML

```yaml
apiVersion: apps/v1
kind: StatefulSet

metadata:
  name: mysql

spec:
  serviceName: mysql

  replicas: 3

  selector:
    matchLabels:
      app: mysql

  template:

    metadata:
      labels:
        app: mysql

    spec:

      containers:

      - name: mysql

        image: mysql:8
```

---

# Headless Service

StatefulSets require a **Headless Service**.

Unlike a normal Service, it does not provide load balancing.

Instead, it provides stable DNS names for each Pod.

```
Headless Service

↓

mysql-0

mysql-1

mysql-2
```

---

# Real-World Example

Imagine a PostgreSQL cluster.

```
postgres-0

Master Database

↓

Persistent Disk

----------------------

postgres-1

Replica

↓

Persistent Disk

----------------------

postgres-2

Replica

↓

Persistent Disk
```

Each database instance keeps

- Same hostname
- Same storage
- Same DNS

even after restarting.

---

# Deployment vs StatefulSet Architecture

Deployment

```
Deployment

↓

ReplicaSet

↓

Random Pods

↓

nginx-h7d2k

↓

nginx-j72ks

↓

nginx-p8d1a
```

---

StatefulSet

```
StatefulSet

↓

mysql-0

↓

mysql-1

↓

mysql-2
```

---

# Advantages

- Stable Pod identity
- Stable storage
- Stable DNS
- Ordered deployment
- Ordered scaling
- Ordered termination
- Ideal for databases

---

# Limitations

- Slower deployment
- More complex than Deployments
- Not suitable for stateless applications

---

# Common Use Cases

Use StatefulSets for

- MySQL
- PostgreSQL
- MongoDB
- Cassandra
- Kafka
- Elasticsearch
- ZooKeeper
- RabbitMQ clusters

Do **not** use StatefulSets for

- REST APIs
- Web Servers
- Frontend applications
- Stateless microservices

---

# Useful Commands

Create StatefulSet

```bash
kubectl apply -f statefulset.yaml
```

View StatefulSets

```bash
kubectl get statefulsets
```

Short form

```bash
kubectl get sts
```

Describe StatefulSet

```bash
kubectl describe statefulset mysql
```

Delete StatefulSet

```bash
kubectl delete statefulset mysql
```

---

# Interview Questions

## What is a StatefulSet?

A StatefulSet is a Kubernetes workload resource used to manage stateful applications by providing stable identities, persistent storage, and ordered deployment.

---

## Difference between Deployment and StatefulSet?

Deployments manage stateless applications with interchangeable Pods.

StatefulSets manage stateful applications where each Pod has a unique identity and persistent storage.

---

## Why do StatefulSets require Persistent Volumes?

Stateful applications must preserve their data even if Pods restart or move to another node.

---

## Why do StatefulSets use a Headless Service?

A Headless Service provides stable DNS names for each Pod instead of load balancing requests.

---

## When should you use a StatefulSet?

Use StatefulSets for databases, messaging systems, and distributed applications that require stable identities and persistent storage.

---

# Key Takeaways

- StatefulSets are designed for **stateful workloads**.
- Each Pod has a **predictable name**, **stable DNS**, and **dedicated Persistent Volume**.
- StatefulSets perform **ordered deployment**, **ordered scaling**, and **ordered termination**.
- They are ideal for databases and distributed systems such as MySQL, PostgreSQL, MongoDB, Kafka, and Cassandra.
- Deployments should be used for stateless applications, while StatefulSets should be used when application state and identity must be preserved.