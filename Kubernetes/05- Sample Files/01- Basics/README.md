# Kubernetes Basics Examples

## Overview

The **Basics** folder introduces the fundamental Kubernetes resources that every Kubernetes engineer should understand before moving on to advanced topics such as networking, storage, scaling, and production deployments.

These examples provide hands-on manifests for creating and managing applications inside a Kubernetes cluster. Each YAML file is heavily commented to explain every important field, making them useful for both learning and future reference.

This section forms the foundation for the remainder of the Kubernetes Playbook.

---

# Why This Section Matters

Every Kubernetes application is built using these core resources.

Understanding how these resources interact is essential before learning advanced Kubernetes features.

After completing this section, you'll understand how Kubernetes:

- Runs containers
- Manages Pods
- Maintains desired state
- Exposes applications
- Organizes resources
- Connects workloads together

---

# Learning Path

Study the examples in the following order.

```text
Pod
 │
 ▼
Deployment
 │
 ▼
ReplicaSet
 │
 ▼
Service
 │
 ▼
Namespace
 │
 ▼
Labels & Selectors
 │
 ▼
Deployment + Service
```

---

# Navigation

- 📄 [01- Pod.yaml](01-%20Pod.yaml)
- 📄 [02- Deployment.yaml](02-%20Deployment.yaml)
- 📄 [03- ReplicaSet.yaml](03-%20ReplicaSet.yaml)
- 📄 [04- Service-ClusterIP.yaml](04-%20Service-ClusterIP.yaml)
- 📄 [05- Service-LoadBalancer.yaml](05-%20Service-LoadBalancer.yaml)
- 📄 [06- Namespace.yaml](06-%20Namespace.yaml)
- 📄 [07- Labels-Selectors.yaml](07-%20Labels-Selectors.yaml)
- 📄 [08- Deployment-Service.yaml](08-%20Deployment-Service.yaml)

---

# Kubernetes Architecture

```text
             User
               │
               ▼
           Kubernetes API
               │
               ▼
           Deployment
               │
               ▼
           ReplicaSet
               │
               ▼
              Pods
               │
               ▼
            Container
```

---

# Resource Relationships

```text
Namespace
     │
     ▼
Deployment
     │
     ▼
ReplicaSet
     │
     ▼
Pods
     │
     ▼
Service
```

---

# What You'll Learn

After completing this section, you'll be able to:

- Create Pods
- Deploy applications
- Scale applications
- Expose workloads using Services
- Organize resources with Namespaces
- Use Labels and Selectors
- Understand Kubernetes object relationships
- Build a complete Kubernetes application

---

# Recommended Workflow

For every example:

1. Read the comments in the YAML file.
2. Apply the manifest.
3. Verify the created resource.
4. Describe the resource.
5. Inspect related objects.
6. Delete the resource.
7. Modify the manifest and redeploy.

---

# Frequently Used Commands

Create Resource

```bash
kubectl apply -f <file>.yaml
```

View Pods

```bash
kubectl get pods
```

View Deployments

```bash
kubectl get deployments
```

View ReplicaSets

```bash
kubectl get replicasets
```

View Services

```bash
kubectl get svc
```

View Namespaces

```bash
kubectl get namespaces
```

Describe Resource

```bash
kubectl describe <resource> <name>
```

Delete Resource

```bash
kubectl delete -f <file>.yaml
```

---

# Best Practices

- Start with Pods to understand the smallest deployable unit.
- Use Deployments instead of creating standalone Pods for production workloads.
- Allow Deployments to manage ReplicaSets automatically.
- Use Services rather than Pod IP addresses for communication.
- Organize applications using Namespaces.
- Apply meaningful Labels for efficient resource management.
- Keep YAML manifests simple, readable, and well documented.

---

## Key Takeaways

- Pods are the smallest deployable units in Kubernetes.
- Deployments provide declarative application management and automatic updates.
- ReplicaSets maintain the desired number of running Pods.
- Services provide stable networking for applications.
- Namespaces organize cluster resources and support multi-tenancy.
- Labels and Selectors connect Kubernetes resources and enable flexible resource management.
- These foundational resources form the basis of every Kubernetes application.