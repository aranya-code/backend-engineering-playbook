# 10- Architecture Questions

## Overview

CloudFront architecture questions evaluate whether you understand **where a CDN fits within distributed systems**, not just how to configure one. Senior backend interviews focus on designing globally scalable, low-latency, secure, and highly available architectures where CloudFront works alongside ALBs, Kubernetes, API Gateways, object storage, authentication systems, and backend microservices.

A strong architectural answer should explain:

- Why CloudFront is included in the architecture
- Which traffic should and should not be cached
- How requests flow through the system
- Security boundaries
- Failure handling
- Scalability and operational trade-offs

This document contains production-oriented architecture scenarios commonly discussed in backend and system design interviews.

---

## Architecture Question 1: Global Static Website Architecture

### Question

Design a highly available global architecture for a React frontend hosted on AWS.

### Answer

The frontend should be served entirely from CloudFront with S3 as the origin.

```mermaid
flowchart LR
    User((Users Worldwide))

    subgraph AWS
        CF[CloudFront]
        S3[S3 Static Website]
        ACM[ACM Certificate]
        R53[Route 53]
    end

    User --> R53
    R53 --> CF
    CF --> S3
    ACM -. TLS .-> CF
```

### Why this architecture?

| Component | Responsibility |
|---|---|
| Route 53 | Global DNS |
| CloudFront | CDN, TLS termination, caching |
| S3 | Durable static asset storage |
| ACM | HTTPS certificate |

### Design Decisions

- Cache HTML with a short TTL.
- Cache JS/CSS with long TTL and versioned filenames.
- Enable compression.
- Use Origin Access Control instead of a public bucket.
- Invalidate only HTML after deployments.

### Interview Follow-up

**Why not expose S3 directly?**

Because CloudFront provides caching, HTTPS, WAF integration, edge locations, DDoS protection, and origin isolation.

---

## Architecture Question 2: CloudFront in Front of REST APIs

### Question

How would you architect a globally distributed REST API using Django or FastAPI?

### Answer

CloudFront should accelerate cacheable endpoints while forwarding dynamic traffic to the application.

```mermaid
flowchart LR
    User((Client))

    subgraph Edge
        CF[CloudFront]
        WAF[AWS WAF]
    end

    subgraph Backend
        ALB[Application Load Balancer]
        API[Django / FastAPI]
        Redis[(Redis)]
        DB[(PostgreSQL)]
    end

    User --> CF
    CF --> WAF
    WAF --> ALB
    ALB --> API
    API --> Redis
    API --> DB
```

### Cache Strategy

| Endpoint | Cache? | TTL |
|---|---|---|
| `/health` | No | 0 |
| `/products` | Yes | 5–30 min |
| `/search` | Partial | Short TTL |
| `/users/me` | No | 0 |
| `/images/*` | Yes | 24 hrs |

### Why CloudFront?

- Reduce origin load
- Improve global latency
- Cache public API responses
- Protect origin with WAF
- Absorb traffic spikes

---

## Architecture Question 3: Microservices Behind CloudFront

### Question

How do you expose multiple microservices through a single CloudFront distribution?

### Answer

Use path-based behaviors with multiple origins.

```mermaid
flowchart TD
    User((Client))
    CF[CloudFront]

    User --> CF

    CF -->|/api/users| Users[User Service]
    CF -->|/api/orders| Orders[Order Service]
    CF -->|/api/products| Products[Product Service]
    CF -->|/static| S3[S3 Assets]
```

### Behavior Mapping

| Path | Origin |
|---|---|
| `/api/users/*` | User Service |
| `/api/orders/*` | Order Service |
| `/api/products/*` | Product Service |
| `/static/*` | S3 |

### Advantages

- Single public endpoint
- Independent backend deployments
- Unified security
- Centralized TLS

### Production Consideration

Keep cache policies independent per service because products and users have different caching requirements.

---

## Architecture Question 4: CloudFront + Kubernetes

### Question

Design CloudFront for applications running on EKS.

### Answer

CloudFront sits outside Kubernetes and communicates with the ingress controller.

