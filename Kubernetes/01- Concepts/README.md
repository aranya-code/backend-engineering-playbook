# Kubernetes Concepts

## Overview

The **Concepts** section is the foundation of this Kubernetes playbook. It introduces the core building blocks, architecture, and essential features that every backend engineer should understand before working with Kubernetes in production.

The topics in this folder follow a logical learning progression—from understanding what Kubernetes is, to deploying applications, managing configuration, scaling workloads, and performing production-ready deployments.

Whether you're learning Kubernetes for the first time or preparing for technical interviews, these notes provide a practical and interview-focused understanding of Kubernetes fundamentals.

---

# Why Learn Kubernetes Concepts?

Kubernetes has become the industry standard for container orchestration. Understanding its core concepts enables you to:

- Deploy containerized applications reliably
- Build highly available systems
- Scale applications automatically
- Manage application configuration securely
- Understand production deployment strategies
- Troubleshoot common Kubernetes issues
- Prepare for backend engineering and DevOps interviews

These concepts form the foundation for advanced topics such as networking, storage, security, monitoring, and production operations.

---

# Topics Covered

This section covers:

- Kubernetes fundamentals
- Cluster architecture
- Core Kubernetes resources
- Labels and Selectors
- YAML configuration
- Namespaces
- Services
- Pods
- ReplicaSets
- Deployments
- ConfigMaps and Secrets
- Persistent Storage
- StatefulSets
- Helm
- kubectl basics
- Local Kubernetes with Minikube
- Pod Lifecycle
- Health Probes
- Resource Management
- Horizontal Pod Autoscaling
- Deployment Strategies

---

# Learning Path

It is recommended to study the notes in the following order:

```text
Introduction
        │
        ▼
Core Components
        │
        ▼
Labels & YAML Basics
        │
        ▼
Namespaces
        │
        ▼
Pods
        │
        ▼
ReplicaSets
        │
        ▼
Deployments
        │
        ▼
Services
        │
        ▼
ConfigMaps & Secrets
        │
        ▼
Persistent Storage
        │
        ▼
StatefulSets
        │
        ▼
Helm
        │
        ▼
kubectl
        │
        ▼
Minikube
        │
        ▼
Pod Lifecycle
        │
        ▼
Health Probes
        │
        ▼
Resource Management
        │
        ▼
Horizontal Pod Autoscaler
        │
        ▼
Deployment Strategies
```

---

# Navigation

| Step | Topic | Description |
|------|-------|-------------|
| 01 | [Introduction](01-%20Introduction.md) | Learn what Kubernetes is, why it exists, and how it solves container orchestration challenges. |
| 02 | [Core Components](02-%20Core%20Components.md) | Explore the Kubernetes architecture, control plane, worker nodes, and cluster components. |
| 03 | [Labels, Selectors & YAML Basics](03-%20Labels,%20Selectors%20&%20YAML%20Basics.md) | Understand resource organization, selectors, and Kubernetes YAML manifests. |
| 04 | [Namespaces](04-%20Namespaces.md) | Organize resources into isolated environments within a cluster. |
| 05 | [Ingress](05-%20Ingress.md) | Route external HTTP/HTTPS traffic to services using Ingress resources. |
| 06 | [Helm](06-%20Helm.md) | Learn how Helm simplifies Kubernetes application deployment and management. |
| 07 | [Persistent Storage](07-%20Persistent%20Storage.md) | Persist application data using Volumes, Persistent Volumes, and Persistent Volume Claims. |
| 08 | [StatefulSets](08-%20StatefulSets.md) | Deploy and manage stateful applications with stable identities and storage. |
| 09 | [Kubernetes Services](09-%20Kubernetes%20Services.md) | Learn ClusterIP, NodePort, LoadBalancer, and ExternalName Services. |
| 10 | [Pods](10-%20Pods.md) | Understand the smallest deployable unit in Kubernetes. |
| 11 | [ReplicaSets](11-%20ReplicaSets.md) | Maintain the desired number of Pod replicas automatically. |
| 12 | [Deployments](12-%20Deployments.md) | Perform rolling updates, rollbacks, and manage application deployments. |
| 13 | [ConfigMaps & Secrets](13-%20ConfigMaps%20&%20Secrets.md) | Store application configuration and sensitive data securely. |
| 14 | [kubectl Commands](14-%20kubectl%20Commands.md) | Learn essential commands for managing Kubernetes clusters. |
| 15 | [Minikube](15-%20Minikube.md) | Create and manage a local Kubernetes cluster for development and testing. |
| 16 | [Pod Lifecycle](16-%20Pod%20Lifecycle.md) | Explore Pod phases, container states, restart policies, and graceful termination. |
| 17 | [Probes (Liveness, Readiness & Startup)](17-%20Probes%20(Liveness,%20Readiness%20&%20Startup).md) | Configure health checks to improve application reliability. |
| 18 | [Resource Requests and Limits](18-%20Resource%20Requests%20and%20Limits.md) | Manage CPU and memory allocation for efficient workloads. |
| 19 | [Horizontal Pod Autoscaler (HPA)](19-%20Horizontal%20Pod%20Autoscaler%20(HPA).md) | Automatically scale applications based on resource utilization. |
| 20 | [Deployment Strategies](20-%20Deployment%20Strategies.md) | Learn Rolling Updates, Recreate, Blue-Green, and Canary deployment strategies. |

---

# Prerequisites

Before starting this section, you should have a basic understanding of:

- Containers
- Docker fundamentals
- Linux command line
- Basic networking concepts
- YAML syntax

While not mandatory, familiarity with these topics will make learning Kubernetes much easier.


---

# After Completing This Section

By the end of these notes, you will be able to:

- Explain Kubernetes architecture and core components.
- Deploy applications using Pods and Deployments.
- Expose applications with Services and Ingress.
- Store configuration using ConfigMaps and Secrets.
- Configure persistent storage for stateful workloads.
- Monitor application health with probes.
- Manage CPU and memory resources effectively.
- Automatically scale workloads using HPA.
- Perform rolling updates and rollbacks confidently.
- Build a strong conceptual foundation for production Kubernetes environments.

---

# Key Takeaways

- Kubernetes Concepts provide the foundational knowledge required to understand container orchestration.
- These topics cover the core resources, architecture, deployment patterns, and operational practices used in modern Kubernetes clusters.
- Learning the concepts in the recommended order helps build a strong understanding before moving on to advanced topics such as networking, security, troubleshooting, and production deployments.
- Mastering these fundamentals prepares you for real-world backend engineering projects, cloud-native application development, and Kubernetes-focused technical interviews.