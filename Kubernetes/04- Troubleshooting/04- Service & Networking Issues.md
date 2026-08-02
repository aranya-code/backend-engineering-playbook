# Service & Networking Issues

## Overview

Networking issues are among the most common problems encountered in Kubernetes. Even if Pods are running successfully, users may still be unable to access the application due to incorrect Service configurations, DNS problems, Ingress issues, or networking policies.

This guide explains common Service and networking problems, how to investigate them, and practical solutions for restoring connectivity.

---

# Why Networking Issues Occur

Networking problems commonly result from:

- Incorrect Service selectors
- Wrong ports
- Missing Endpoints
- DNS failures
- Ingress configuration issues
- Network Policies
- Application not listening on the expected port

Understanding Kubernetes networking is essential for troubleshooting production environments.

---

# Service Cannot Reach Pods

## Symptoms

- Service exists
- Pods are running
- Application cannot be accessed

---

## Possible Causes

- Incorrect label selector
- Wrong namespace
- Wrong targetPort
- Application not listening

---

## Investigation

Check Service:

```bash
kubectl get svc
```

Describe Service:

```bash
kubectl describe svc <service-name>
```

Check Pod labels:

```bash
kubectl get pods --show-labels
```

---

## Resolution

- Verify labels
- Verify selectors
- Verify namespace
- Verify application port

---

# Service Has No Endpoints

## Symptoms

```text
ENDPOINTS

<none>
```

---

## Possible Causes

- Selector mismatch
- Pods not Ready
- Wrong namespace

---

## Investigation

```bash
kubectl get endpoints

kubectl describe svc <service-name>

kubectl get pods --show-labels
```

---

## Resolution

Ensure:

```yaml
selector:
  app: backend
```

matches:

```yaml
labels:
  app: backend
```

Pods must also pass their Readiness Probe before becoming Endpoints.

---

# Wrong targetPort

## Symptoms

Connection refused.

---

## Example

Service:

```yaml
targetPort: 8080
```

Application:

```text
Listening on 8000
```

---

## Investigation

Check Service:

```bash
kubectl describe svc <service-name>
```

Check container ports:

```bash
kubectl describe pod <pod-name>
```

---

## Resolution

Update the Service so that:

```text
targetPort

↓

Matches

↓

Container Port
```

---

# DNS Resolution Failure

## Symptoms

Application cannot resolve another Service.

Example:

```text
Temporary failure in name resolution
```

---

## Investigation

Start a temporary Pod:

```bash
kubectl run dns-test --image=busybox --restart=Never -it -- sh
```

Inside the Pod:

```bash
nslookup backend-service
```

---

## Resolution

Verify:

- Service exists
- Correct namespace
- CoreDNS is running

Check CoreDNS:

```bash
kubectl get pods -n kube-system
```

---

# Pod Cannot Reach Another Pod

## Possible Causes

- Network Policy
- Wrong Service
- DNS failure
- Application not listening

---

## Investigation

Test connectivity:

```bash
kubectl exec -it <pod-name> -- sh
```

Inside the Pod:

```bash
ping backend-service

wget backend-service
```

---

## Resolution

- Verify Service
- Verify Endpoints
- Verify Network Policies

---

# NodePort Not Accessible

## Symptoms

Cannot access:

```text
Node-IP:30080
```

---

## Possible Causes

- Wrong Node IP
- Firewall
- Incorrect NodePort
- Application not listening

---

## Investigation

```bash
kubectl get svc
```

Verify Node:

```bash
kubectl get nodes -o wide
```

---

## Resolution

- Verify firewall rules
- Verify NodePort
- Verify application port

---

# LoadBalancer EXTERNAL-IP Pending

## Symptoms

```text
EXTERNAL-IP

<pending>
```

---

## Possible Causes

- Running on Minikube
- No cloud provider
- Load Balancer Controller missing

---

## Investigation

```bash
kubectl get svc
```