```mermaid
flowchart LR
    User((Global Users))
    CF[CloudFront]
    ALB[Public ALB]
    Ingress[Kubernetes Ingress]
    Services[Microservices]
    Redis[(Redis)]
    DB[(PostgreSQL)]

    User --> CF
    CF --> ALB
    ALB --> Ingress
    Ingress --> Services
    Services --> Redis
    Services --> DB
```

### Why not expose Kubernetes directly?

CloudFront provides:

- Edge caching
- Global latency reduction
- WAF
- Rate limiting
- DDoS mitigation

### Production Tip

Keep ALB private to CloudFront whenever possible using origin restrictions.

---

## Architecture Question 5: Media Streaming Platform

### Question

How would you design a Netflix-like video delivery architecture?

### Answer

Separate metadata APIs from media delivery.

```mermaid
flowchart TD
    User((Viewer))

    User --> CF[CloudFront]

    CF -->|Video| S3[(Video Storage)]
    CF -->|Metadata| API[Django API]

    API --> DB[(PostgreSQL)]
```

### Traffic Characteristics

| Request | Destination |
|---|---|
| Video segments | S3 via CloudFront |
| Playback metadata | API |
| Authentication | API |
| Images | S3 |

### Why CloudFront?

Video files are extremely cacheable, reducing bandwidth costs dramatically.

---

## Architecture Question 6: Private Content Delivery

### Question

Design secure document downloads for authenticated users.

### Answer

Never expose the storage layer publicly.

```mermaid
sequenceDiagram
    participant User
    participant API
    participant CloudFront
    participant S3

    User->>API: Login
    API-->>User: JWT

    User->>API: Request document
    API-->>User: Signed URL

    User->>CloudFront: Download
    CloudFront->>S3: Fetch private object
    S3-->>CloudFront: Document
    CloudFront-->>User: File
```

### Security Layers

- JWT authenticates users
- Backend authorizes access
- Signed URL limits download duration
- Private S3 bucket prevents bypass

---

## Architecture Question 7: Multi-Origin Enterprise Platform

### Question

A company hosts:

- React frontend
- Django APIs
- Product images
- Documentation
- Video tutorials

Design CloudFront.

### Answer

Use dedicated origins.

```mermaid
flowchart TD
    User((Users))
    CF[CloudFront]

    User --> CF

    CF --> Frontend[S3 Frontend]
    CF --> API[Django APIs]
    CF --> Images[S3 Images]
    CF --> Docs[Documentation]
    CF --> Video[Video Storage]
```

### Recommended Behaviors

| Path | Origin | Cache |
|---|---|---|
| `/` | Frontend | Medium |
| `/api/*` | Django | Low |
| `/images/*` | S3 | High |
| `/docs/*` | Documentation | High |
| `/videos/*` | Video Storage | High |

---

## Architecture Question 8: Global SaaS Platform

### Question

How would you reduce latency for customers across multiple continents?

### Answer

CloudFront should terminate traffic globally while regional application clusters serve dynamic workloads.

```mermaid
flowchart TD
    User((Users))

    User --> CF[CloudFront]

    CF --> US[US Region]
    CF --> EU[EU Region]
    CF --> AP[APAC Region]

    US --> USAPI[API Cluster]
    EU --> EUAPI[API Cluster]
    AP --> APAPI[API Cluster]
```

### Key Principle

Static assets are global, but user-specific data remains regional for compliance and latency.

---

## Architecture Question 9: High-Traffic E-Commerce Platform

### Question

Design CloudFront for an e-commerce website serving millions of users.

### Answer

Different content types require different cache strategies.

```mermaid
flowchart LR
    User((Customer))
    CF[CloudFront]

    CF --> HTML[Frontend]
    CF --> Images[S3 Images]
    CF --> API[Product APIs]
    CF --> Checkout[Checkout API]
```

### Cache Matrix

| Resource | Cache |
|---|---|
| Product images | Long |
| CSS/JS | Long |
| Product catalog | Medium |
| Cart | None |
| Checkout | None |
| Inventory | Very short |

### Production Insight

Never cache personalized checkout or payment responses.

---

## Architecture Question 10: Event-Driven Backend

### Question

How does CloudFront fit into a Kafka-based architecture?

### Answer

CloudFront accelerates client-facing traffic, while Kafka remains internal.

