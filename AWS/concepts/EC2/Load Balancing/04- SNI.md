# SNI (Server Name Indication) for SSL Certificates

## Definition

SNI allows multiple SSL certificates to be hosted on the same server or load balancer using a single IP address.

---

# Problem Before SNI

Traditionally:
- One SSL certificate required one IP address

This was expensive and inefficient.

---

# How SNI Works

During SSL handshake:
- Client sends hostname information
- Load balancer selects the correct certificate

Example:

- api.example.com → API certificate
- admin.example.com → Admin certificate

Both can use:
- Same ALB
- Same IP

---

# AWS Support for SNI

AWS ALB supports:
- Multiple SSL certificates
- Smart certificate selection using SNI

---

# Benefits of SNI

- Multiple HTTPS websites on one ALB
- Lower infrastructure cost
- Easier certificate management
- Better scalability

---

# Important Limitation

Very old browsers may not support SNI.

Modern browsers support it without issues.

---

# Real-World Example

Single ALB hosting:

- app.company.com
- admin.company.com
- api.company.com

Each domain:
- Uses separate SSL certificate
- Shares same ALB

---

# Interview Notes

## Common Question

### Why is SNI important?

Because it allows:
- Multiple SSL certificates
- Single IP address
- Better resource utilization

---

# Quick Revision

| Topic | Key Point |
|---|---|
| Sticky Sessions | Client always hits same instance |
| ACM | AWS managed SSL certificate service |
| SSL Termination | HTTPS ends at load balancer |
| SNI | Multiple SSL certs on one ALB/IP |