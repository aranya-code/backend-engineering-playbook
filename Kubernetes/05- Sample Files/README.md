# Kubernetes Sample Files

## Overview

The **Sample Files** section contains practical Kubernetes manifests that complement the conceptual documentation throughout this playbook.

Instead of focusing on theory, these examples demonstrate how Kubernetes resources are defined, configured, and deployed in real-world environments.

Every YAML file is heavily commented to explain:

- Why the resource exists
- What each field does
- Common configuration options
- Production best practices
- Interview insights
- Common mistakes to avoid

These examples are designed to serve as both a learning resource and a reference for future Kubernetes projects.

---

# Purpose of This Section

Reading Kubernetes documentation is useful, but the fastest way to learn Kubernetes is by working with real manifests.

This section bridges the gap between theory and practice by providing complete, well-documented examples that can be:

- Read line by line
- Applied directly to a Kubernetes cluster
- Modified for experimentation
- Used as templates for production projects

Every example builds upon concepts introduced in earlier sections of this playbook.

---
# Navigation

## 📂 01 – Basics

- [01- Pod.yaml](01-%20Basics/01-%20Pod.yaml)
- [02- Deployment.yaml](01-%20Basics/02-%20Deployment.yaml)
- [03- ReplicaSet.yaml](01-%20Basics/03-%20ReplicaSet.yaml)
- [04- Service-ClusterIP.yaml](01-%20Basics/04-%20Service-ClusterIP.yaml)
- [05- Service-LoadBalancer.yaml](01-%20Basics/05-%20Service-LoadBalancer.yaml)
- [06- Namespace.yaml](01-%20Basics/06-%20Namespace.yaml)
- [07- Labels-Selectors.yaml](01-%20Basics/07-%20Labels-Selectors.yaml)
- [08- Deployment-Service.yaml](01-%20Basics/08-%20Deployment-Service.yaml)

---

## 📂 02 – Configuration

- [01- ConfigMap.yaml](02-%20Configuration/01-%20ConfigMap.yaml)
- [02- Secret.yaml](02-%20Configuration/02-%20Secret.yaml)
- [03- Deployment-With-ConfigMap.yaml](02-%20Configuration/03-%20Deployment-With-ConfigMap.yaml)
- [04- Deployment-With-Secret.yaml](02-%20Configuration/04-%20Deployment-With-Secret.yaml)
- [05- Deployment-With-ConfigMap-Secret.yaml](02-%20Configuration/05-%20Deployment-With-ConfigMap-Secret.yaml)

---

## 📂 03 – Storage

- [01- Persistent-Volume.yaml](03-%20Storage/01-%20Persistent-Volume.yaml)
- [02- PersistentVolume-Claim.yaml](03-%20Storage/02-%20PersistentVolume-Claim.yaml)
- [03- StorageClass.yaml](03-%20Storage/03-%20StorageClass.yaml)
- [04- Deployment-With-PVC.yaml](03-%20Storage/04-%20Deployment-With-PVC.yaml)
- [05- StatefulSet-With-PVC.yaml](03-%20Storage/05-%20StatefulSet-With-PVC.yaml)

---

## 📂 04 – Networking

- [01- Ingress.yaml](04-%20Networking/01-%20Ingress.yaml)
- [02- Ingress-TLS.yaml](04-%20Networking/02-%20Ingress-TLS.yaml)
- [03- NetworkPolicy.yaml](04-%20Networking/03-%20NetworkPolicy.yaml)
- [04- Ingress-Host-Routing.yaml](04-%20Networking/04-%20Ingress-Host-Routing.yaml)
- [05- Ingress-Path-Routing.yaml](04-%20Networking/05-%20Ingress-Path-Routing.yaml)

---

## 📂 05 – Scaling

- [01- Resource-Requests-Limits.yaml](05-%20Scaling/01-%20Resource-Requests-Limits.yaml)
- [02- Horizontal-Pod-Autoscaler.yaml](05-%20Scaling/02-%20Horizontal-Pod-Autoscaler.yaml)
- [03- Vertical-Pod-Autoscaler.yaml](05-%20Scaling/03-%20Vertical-Pod-Autoscaler.yaml)
- [04- Pod-Disruption-Budget.yaml](05-%20Scaling/04-%20Pod-Disruption-Budget.yaml)

---

## 📂 06 – Production