```mermaid
flowchart LR
    User((Client))
    CF[CloudFront]
    API[FastAPI]
    Kafka[(Kafka)]
    Worker[Consumers]
    DB[(PostgreSQL)]

    User --> CF
    CF --> API
    API --> Kafka
    Kafka --> Worker
    Worker --> DB
```

### Why CloudFront Doesn't Replace Kafka

CloudFront optimizes HTTP delivery.

Kafka manages asynchronous event processing.

They solve completely different problems.

---

## Architecture Question 11: Edge Authentication

### Question

How would you authenticate requests without sending every request to Django?

### Answer

Move lightweight authorization to the edge.

```mermaid
flowchart LR
    User((Client))
    CF[CloudFront]
    Edge[CloudFront Function]
    API[Django]

    User --> CF
    CF --> Edge
    Edge --> API
```

### Responsibilities

| Layer | Responsibility |
|---|---|
| Edge Function | JWT validation, redirects |
| Django | Business authorization |

### Benefit

Reduce unnecessary origin traffic for invalid requests.

---

## Architecture Question 12: Disaster Recovery Architecture

### Question

Design CloudFront for automatic regional failover.

### Answer

Use origin groups.

```mermaid
flowchart LR
    User((Users))
    CF[CloudFront]

    CF --> Primary[Primary ALB]

    Primary --> API1[Region A]

    CF -. Failover .-> Secondary[Secondary ALB]
    Secondary --> API2[Region B]
```

### Failover Conditions

- ALB unavailable
- Health checks fail
- Origin timeout
- Excessive origin errors

### Important Note

CloudFront failover protects origin availability, not database replication.

---

## Architecture Question 13: Multi-Tenant SaaS

### Question

How do you support tenant-specific branding with CloudFront?

### Answer

Use tenant-aware routing while avoiding unnecessary cache fragmentation.

```mermaid
flowchart TD
    User((Tenant User))
    CF[CloudFront]

    CF --> API[Django]
    CF --> Assets[S3 Branding Assets]
```

### Cache Key

Include only tenant identity if branding changes the response.

Avoid including user identity.

---

## Architecture Question 14: Hybrid Static + Dynamic Architecture

### Question

Why separate static assets from APIs?

### Answer

Because they have fundamentally different performance characteristics.

| Static Assets | APIs |
|---|---|
| Large files | Small payloads |
| Cache for hours | Cache minimally |
| High bandwidth | Low bandwidth |
| S3 origin | Application origin |

### Architecture

```mermaid
flowchart LR
    User((Browser))
    CF[CloudFront]

    CF --> Static[S3]
    CF --> API[Django]
```

### Benefit

Independent scaling and optimized cache policies.

---

## Architecture Question 15: Large File Download Platform

### Question

Design a secure software download platform.

### Answer

```mermaid
flowchart TD
    User((Customer))

    User --> API[License API]
    API --> DB[(Licenses)]

    API --> Signed[Signed URL]

    Signed --> CF[CloudFront]
    CF --> S3[(Software Packages)]
```

### Security

- License verification
- Short-lived signed URLs
- Private bucket
- CloudFront delivery

---

## Architecture Question 16: Global Image Optimization

### Question

How would you serve millions of images efficiently?

### Answer

```mermaid
flowchart LR
    User((Users))
    CF[CloudFront]
    Edge[Image Optimization]
    S3[(Original Images)]

    User --> CF
    CF --> Edge
    Edge --> S3
```

### Workflow

1. User requests image
2. Edge resizes if needed
3. Optimized image cached
4. Future requests become cache hits

---

## Architecture Question 17: CI/CD Deployment Architecture

### Question

How do frontend deployments interact with CloudFront?

### Answer

```mermaid
flowchart LR
    Dev[Developer]
    GitHub[GitHub]
    Actions[GitHub Actions]
    S3[S3]
    CF[CloudFront]

    Dev --> GitHub
    GitHub --> Actions
    Actions --> S3
    S3 --> CF
```

### Deployment Strategy

| Asset | Strategy |
|---|---|
| JS/CSS | Versioned filenames |
| Images | Immutable |
| HTML | Invalidate after deployment |

### Why version assets?

It eliminates unnecessary global cache invalidations.

---

## Architecture Question 18: CloudFront + API Gateway

### Question

Should CloudFront sit in front of API Gateway?