---

## Resolution

For local development:

```bash
minikube tunnel
```

For cloud:

- Verify cloud integration
- Verify Load Balancer Controller

---

# Ingress Returns 404

## Symptoms

```text
404 Not Found
```

---

## Possible Causes

- Incorrect host
- Wrong path
- Backend Service missing
- Wrong Service port

---

## Investigation

```bash
kubectl describe ingress

kubectl get ingress
```

---

## Resolution

Verify:

- Host
- Path
- Backend Service
- Service Port

---

# Ingress Returns 502 / 503

## Symptoms

```text
502 Bad Gateway

503 Service Unavailable
```

---

## Possible Causes

- Backend Pods unhealthy
- Service has no Endpoints
- Wrong Service port

---

## Investigation

```bash
kubectl get endpoints

kubectl describe ingress

kubectl get pods
```

---

## Resolution

- Restore healthy Pods
- Fix Service selectors
- Verify container ports

---

# TLS Certificate Issues

## Symptoms

Browser displays:

```text
Certificate Invalid

TLS Handshake Failed
```

---

## Investigation

```bash
kubectl describe ingress
```

Verify Secret:

```bash
kubectl get secret
```

---

## Resolution

- Verify certificate
- Verify TLS Secret
- Verify hostname

---

# Network Policy Blocking Traffic

## Symptoms

Pods cannot communicate.

---

## Investigation

```bash
kubectl get networkpolicy
```

Describe policy:

```bash
kubectl describe networkpolicy
```

---

## Resolution

Allow required:

- Ingress traffic
- Egress traffic

Review namespace selectors and Pod selectors.

---

# Application Accessible by Pod IP but Not Service

## Possible Causes

- Service selector mismatch
- Missing Endpoints
- Wrong targetPort

---

## Investigation

```bash
kubectl get svc

kubectl get endpoints
```

---

## Resolution

Verify:

- Labels
- Selectors
- Ports

---

# Service & Networking Troubleshooting Workflow

```text
Application Unreachable
         │
         ▼
Check Pod Status
         │
         ▼
Check Service
         │
         ▼
Check Endpoints
         │
         ▼
Verify Labels
         │
         ▼
Check DNS
         │
         ▼
Check Ingress
         │
         ▼
Review Network Policies
         │
         ▼
Verify Application Port
```

---

# Useful Commands

```bash
kubectl get svc

kubectl describe svc <service-name>

kubectl get endpoints

kubectl get ingress

kubectl describe ingress

kubectl get networkpolicy

kubectl get pods --show-labels

kubectl exec -it <pod-name> -- sh

kubectl get nodes -o wide
```

---

# Best Practices

- Always access Pods through Services.
- Use meaningful labels and selectors.
- Configure Readiness Probes so only healthy Pods receive traffic.
- Use Ingress instead of exposing multiple LoadBalancer Services.
- Monitor DNS and networking components.
- Test connectivity from inside the cluster before investigating external access.

---

# Interview Tips

- A Service without Endpoints usually indicates a selector mismatch or Pods that are not Ready.
- `targetPort` must match the port on which the application listens.
- Kubernetes Services provide Layer 4 load balancing, while Ingress provides Layer 7 HTTP/HTTPS routing.
- Always verify Services, Endpoints, and DNS before assuming there is a networking problem.
- Know how to troubleshoot 404, 502, and 503 responses from an Ingress.

---

## Key Takeaways

- Most Kubernetes networking issues originate from incorrect Service configuration, selector mismatches, missing Endpoints, DNS failures, or Ingress misconfiguration.
- `kubectl get svc`, `kubectl get endpoints`, `kubectl describe ingress`, and `kubectl exec` are essential tools for diagnosing connectivity problems.
- Services provide stable access to Pods, while Ingress manages external HTTP/HTTPS traffic.
- A systematic troubleshooting process helps quickly isolate networking issues and restore application availability.