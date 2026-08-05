# Overview

A **DNS Resolution Failure** occurs when Nginx cannot resolve a hostname to an IP address.

DNS plays a critical role in reverse proxy configurations. Whenever Nginx forwards requests to an upstream server using a hostname instead of an IP address, it must first resolve that hostname.

If DNS resolution fails, Nginx cannot establish a connection with the backend server, resulting in application failures.

This issue commonly affects:

- Reverse Proxy
- Upstream Servers
- Docker Compose
- Kubernetes
- Load Balancers
- External APIs

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🔴 Critical |
| Performance | 🟡 Medium |
| Security | 🟢 None |
| Production Risk | 🔴 High |

---

# When You'll See This

This issue commonly occurs when:

- Backend hostname changes
- DNS server is unavailable
- Docker service names are incorrect
- Kubernetes Services are renamed
- Reverse proxy points to a non-existent host
- Firewall blocks DNS traffic
- External APIs change DNS records

---

# Affected Components

- DNS
- Reverse Proxy
- Upstream Servers
- Docker Networking
- Kubernetes Services
- Resolver Directive

---

# Symptoms

## Browser

```text
502 Bad Gateway
```

---

## Nginx Error Log

```text
host not found in upstream
```

---

Another Example

```text
no resolver defined to resolve
```

---

Docker

```text
Temporary failure in name resolution
```

---

Kubernetes

```text
Name or service not known
```

---

# Quick Diagnosis

## Test DNS Resolution

```bash
nslookup backend.example.com
```

---

## Using dig

```bash
dig backend.example.com
```

---

## Check Resolver Configuration

```bash
cat /etc/resolv.conf
```

---

## Test Network Connectivity

```bash
ping backend.example.com
```

---

## Validate Configuration

```bash
sudo nginx -t
```

---

# Decision Tree

```text
             Backend Unreachable
                     │
                     ▼
            Is Hostname Correct?
               │            │
              No           Yes
               │            │
               ▼            ▼
         Fix Hostname    Resolve DNS?
                              │
                     ┌────────┴─────────┐
                     │                  │
                    No                 Yes
                     │                  │
                     ▼                  ▼
             Check DNS Server     Check Backend
             Check Resolver       Check Firewall
                     │
                     ▼
             Reload Configuration
```

---

# Why This Happens

Request flow:

```text
Client

↓

Nginx

↓

DNS Lookup

↓

Backend IP Address

↓

Backend Server

↓

Response
```

If DNS resolution fails:

```text
DNS Lookup

↓

Failed

↓

502 Bad Gateway
```

Nginx cannot connect to the upstream server.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Incorrect hostname | Typographical error |
| DNS server unavailable | Resolver cannot answer queries |
| Missing resolver directive | Required for dynamic DNS resolution |
| Docker service renamed | Old hostname still configured |
| Kubernetes Service missing | Service name cannot be resolved |
| Firewall | DNS requests blocked |
| Expired DNS records | Cached records outdated |

---

# Error Message Decoder

## Host Not Found

```text
host not found in upstream
```

### Meaning

The configured hostname cannot be resolved.

### Solution

Verify the hostname and DNS configuration.

---

## No Resolver Defined

```text
no resolver defined to resolve
```

### Meaning

Nginx requires a DNS resolver but none has been configured.

### Solution

Configure a resolver.

Example:

```nginx
resolver 8.8.8.8 valid=30s;
```

or use your organization's internal DNS server.

---

## Temporary Failure in Name Resolution

```text
Temporary failure in name resolution
```

### Meaning

The DNS server is temporarily unavailable.

### Solution

Verify network connectivity and DNS server health.

---

# Step-by-Step Troubleshooting

## Step 1 — Verify Hostname

Example

```nginx
proxy_pass http://backend:8000;
```

Ensure:

```text
backend
```

exists and is reachable.

---

## Step 2 — Test DNS

```bash
nslookup backend
```

or

```bash
dig backend
```

Expected

```text
Address:

192.168.x.x
```

---

## Step 3 — Verify Resolver

```bash
cat /etc/resolv.conf
```

Example

```text
nameserver 8.8.8.8
```

---

## Step 4 — Configure Resolver (If Required)

Example

```nginx
resolver 8.8.8.8 valid=30s;

resolver_timeout 5s;
```

Reload Nginx after making changes.

---

## Step 5 — Verify Docker or Kubernetes

Docker

```bash
docker network inspect bridge
```

Verify service names.

---

Kubernetes

```bash
kubectl get svc
```

Ensure the Service exists.

---

## Step 6 — Validate Configuration

```bash
sudo nginx -t
```

---

## Step 7 — Reload Nginx

```bash
sudo systemctl reload nginx
```

---

# Best Practices

- Use reliable DNS servers.
- Avoid hardcoding IP addresses unless necessary.
- Use Docker Compose service names.
- Use Kubernetes Service names.
- Configure the `resolver` directive for dynamic upstreams.
- Monitor DNS availability.

---

# Real Production Scenario

## Problem

A production API suddenly began returning:

```text
502 Bad Gateway
```

---

## Investigation

The Nginx error log contained:

```text
host not found in upstream "api-service"
```

The backend team had renamed the Kubernetes Service from:

```text
api-service
```

to

```text
backend-service
```

The Nginx Ingress configuration still referenced the old service name.

---

## Resolution

The upstream configuration was updated:

```nginx
proxy_pass http://backend-service:8000;
```

After reloading Nginx, traffic was restored immediately.

---

# Verification Checklist

After fixing the issue:

- ✅ Hostname resolves successfully
- ✅ DNS server is reachable
- ✅ Resolver configuration is correct
- ✅ Docker/Kubernetes service names are valid
- ✅ Nginx configuration validates
- ✅ Website returns HTTP 200

---

# Common Mistakes

❌ Misspelling backend hostnames

❌ Forgetting the `resolver` directive

❌ Hardcoding outdated IP addresses

❌ Assuming Docker and Kubernetes use the same DNS behavior

❌ Ignoring DNS cache updates

❌ Not testing hostname resolution from the Nginx host/container

---

# Prevention Tips

- Use service discovery whenever possible.
- Monitor DNS availability.
- Standardize service naming.
- Avoid manual IP management.
- Test DNS resolution after infrastructure changes.
- Document upstream hostnames and DNS dependencies.

---

# Production Notes

DNS failures are often mistaken for application or Nginx issues.

When troubleshooting, investigate in this order:

1. Verify the configured hostname
2. Test DNS resolution (`nslookup` or `dig`)
3. Check `/etc/resolv.conf`
4. Verify Docker or Kubernetes service names
5. Configure the `resolver` directive if required
6. Test backend connectivity

A healthy backend is unreachable if its hostname cannot be resolved, making DNS a critical dependency in modern Nginx deployments.

---