### Answer

Yes, when global performance or caching is required.

```mermaid
flowchart LR
    User((Users))
    CF[CloudFront]
    APIGW[API Gateway]
    Lambda[Lambda]
    DB[(DynamoDB)]

    User --> CF
    CF --> APIGW
    APIGW --> Lambda
    Lambda --> DB
```

### Benefits

- Edge caching
- Custom domains
- WAF
- Lower latency

---

## Architecture Question 19: Secure Enterprise API

### Question

How would you expose internal APIs securely?

### Answer

```mermaid
flowchart TD
    User((Client))

    User --> CF[CloudFront]
    CF --> WAF[AWS WAF]
    WAF --> ALB[Private ALB]
    ALB --> API[Django APIs]
```

### Security Layers

| Layer | Protection |
|---|---|
| CloudFront | DDoS mitigation |
| WAF | OWASP filtering |
| ALB | Private networking |
| API | Authentication & authorization |

### Interview Insight

Security should be layered rather than relying on a single control.

---

## Architecture Question 20: Complete Backend Platform

### Question

Design CloudFront for a modern backend platform using Django, Redis, PostgreSQL, Kafka, and Kubernetes.

### Answer

```mermaid
flowchart TD
    User((Global Users))

    User --> R53[Route 53]
    R53 --> CF[CloudFront]
    CF --> WAF[AWS WAF]
    WAF --> ALB[Application Load Balancer]
    ALB --> Ingress[Kubernetes Ingress]

    Ingress --> API[Django / FastAPI Services]

    API --> Redis[(Redis Cache)]
    API --> PG[(PostgreSQL)]
    API --> Kafka[(Kafka)]

    Kafka --> Workers[Background Workers]
```

### Responsibilities

| Component | Purpose |
|---|---|
| Route 53 | Global DNS |
| CloudFront | CDN & TLS |
| WAF | Security |
| ALB | Load balancing |
| Kubernetes | Compute platform |
| Redis | Low-latency caching |
| PostgreSQL | Persistent storage |
| Kafka | Event streaming |

### Scalability Strategy

- CloudFront absorbs read traffic.
- Redis reduces database pressure.
- Kubernetes scales application pods.
- Kafka decouples asynchronous workloads.
- PostgreSQL scales independently.

This architecture separates concerns while minimizing latency and protecting the origin.

---

## Common Architecture Mistakes

| Mistake | Why it's Wrong | Better Design |
|---|---|---|
| Caching authenticated APIs | Data leakage risk | Cache only public resources |
| Making S3 public | Origin bypass | Use Origin Access Control |
| One cache policy for everything | Poor cache efficiency | Separate policies per workload |
| Sending every request to origin | Higher latency | Cache aggressively where safe |
| Putting Kafka behind CloudFront | Different protocol and purpose | Keep Kafka internal |
| Using CloudFront for databases | Unsupported architecture | CloudFront serves HTTP/S only |
| Invalidating all assets every deployment | Expensive and slow | Use versioned assets |
| Mixing static and dynamic origins | Operational coupling | Separate origins and behaviors |

---

## Senior Interview Framework

When answering CloudFront architecture questions, structure your response in this order:

1. **Identify the workload** (static site, API, media, SaaS, microservices).
2. **Separate static and dynamic traffic** with different origins and cache policies.
3. **Explain the request flow** from DNS to backend services.
4. **Define security boundaries** using WAF, private origins, and signed access.
5. **Discuss scalability and failure handling** including caching, autoscaling, and regional failover.

This structure demonstrates architectural thinking rather than service memorization.

## Key Takeaways

- **CloudFront belongs at the edge of distributed architectures, accelerating static assets, cacheable APIs, and media while protecting backend origins.**
- **Strong designs separate workloads into independent origins and behaviors, each with its own cache, security, and routing policy.**
- **CloudFront complements—not replaces—backend technologies like Kubernetes, Redis, PostgreSQL, Kafka, and API Gateways by optimizing HTTP delivery.**
- **Senior architecture interviews prioritize request flow, cache strategy, security boundaries, scalability, and disaster recovery over configuration details.**
- **The best CloudFront architectures minimize origin traffic, isolate services, and use layered security while remaining easy to operate and evolve.**