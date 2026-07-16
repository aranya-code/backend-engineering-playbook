# Overview

An **Ingress Issue** occurs when external traffic cannot successfully reach an application running inside a Kubernetes cluster through the **Nginx Ingress Controller**.

Unlike traditional Nginx deployments, Kubernetes introduces additional networking layers:

- Ingress
- Ingress Controller
- Services
- Endpoints
- Pods
- Cluster Networking

A problem in **any** of these layers can prevent requests from reaching the application.

Common symptoms include:

- 404 Not Found
- 502 Bad Gateway
- 503 Service Unavailable
- 504 Gateway Timeout
- TLS failures
- DNS failures

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🔴 Critical |
| Performance | 🟡 Medium |
| Security | 🟡 Medium |
| Production Risk | 🔴 Critical |

---

# When You'll See This

This issue commonly occurs when:

- Deploying a new Ingress
- Updating Services
- Deploying new Pods
- Configuring TLS
- Migrating applications
- Rolling updates
- DNS changes

---

# Affected Components

- Kubernetes Ingress
- Nginx Ingress Controller
- Service
- Endpoint
- Pod
- Deployment
- DNS
- TLS

---

# Symptoms

## Browser

```text
404 Not Found
```

---

Another Example

```text
502 Bad Gateway
```

---

Another Example

```text
503 Service Unavailable
```

---

Nginx Ingress Logs

```text
no endpoints available for service
```

---

Another Example

```text
service not found
```

---

Kubectl

```text
CrashLoopBackOff
```

---

# Quick Diagnosis

## Check Pods

```bash
kubectl get pods -A
```

---

## Check Services

```bash
kubectl get svc
```

---

## Check Endpoints

```bash
kubectl get endpoints
```

---

## Check Ingress

```bash
kubectl get ingress
```

---

## Describe Ingress

```bash
kubectl describe ingress <ingress-name>
```

---

## Check Controller Logs

```bash
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

---

# Decision Tree

```text
             Request Fails
                  │
                  ▼
          Is Ingress Created?
            │             │
           No            Yes
            │             │
            ▼             ▼
      Apply Manifest   Service Exists?
                              │
                    ┌─────────┴─────────┐
                    │                   │
                   No                  Yes
                    │                   │
                    ▼                   ▼
             Create Service      Endpoints Ready?
                                       │
                             ┌─────────┴─────────┐
                             │                   │
                            No                  Yes
                             │                   │
                             ▼                   ▼
                       Check Pods        Check Controller
                                              │
                                              ▼
                                         Verify DNS
```

---

# Why This Happens

Request flow inside Kubernetes:

```text
Internet

↓

DNS

↓

Load Balancer

↓

Ingress

↓

Nginx Ingress Controller

↓

Service

↓

Pod

↓

Application
```

A failure anywhere in this chain prevents the request from reaching the application.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Missing Ingress | No routing rule exists |
| Service missing | Ingress points to a non-existent Service |
| No endpoints | Service has no healthy Pods |
| Pod crash | Backend application unavailable |
| Label mismatch | Service selector doesn't match Pods |
| DNS issue | Domain doesn't resolve to Ingress IP |
| TLS misconfiguration | Invalid secret or certificate |

---

# Error Message Decoder

## No Endpoints Available

```text
no endpoints available for service
```

### Meaning

The Service has no healthy Pods.

### Solution

Check:

```bash
kubectl get endpoints
```

---

## Service Not Found

```text
service not found
```

### Meaning

Ingress references a Service that doesn't exist.

### Solution

Verify:

```bash
kubectl get svc
```

---

## Default Backend - 404

```text
404 Not Found

default backend
```

### Meaning

The request doesn't match any Ingress rule.

### Solution

Verify:

- Host
- Path
- Ingress rules

---

# Step-by-Step Troubleshooting

## Step 1 — Verify Pods

```bash
kubectl get pods
```

Expected

```text
Running
```

---

## Step 2 — Verify Services

```bash
kubectl get svc
```

Ensure the Service exists.

---

## Step 3 — Verify Endpoints

```bash
kubectl get endpoints
```

Example

```text
backend-service

10.244.0.12:8000
```

If no endpoints exist, verify Pod labels.

---

## Step 4 — Verify Ingress

```bash
kubectl describe ingress
```

Check:

- Host
- Path
- Backend Service
- TLS

---

## Step 5 — Verify Labels

Deployment

```yaml
labels:

  app: backend
```

Service

```yaml
selector:

  app: backend
```

Labels must match.

---

## Step 6 — Review Controller Logs

```bash
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

Look for:

- Routing failures
- TLS errors
- Service lookup failures

---

## Step 7 — Verify DNS

```bash
nslookup example.com
```

Ensure the domain resolves to the Ingress Load Balancer.

---

# Best Practices

- Always use readiness probes.
- Use rolling deployments.
- Keep labels consistent.
- Monitor Ingress Controller logs.
- Validate manifests before deployment.
- Configure health checks.

---

# Real Production Scenario

## Problem

A new application was deployed successfully.

Users received:

```text
503 Service Unavailable
```

---

## Investigation

Pods:

```bash
kubectl get pods
```

were healthy.

However,

```bash
kubectl get endpoints
```

returned:

```text
<none>
```

The Service selector was:

```yaml
app: api
```

while the Deployment labels were:

```yaml
app: backend
```

The Service could not discover any Pods.

---

## Resolution

The Service selector was updated:

```yaml
selector:

  app: backend
```

Endpoints appeared immediately.

Traffic began flowing without restarting the Ingress Controller.

---

# Verification Checklist

After fixing the issue:

- ✅ Pods are Running
- ✅ Services exist
- ✅ Endpoints are populated
- ✅ Labels match
- ✅ Ingress rules are correct
- ✅ DNS resolves correctly
- ✅ HTTPS works
- ✅ Application returns HTTP 200

---

# Common Mistakes

❌ Service selector doesn't match Pod labels

❌ Wrong Service name in Ingress

❌ Missing Ingress Controller

❌ Forgetting TLS Secret

❌ Wrong namespace

❌ Assuming the Pod is the problem without checking Endpoints

---

# Prevention Tips

- Use consistent labels across Deployments and Services.
- Always verify Endpoints after deployment.
- Use readiness and liveness probes.
- Validate Kubernetes manifests before applying them.
- Monitor Ingress Controller logs continuously.
- Configure alerts for unhealthy Services and Pods.

---

# Production Notes

When troubleshooting Kubernetes Ingress, always investigate in this order:

1. Is the Pod running?
2. Does the Service exist?
3. Does the Service have Endpoints?
4. Do Service selectors match Pod labels?
5. Is the Ingress configured correctly?
6. Is the Ingress Controller running?
7. Does DNS resolve correctly?
8. Is the TLS Secret valid?

**More than 90% of Kubernetes Ingress issues are caused by missing Endpoints, incorrect Service selectors, or invalid Ingress rules—not by the Nginx Ingress Controller itself.**

---

