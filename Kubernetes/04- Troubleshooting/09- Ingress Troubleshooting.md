# Ingress Troubleshooting

## Overview

Ingress is the entry point for HTTP and HTTPS traffic into a Kubernetes cluster. It provides URL routing, host-based routing, TLS termination, and acts as a centralized gateway for multiple applications.

When an Ingress is misconfigured, users may experience errors such as **404 Not Found**, **502 Bad Gateway**, **503 Service Unavailable**, TLS failures, or complete application outages.

This guide explains the most common Ingress issues, how to diagnose them, and practical steps to restore connectivity.

---

# Why Ingress Issues Occur

Ingress problems commonly result from:

- Incorrect routing rules
- Missing Ingress Controller
- Service configuration errors
- Missing Endpoints
- DNS issues
- TLS certificate problems
- Backend application failures

---

# Ingress Not Working

## Symptoms

- Application cannot be reached
- Browser times out
- No response from the application

---

## Investigation

Check Ingress resources:

```bash
kubectl get ingress
```

Describe the Ingress:

```bash
kubectl describe ingress <ingress-name>
```

Verify the Ingress Controller:

```bash
kubectl get pods -n ingress-nginx
```

---

## Resolution

- Verify the Ingress Controller is running.
- Verify routing rules.
- Verify backend Service.
- Verify DNS records.

---

# HTTP 404 Not Found

## Symptoms

```text
404 Not Found
```

---

## Possible Causes

- Incorrect host
- Incorrect path
- Backend Service missing
- Wrong namespace

---

## Investigation

Describe Ingress:

```bash
kubectl describe ingress
```

Verify rules:

```text
Host

↓

Path

↓

Backend Service
```

---

## Resolution

- Correct host configuration.
- Verify path rules.
- Verify backend Service name.
- Verify namespace.

---

# HTTP 502 Bad Gateway

## Symptoms

```text
502 Bad Gateway
```

---

## Possible Causes

- Backend Pods unhealthy
- Service port mismatch
- Application not listening

---

## Investigation

Check Pods:

```bash
kubectl get pods
```

Check Endpoints:

```bash
kubectl get endpoints
```

Check Service:

```bash
kubectl describe svc
```

---

## Resolution

- Restore healthy Pods.
- Verify targetPort.
- Verify application port.

---

# HTTP 503 Service Unavailable

## Symptoms

```text
503 Service Unavailable
```

---

## Possible Causes

- Service has no Endpoints
- Pods not Ready
- Readiness Probe failures

---

## Investigation

```bash
kubectl get endpoints

kubectl get pods

kubectl describe pod <pod-name>
```

---

## Resolution

- Fix Readiness Probe.
- Verify Service selector.
- Ensure Pods become Ready.

---

# TLS Certificate Problems

## Symptoms

Browser displays:

```text
Certificate Invalid

SSL Handshake Failed
```

---

## Possible Causes

- Missing TLS Secret
- Expired certificate
- Wrong hostname
- Invalid certificate chain

---

## Investigation

Check TLS Secret:

```bash
kubectl get secret
```

Describe Ingress:

```bash
kubectl describe ingress
```

---

## Resolution

- Replace expired certificate.
- Verify Secret name.
- Verify hostname.
- Ensure certificate matches the domain.

---

# DNS Not Resolving

## Symptoms

```text
DNS_PROBE_FINISHED_NXDOMAIN
```

---

## Possible Causes

- Missing DNS record
- Incorrect A record
- Incorrect CNAME
- Wrong Load Balancer IP

---

## Investigation

Verify DNS:

```bash
nslookup api.example.com
```

Check external IP:

```bash
kubectl get ingress
```

---

## Resolution

- Update DNS records.
- Verify Load Balancer IP.
- Wait for DNS propagation if changes were recently made.

---

# Backend Service Not Found

## Symptoms

Ingress exists but traffic never reaches the application.

---

## Investigation

```bash
kubectl get svc
```

Verify backend:

```yaml
backend:
  service:
    name: backend-api
```

---

## Resolution

- Correct Service name.
- Verify namespace.
- Redeploy Ingress.

---

# Service Has No Endpoints

## Symptoms

```text
Endpoints: <none>
```

---

## Investigation

```bash
kubectl get endpoints

kubectl get pods --show-labels
```

---

## Resolution

- Fix Service selector.
- Ensure Pods pass Readiness Probe.
- Verify labels.

---

# Wrong Service Port

## Symptoms

Ingress returns:

```text
502

503
```

---

## Investigation

Describe Service:

```bash
kubectl describe svc
```

Verify:

```text
Ingress Port

↓

Service Port

↓

targetPort

↓

Container Port
```

---

## Resolution

Ensure all ports match correctly.

---

# Ingress Controller Not Running

## Symptoms

Ingress resources exist but nothing responds.

---

## Investigation

```bash
kubectl get pods -n ingress-nginx
```

---

## Resolution

Restart the controller.

Verify:

- Controller Pods
- Service
- Load Balancer

---

# Multiple Applications Not Routing Correctly

## Symptoms

Every request reaches the wrong application.

---

## Investigation

Review:

```yaml
rules:
```

Verify:

- Host
- Path
- Backend

---

## Resolution

Correct routing rules.

Example:

```text
api.example.com

↓

API Service

admin.example.com

↓

Admin Service
```

---

# Ingress Troubleshooting Workflow

```text
Application Not Reachable
           │
           ▼
Check Ingress
           │
           ▼
Check Controller
           │
           ▼
Verify Rules
           │
           ▼
Check Service
           │
           ▼
Check Endpoints
           │
           ▼
Check Pods
           │
           ▼
Verify DNS
           │
           ▼
Verify TLS
```

---

# Useful Commands

```bash
kubectl get ingress

kubectl describe ingress <ingress-name>

kubectl get svc

kubectl describe svc <service-name>

kubectl get endpoints

kubectl get pods

kubectl describe pod <pod-name>

kubectl logs -n ingress-nginx <controller-pod>

kubectl get secret
```

---

# Best Practices

- Use a single Ingress Controller for multiple applications.
- Configure Readiness Probes to prevent traffic reaching unhealthy Pods.
- Use TLS for all production applications.
- Monitor Ingress Controller logs.
- Keep DNS records synchronized with Load Balancer addresses.
- Regularly renew TLS certificates.
- Validate routing rules before deploying to production.

---

# Interview Tips

- A **404** usually indicates incorrect routing rules.
- A **502** generally means the backend application is unreachable or listening on the wrong port.
- A **503** often indicates that the Service has no healthy Endpoints.
- Always verify the complete request flow:

```text
Client

↓

DNS

↓

Load Balancer

↓

Ingress

↓

Service

↓

Endpoints

↓

Pods
```

- Remember that an Ingress resource requires an **Ingress Controller** to process traffic.

---

## Key Takeaways

- Ingress provides centralized HTTP/HTTPS routing for Kubernetes applications.
- Most Ingress issues are caused by routing errors, Service misconfigurations, missing Endpoints, DNS problems, or TLS issues.
- `kubectl describe ingress`, `kubectl get endpoints`, and Ingress Controller logs are the primary tools for troubleshooting.
- Following the request path from the client to the Pod helps isolate connectivity problems quickly and systematically.