- [01- Rolling-Update.yaml](06-%20Production/01-%20Rolling-Update.yaml)
- [02- Liveness-Readiness-Startup-Probes.yaml](06-%20Production/02-%20Liveness-Readiness-Startup-Probes.yaml)
- [03- Deployment-Strategy.md](06-%20Production/03-%20Deployment-Strategy.md)
- [04- Production-Deployment.yaml](06-%20Production/04-%20Production-Deployment.yaml)
- [05- Production-Stack-Architecture.md](06-%20Production/05-%20Production-Stack-Architecture.md)

---

# Learning Roadmap

The folders are organized from beginner to production-level concepts.

```text
Basics
   │
   ▼
Configuration
   │
   ▼
Storage
   │
   ▼
Networking
   │
   ▼
Scaling
   │
   ▼
Production
```

Each section introduces new Kubernetes capabilities while reinforcing concepts learned in previous sections.

---

# Section Overview

## 01 – Basics

Learn the fundamental Kubernetes resources that form the foundation of every application.

Topics include:

- Pods
- ReplicaSets
- Deployments
- Services
- Namespaces
- Labels
- Selectors

---

## 02 – Configuration

Learn how applications receive configuration and sensitive information.

Topics include:

- ConfigMaps
- Secrets
- Environment Variables
- Injecting Configuration
- Managing Sensitive Data

---

## 03 – Storage

Learn how Kubernetes manages persistent application data.

Topics include:

- Persistent Volumes
- Persistent Volume Claims
- Storage Classes
- Persistent Storage in Deployments
- Stateful Workloads

---

## 04 – Networking

Learn how applications communicate both inside and outside the cluster.

Topics include:

- Ingress
- TLS
- Host Routing
- Path Routing
- Network Policies

---

## 05 – Scaling

Learn how Kubernetes automatically manages application capacity and resource allocation.

Topics include:

- Resource Requests
- Resource Limits
- Horizontal Pod Autoscaler
- Vertical Pod Autoscaler
- Pod Disruption Budgets

---

## 06 – Production

Learn how production Kubernetes deployments are built.

Topics include:

- Rolling Updates
- Health Probes
- Deployment Strategies
- Production Deployment
- Production Architecture

---

# Example Design Philosophy

Every example follows the same structure to make learning consistent.

```text
Overview

↓

Well Commented Manifest

↓

Architecture Diagram

↓

Useful Commands

↓

Common Mistakes

↓

Best Practices

↓

Interview Tips
```

This standardized format allows you to quickly understand any resource without repeatedly consulting external documentation.

---

# How to Use These Examples

For every example:

1. Read the introductory comments.
2. Understand each YAML section.
3. Deploy the manifest to a test cluster.
4. Verify the created resources.
5. Modify values and observe the results.
6. Delete the resource and repeat.

Hands-on experimentation is the best way to understand Kubernetes behavior.

---

# Recommended Practice Workflow

```text
Read Example

      │

      ▼

Understand YAML

      │

      ▼

Deploy Resource

      │

      ▼

Inspect Resource

      │

      ▼

Modify Configuration

      │

      ▼

Observe Changes

      │

      ▼

Repeat
```

---

# Production Focus

Although these examples are educational, they are written with production environments in mind.

Where appropriate, they include:

- Resource Requests & Limits
- Health Probes
- Rolling Updates
- Security Contexts
- Persistent Storage
- Graceful Shutdown
- High Availability
- Production Deployment Practices

This ensures the examples reflect how Kubernetes is commonly used in professional environments rather than simplified demonstrations.

---

# Best Practices

- Deploy examples in a local Kubernetes cluster such as Minikube or Kind before using them elsewhere.
- Read the comments before applying the manifests.
- Modify one setting at a time to understand its impact.
- Inspect created resources using `kubectl describe`.
- Review Kubernetes Events when troubleshooting.
- Use these examples as templates rather than copying them unchanged into production.

---

## Key Takeaways

- The Sample Files section transforms Kubernetes concepts into practical, deployable examples.
- Every manifest is designed to explain not only *how* Kubernetes resources work, but also *why* they are configured in a particular way.
- The examples progress from fundamental resources to production-ready deployment patterns, providing a structured hands-on learning experience.
- Together, these examples serve as reusable templates, interview preparation material, and a long-term reference for building Kubernetes applications.