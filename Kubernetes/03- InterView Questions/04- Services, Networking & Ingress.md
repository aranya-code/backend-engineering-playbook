# Services, Networking & Ingress

## Overview

Networking is one of the most important aspects of Kubernetes. While Pods run applications, they are temporary and can be recreated at any time. Kubernetes provides **Services** and **Ingress** to ensure applications remain accessible even when Pods change.

Understanding Kubernetes networking is essential for designing scalable, highly available, and production-ready applications.

---

# Why These Questions Matter

Interviewers ask networking questions to evaluate your understanding of:

- Pod communication
- Service discovery
- Load balancing
- Internal vs external traffic
- DNS resolution
- Ingress routing
- Production networking

Networking questions are extremely common in Kubernetes interviews.

---

# Beginner Questions

## 1. Why do we need Kubernetes Services?

**Answer**

Pods are ephemeral.

When a Pod is recreated, it receives a new IP address.

A Service provides:

- Stable IP address
- Stable DNS name
- Load balancing
- Service discovery

Applications communicate through Services instead of directly using Pod IP addresses.

---

## 2. What is a Kubernetes Service?

**Answer**

A Service is an abstraction that exposes one or more Pods using a stable network endpoint.

It automatically routes traffic to healthy Pods matching its selector.

---

## 3. What types of Services are available?

**Answer**

Kubernetes provides four Service types:

- ClusterIP
- NodePort
- LoadBalancer
- ExternalName

Each serves a different networking purpose.

---

## 4. What is a ClusterIP Service?

**Answer**

ClusterIP is the default Service type.

It exposes an application **only inside the cluster**.

Example:

```text
Backend API

↓

ClusterIP Service

↓

Frontend Pods
```

External users cannot access it.

---

## 5. What is a NodePort Service?

**Answer**

NodePort exposes an application through a port on every Worker Node.

Example:

```text
http://Node-IP:30080
```

Useful for:

- Development
- Testing
- Small environments

---

## 6. What is a LoadBalancer Service?

**Answer**

LoadBalancer creates an external load balancer in supported cloud providers.

Traffic flow:

```text
Internet

↓

Cloud Load Balancer

↓

Kubernetes Service

↓

Pods
```

It is commonly used in AWS, Azure, and GCP.

---

## 7. What is an ExternalName Service?

**Answer**

ExternalName maps a Kubernetes Service to an external DNS name.

Example:

```text
database.company.com
```

No proxy is created.

Kubernetes simply returns the external DNS record.

---

## 8. What is Service Discovery?

**Answer**

Service Discovery allows applications to communicate using Service names instead of IP addresses.

Example:

```text
http://user-service

http://payment-service

http://order-service
```

Kubernetes DNS resolves these names automatically.

---

## Intermediate Questions

## 9. How do Services find Pods?

**Answer**

Services use **Label Selectors**.

Example:

Pods:

```yaml
labels:
  app: backend
```

Service:

```yaml
selector:
  app: backend
```

The Service automatically routes traffic to matching Pods.

---

## 10. How does load balancing work?

**Answer**

A Service distributes incoming traffic across all healthy Pods.

Example:

```text
Service

↓

Pod A

Pod B

Pod C
```

This improves availability and scalability.

---

## 11. Can a Service communicate with Pods on different nodes?

**Answer**

Yes.

Services route traffic across the entire cluster regardless of which Worker Node hosts the Pods.

---

## 12. What is kube-proxy?

**Answer**

kube-proxy runs on every Worker Node.

It manages:

- Network rules
- Packet forwarding
- Service load balancing
- Pod communication

---

## 13. What is Kubernetes DNS?

**Answer**

Kubernetes includes an internal DNS service.

It automatically creates DNS records for Services.

Example:

```text
payment-service.default.svc.cluster.local
```

Applications usually use the short Service name.

---

## 14. What is an Ingress?

**Answer**

Ingress manages external HTTP and HTTPS access to Services.

Instead of exposing every application with its own LoadBalancer, one Ingress can route traffic to multiple Services.

---

## 15. What is an Ingress Controller?

**Answer**

Ingress resources only define routing rules.

An **Ingress Controller** implements those rules.

Common controllers include:

- NGINX Ingress Controller
- Traefik
- HAProxy
- AWS Load Balancer Controller

---

## 16. What problems does Ingress solve?

**Answer**

Ingress provides:

- URL routing
- Host-based routing
- TLS termination
- Centralized entry point
- Reduced cloud costs

---

## Advanced Questions

## 17. Explain the traffic flow from the Internet to a Pod.

**Answer**

```text
Client

↓

Load Balancer

↓

Ingress Controller

↓

Ingress

↓

Service

↓

Pod
```

Each component has a specific networking responsibility.

---

## 18. What is the difference between a Service and an Ingress?

**Answer**

| Service | Ingress |
|----------|----------|
| Exposes Pods | Routes HTTP/HTTPS traffic |
| Provides stable IP | Provides URL routing |
| Internal or external | External HTTP/HTTPS entry point |
| Works at Layer 4 | Works at Layer 7 |

---

## 19. Why shouldn't applications use Pod IPs directly?

**Answer**

Pod IPs change whenever Pods are recreated.

Services provide stable networking endpoints.

Applications should always communicate through Services.

---

## 20. What is host-based routing?

**Answer**

Host-based routing directs traffic based on the requested domain.

Example:

```text
api.company.com

↓

API Service

admin.company.com

↓

Admin Service
```

---

## 21. What is path-based routing?

**Answer**

Path-based routing directs traffic using URL paths.

Example:

```text
/api

↓

API Service

/admin

↓

Admin Service
```

---

## 22. Why is ClusterIP the default Service type?

**Answer**

Most microservices communicate internally.

ClusterIP provides secure internal communication without exposing applications to the Internet.

---

## 23. When would you use NodePort?

**Answer**

NodePort is commonly used for:

- Local development
- Testing
- Small clusters
- Demonstrations

In production, LoadBalancer or Ingress is generally preferred.

---

## 24. Can multiple Services point to the same Pods?

**Answer**

Yes.

As long as they use matching label selectors.

This allows applications to expose different ports or networking configurations.

---

## 25. How would you expose multiple applications using one LoadBalancer?

**Answer**

Use an **Ingress Controller**.

Example:

```text
shop.example.com

↓

Shop Service

blog.example.com

↓

Blog Service

api.example.com

↓

API Service
```

One external LoadBalancer serves multiple applications.

---

# Common Mistakes

- Using Pod IP addresses directly.
- Confusing Services with Ingress.
- Assuming Ingress replaces Services.
- Exposing every application using a separate LoadBalancer.
- Forgetting that Services rely on label selectors.

---

# Interview Tips

- Remember the four Service types.
- Understand the difference between Layer 4 (Service) and Layer 7 (Ingress).
- Be able to explain the complete networking flow from a client to a Pod.
- Know why Services exist even when using Ingress.
- Mention Kubernetes DNS when discussing Service Discovery.

---

## Key Takeaways

- Services provide stable networking endpoints for Pods and enable service discovery and load balancing.
- Kubernetes offers ClusterIP, NodePort, LoadBalancer, and ExternalName Service types for different networking scenarios.
- Ingress provides centralized HTTP/HTTPS routing, host-based routing, path-based routing, and TLS termination.
- Services and Ingress work together to expose applications reliably while hiding the temporary nature of Pod IP addresses.
- A strong understanding of Kubernetes networking is essential for designing scalable, production-ready applications and performing well in technical interviews.