# What is a Deployment?

A **Deployment** is a Kubernetes workload resource used to deploy, manage, and update stateless applications.

It is the **most commonly used Kubernetes object** in production.

A Deployment manages one or more **ReplicaSets**, which in turn manage **Pods**.

Think of a Deployment as the **manager** of your application's lifecycle.

---

# Why Do We Need Deployments?

Creating Pods directly has several limitations.

- No self-healing
- No automatic scaling
- No rolling updates
- No rollback support

Creating ReplicaSets solves self-healing but still lacks deployment management.

Deployment provides:

- Self-healing
- Scaling
- Rolling Updates
- Rollbacks
- Version History
- Zero Downtime Deployment

---

# Deployment Architecture

```
                 Deployment
                      │
               ReplicaSet
                      │
       ┌──────────────┼──────────────┐
       │              │              │
     Pod 1         Pod 2         Pod 3
```

---

# Deployment Workflow

```
Developer

↓

Deployment

↓

ReplicaSet

↓

Pods

↓

Application Running
```

---

# Deployment Controller

The Deployment Controller continuously monitors the Deployment.

Responsibilities

- Create ReplicaSets
- Scale Pods
- Perform Rolling Updates
- Rollback Failed Deployments
- Maintain Desired State

---

# Deployment Lifecycle

```
Create Deployment

↓

Create ReplicaSet

↓

Create Pods

↓

Application Running

↓

Update Deployment

↓

New ReplicaSet

↓

New Pods

↓

Old Pods Removed
```

---

# Deployment YAML

```yaml
apiVersion: apps/v1

kind: Deployment

metadata:
  name: nginx-deployment

spec:
  replicas: 3

  selector:
    matchLabels:
      app: nginx

  template:

    metadata:
      labels:
        app: nginx

    spec:

      containers:
      - name: nginx

        image: nginx:latest

        ports:
        - containerPort: 80
```

Create Deployment

```bash
kubectl apply -f deployment.yaml
```

---

# Deployment Components

```
Deployment

│

├── Metadata

├── Selector

├── Replica Count

└── Pod Template
```

---

# Replica Count

Specifies how many Pod replicas should run.

Example

```yaml
replicas: 5
```

Deployment automatically ensures five Pods remain available.

---

# Scaling Deployments

Scaling Up

```bash
kubectl scale deployment nginx-deployment --replicas=5
```

```
Deployment

↓

ReplicaSet

↓

Pod

Pod

Pod

Pod

Pod
```

---

Scaling Down

```bash
kubectl scale deployment nginx-deployment --replicas=2
```

Deployment removes extra Pods gracefully.

---

# Rolling Updates

Rolling Update is the default deployment strategy.

Pods are updated gradually.

Example

Old Version

```
v1

↓

Pod

Pod

Pod
```

Update Image

```
v2
```

Deployment performs

```
New Pod

↓

Old Pod Removed

↓

New Pod

↓

Old Pod Removed
```

Users experience little or no downtime.

---

# Rolling Update Architecture

```
Deployment

↓

ReplicaSet (v1)

↓

Pods

↓

Deployment Updated

↓

ReplicaSet (v2)

↓

New Pods Created

↓

Old Pods Removed
```

---

# Rollback

If an update fails,

Deployment can restore the previous version.

Rollback command

```bash
kubectl rollout undo deployment nginx-deployment
```

Deployment restores the previous ReplicaSet automatically.

---

# Rollout Status

Check deployment progress.

```bash
kubectl rollout status deployment nginx-deployment
```

Example

```
Waiting...

↓

Deployment Complete
```

---

# Rollout History

View previous revisions.

```bash
kubectl rollout history deployment nginx-deployment
```

Example

```
Revision 1

Revision 2

Revision 3
```

---

# Updating an Application

Update image

```bash
kubectl set image deployment/nginx-deployment nginx=nginx:1.27
```

Deployment creates

```
New ReplicaSet

↓

New Pods

↓

Old Pods Removed
```

---

# Deployment Strategies

Kubernetes supports different deployment strategies.

```
Deployment

├── Rolling Update
├── Recreate
├── Blue-Green
└── Canary
```

---

# 1. Rolling Update

Default strategy.

```
Old Pod

↓

New Pod

↓

Old Pod Removed
```

Advantages

- No downtime
- Safe updates

---

# 2. Recreate

Old Pods are deleted first.

```
Delete Old Pods

↓

Create New Pods
```

Advantages

- Simple

Disadvantages

- Downtime occurs

Used for

- Development
- Testing
- Applications that cannot run multiple versions simultaneously

---

# 3. Blue-Green Deployment

Maintain two environments.

```
Blue

↓

Production
```

Deploy new version.

```
Green
```

