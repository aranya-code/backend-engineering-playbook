# Kubernetes CLI

## Overview

The **Kubernetes CLI** section focuses on using **kubectl**, the command-line interface for interacting with Kubernetes clusters. While the Concepts section explains *how Kubernetes works*, this section demonstrates *how to perform real-world tasks* using practical commands.

Whether you're deploying applications, inspecting Pods, troubleshooting issues, or managing cluster resources, `kubectl` is the primary tool used by Kubernetes administrators, DevOps engineers, and backend developers.

This section is designed as a practical reference with commonly used commands that you'll use daily when working with Kubernetes.

---

# Why Learn kubectl?

`kubectl` is the official command-line tool for Kubernetes.

Learning it enables you to:

- Deploy applications
- Manage cluster resources
- Debug production issues
- View logs and events
- Scale applications
- Configure networking
- Inspect storage
- Perform rolling updates
- Troubleshoot failed deployments
- Prepare for Kubernetes interviews

Nearly every Kubernetes operation eventually translates into a `kubectl` command.

---

# Topics Covered

This section covers:

- Setting up Minikube
- Working with Kubernetes contexts
- Writing YAML manifests
- Managing Namespaces
- Creating and inspecting Pods
- Managing ReplicaSets
- Deployments
- Services
- Ingress
- ConfigMaps and Secrets
- Labels and Selectors
- Persistent Volumes
- StorageClasses
- Debugging commands
- Helm CLI
- Productivity aliases

---

# Navigation

| Step | Topic | Description |
|------|-------|-------------|
| 01 | [Minikube](01-%20Minikube.md) | Install and run a local Kubernetes cluster. |
| 02 | [Cluster and Context](02-%20Cluster%20and%20Context.md) | Configure clusters, users, and contexts. |
| 03 | [YAML](03-%20YAML.md) | Create and manage Kubernetes resource manifests. |
| 04 | [Namespaces](04-%20Namespaces.md) | Organize workloads into isolated environments. |
| 05 | [Pods](05-%20Pods.md) | Create, inspect, and manage Pods. |
| 06 | [ReplicaSets](06-%20ReplicaSets.md) | Maintain the desired number of Pod replicas. |
| 07 | [Deployments](07-%20Deployments.md) | Deploy applications and manage rollouts. |
| 08 | [Services](08-%20Services.md) | Expose applications within and outside the cluster. |
| 09 | [Ingress](09-%20Ingress.md) | Route HTTP and HTTPS traffic to Services. |
| 10 | [ConfigMaps and Secrets](10-%20ConfigMaps%20and%20Secrets.md) | Store application configuration and sensitive data. |
| 11 | [Labels and Selectors](11-%20Labels%20and%20Selectors.md) | Organize and query Kubernetes resources. |
| 12 | [Persistent Volumes](12-%20Persistent%20Volumes.md) | Manage persistent storage for applications. |
| 13 | [StorageClass](13-%20StorageClass.md) | Configure dynamic storage provisioning. |
| 14 | [Debugging](14-%20Debugging.md) | Troubleshoot Pods, Deployments, Services, and cluster resources. |
| 15 | [Helm](15-%20Helm.md) | Manage Kubernetes packages using Helm. |
| 16 | [Useful Aliases](16-%20Useful%20Aliases.md) | Improve productivity with commonly used kubectl aliases. |

---

# Learning Path

Follow the files in the following order:

```text
Minikube
      │
      ▼
Cluster & Context
      │
      ▼
YAML
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
Ingress
      │
      ▼
ConfigMaps & Secrets
      │
      ▼
Labels & Selectors
      │
      ▼
Persistent Volumes
      │
      ▼
StorageClass
      │
      ▼
Debugging
      │
      ▼
Helm
      │
      ▼
Useful Aliases
```

---

# Prerequisites

Before using these commands, you should have:

- Basic Kubernetes knowledge
- Docker installed (recommended)
- kubectl installed
- Minikube or access to a Kubernetes cluster
- Basic understanding of YAML

---

# Quick Navigation

| Category | Description |
|----------|-------------|
| **Cluster Setup** | Minikube and Kubernetes contexts |
| **Resource Management** | Pods, ReplicaSets, Deployments, Services |
| **Networking** | Ingress and Service management |
| **Configuration** | ConfigMaps, Secrets, Labels |
| **Storage** | Persistent Volumes and StorageClasses |
| **Troubleshooting** | Debugging commands and diagnostics |
| **Package Management** | Helm commands |
| **Productivity** | Useful kubectl aliases |

---

# After Completing This Section

After completing this section, you will be able to:

- Confidently use `kubectl` to manage Kubernetes resources.
- Deploy and update applications from the command line.
- Inspect Pods, Deployments, Services, and storage resources.
- Debug common Kubernetes issues using logs, events, and resource descriptions.
- Manage Helm releases for application deployments.
- Navigate Kubernetes clusters efficiently using contexts and aliases.

---

# Key Takeaways

- `kubectl` is the primary interface for interacting with Kubernetes clusters.
- Mastering common CLI commands significantly improves development, deployment, and troubleshooting workflows.
- Understanding how to inspect, manage, and debug resources is essential for production Kubernetes environments.
- This section provides a practical command reference that complements the Kubernetes Concepts notes and prepares you for real-world backend engineering tasks and technical interviews.