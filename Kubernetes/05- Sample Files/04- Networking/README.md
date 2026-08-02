# Kubernetes Networking Examples

## Overview

The **Networking** folder demonstrates how Kubernetes exposes applications to users and controls communication between workloads using **Ingress** and **Network Policies**.

Networking is one of the most important aspects of Kubernetes because applications rarely run in isolation. They need to communicate securely with users, other services, databases, and external systems.

These examples cover both **traffic routing** and **network security**, providing a strong foundation for production Kubernetes deployments.

---

# Why This Section Matters

A Kubernetes application typically receives traffic through an Ingress Controller and communicates internally using Services.

Without proper networking:

- Users cannot access applications.
- Services cannot communicate efficiently.
- Applications become difficult to scale.
- Security boundaries cannot be enforced.

This section teaches how Kubernetes routes, secures, and manages application traffic.

---

# Navigation

| Step | File | Purpose |
|------|------|---------|
| 01 | **01- Ingress.yaml** | Learn how to expose an application using an Ingress resource. |
| 02 | **02- Ingress-TLS.yaml** | Secure applications with HTTPS using TLS certificates. |
| 03 | **03- NetworkPolicy.yaml** | Restrict Pod communication using Kubernetes Network Policies. |
| 04 | **04- Ingress-Host-Routing.yaml** | Route traffic to multiple applications using different hostnames. |
| 05 | **05- Ingress-Path-Routing.yaml** | Route traffic to multiple services using URL paths under a single domain. |

---

# Learning Path

Study these examples in the following order.

```text
Basic Ingress
      │
      ▼
Ingress + TLS
      │
      ▼
Network Policy
      │
      ▼
Host-Based Routing
      │
      ▼
Path-Based Routing
```

---

# Networking Architecture

```text
                  Internet
                      │
                      ▼
               Load Balancer
                      │
                      ▼
            Ingress Controller
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   frontend      backend-api     admin
      │              │             │
      ▼              ▼             ▼
  Kubernetes Services
                      │
                      ▼
                    Pods
```

---

# Host-Based Routing

One hostname maps to one application.

```text
app.company.com
        │
        ▼
Frontend Service


api.company.com
        │
        ▼
Backend Service


admin.company.com
        │
        ▼
Admin Service
```

---

# Path-Based Routing

One hostname serves multiple applications.

```text
company.com/
        │
        ▼
Frontend


company.com/api
        │
        ▼
Backend API


company.com/admin
        │
        ▼
Admin Portal
```

---

# Network Policy Architecture

```text
Frontend Pods
       │
 Allowed
       ▼
Backend Pods
       │
 Allowed
       ▼
Database Pods


Any other traffic

Blocked
```

---

# What You'll Learn

After completing this section, you'll understand how to:

- Configure an Ingress Controller
- Expose applications externally
- Enable HTTPS using TLS
- Configure host-based routing
- Configure path-based routing
- Restrict Pod communication
- Secure workloads using Network Policies
- Design production-ready Kubernetes networking

---

# Typical Production Architecture

```text
                Internet
                    │
                    ▼
             Cloud Load Balancer
                    │
                    ▼
            Ingress Controller
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
  Frontend       Backend API     Admin
      │             │             │
      └─────────────┼─────────────┘
                    ▼
              Kubernetes Services
                    │
                    ▼
                  Pods
                    │
                    ▼
              Network Policies
                    │
                    ▼
                Databases
```

---

# Recommended Workflow

For each example:

1. Read the comments in the YAML file.
2. Deploy the required Services.
3. Apply the networking resource.
4. Verify the resource creation.
5. Test connectivity.
6. Inspect the routing behavior.
7. Modify routing rules.
8. Observe how traffic changes.

---

# Frequently Used Commands

View Ingresses

```bash
kubectl get ingress
```

Short Form

```bash
kubectl get ing
```

Describe an Ingress

```bash
kubectl describe ingress <ingress-name>
```

View Network Policies

```bash
kubectl get networkpolicy
```

Short Form

```bash
kubectl get netpol
```

Describe a Network Policy

```bash
kubectl describe networkpolicy <policy-name>
```

View Services

```bash
kubectl get svc
```

View Endpoints

```bash
kubectl get endpoints
```

Test Connectivity

```bash
curl http://<hostname>
```

---

# Best Practices

- Always deploy an Ingress Controller before creating Ingress resources.
- Use HTTPS for all public-facing applications.
- Store TLS certificates in Kubernetes Secrets.
- Prefer Ingress over multiple LoadBalancer Services for HTTP/HTTPS traffic.
- Use meaningful hostnames and predictable URL paths.
- Apply the principle of least privilege with Network Policies.
- Test routing and security rules before production deployment.
- Monitor the Ingress Controller for traffic, latency, and errors.

---

## Key Takeaways

- Ingress provides Layer 7 routing for HTTP and HTTPS traffic.
- Host-based and path-based routing allow multiple applications to share a single external endpoint.
- TLS secures client communication and is typically terminated at the Ingress Controller.
- Network Policies restrict Pod-to-Pod communication and improve cluster security.
- Together, Ingress and Network Policies form the foundation of production-grade Kubernetes networking.