Switch traffic when ready.

```
Blue

↓

Green
```

Advantages

- Instant rollback
- Minimal downtime

---

# 4. Canary Deployment

Deploy the new version to a small percentage of users.

```
90%

↓

Version 1

10%

↓

Version 2
```

Gradually increase traffic if successful.

Benefits

- Lower deployment risk
- Easy monitoring

---

# Deployment vs ReplicaSet

| Deployment | ReplicaSet |
|------------|------------|
| Manages ReplicaSets | Manages Pods |
| Rolling Updates | No Rolling Updates |
| Rollbacks | No Rollbacks |
| Version History | No Version History |
| Production Ready | Lower-level controller |

---

# Deployment vs StatefulSet

| Deployment | StatefulSet |
|------------|-------------|
| Stateless Applications | Stateful Applications |
| Random Pod Names | Stable Pod Names |
| No Stable Storage | Persistent Storage |
| REST APIs | Databases |

---

# Deployment Architecture During Update

```
                Deployment

                      │

          ┌───────────┴───────────┐

     ReplicaSet v1         ReplicaSet v2

          │                     │

      Old Pods             New Pods

          │

     Removed Gradually
```

---

# Real-World Example

Deploy a Django REST API.

```
Deployment

↓

ReplicaSet

↓

API Pod 1

API Pod 2

API Pod 3

↓

ClusterIP Service

↓

Ingress

↓

Internet
```

Update

```
Django 5.2

↓

Django 5.3

↓

Rolling Update

↓

Zero Downtime
```

---

# Useful Commands

Create Deployment

```bash
kubectl apply -f deployment.yaml
```

View Deployments

```bash
kubectl get deployments
```

Short form

```bash
kubectl get deploy
```

Describe Deployment

```bash
kubectl describe deployment nginx-deployment
```

Delete Deployment

```bash
kubectl delete deployment nginx-deployment
```

Scale Deployment

```bash
kubectl scale deployment nginx-deployment --replicas=5
```

View Rollout Status

```bash
kubectl rollout status deployment nginx-deployment
```

View Rollout History

```bash
kubectl rollout history deployment nginx-deployment
```

Rollback Deployment

```bash
kubectl rollout undo deployment nginx-deployment
```

Restart Deployment

```bash
kubectl rollout restart deployment nginx-deployment
```

Update Image

```bash
kubectl set image deployment/nginx-deployment nginx=nginx:latest
```

---

# Best Practices

✔ Always use Deployments instead of creating Pods directly.

✔ Use Rolling Updates for production.

✔ Define resource requests and limits.

✔ Configure Liveness and Readiness Probes.

✔ Keep multiple replicas for high availability.

✔ Use Labels consistently.

✔ Store configuration in ConfigMaps and Secrets.

---

# Common Problems

## Pods Not Updating

Possible causes

- Incorrect image name
- Failed image pull
- Readiness probe failure

---

## Deployment Stuck

Possible reasons

- Insufficient resources
- Scheduling issues
- Failing health checks

---

## Rollout Failed

Common causes

- Application crashes
- Invalid configuration
- Missing environment variables

Rollback to the previous version.

```bash
kubectl rollout undo deployment nginx-deployment
```

---

# Interview Questions

## What is a Deployment?

A Deployment is a Kubernetes resource that manages ReplicaSets and Pods while providing rolling updates, scaling, rollbacks, and version management.

---

## Why should Deployments be used instead of Pods?

Deployments provide self-healing, scaling, rolling updates, rollbacks, and version history, making them suitable for production workloads.

---

## What is a Rolling Update?

A Rolling Update gradually replaces old Pods with new Pods, allowing application updates with minimal or zero downtime.

---

## What is the difference between a Deployment and a ReplicaSet?

A ReplicaSet only maintains the desired number of Pods.

A Deployment manages ReplicaSets and provides advanced deployment capabilities such as rolling updates and rollbacks.

---

## What is a Rollback?

A Rollback restores a Deployment to a previously working revision if an update fails.

---

## What deployment strategy is used by default?

Rolling Update.

---

## When should StatefulSets be used instead of Deployments?

StatefulSets should be used for stateful applications such as databases, where stable identities and persistent storage are required.

---

# Key Takeaways

- Deployment is the recommended way to deploy stateless applications.
- Deployments manage ReplicaSets, and ReplicaSets manage Pods.
- Deployments provide self-healing, scaling, rolling updates, rollbacks, and revision history.
- Rolling Update is the default deployment strategy and enables zero-downtime updates.
- Other deployment strategies include Recreate, Blue-Green, and Canary.
- Deployments are ideal for web applications, REST APIs, and microservices.
- Stateful applications such as databases should use StatefulSets instead of Deployments.