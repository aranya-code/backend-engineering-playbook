# Kubernetes Deployment Strategies

## Overview

A **Deployment Strategy** defines **how Kubernetes replaces an existing application version with a new one**.

Choosing the right deployment strategy is critical because it directly affects:

- Application availability
- Deployment speed
- Rollback capability
- Infrastructure cost
- Deployment risk
- User experience

Different applications require different deployment strategies. For example, an internal admin portal may tolerate a short outage, whereas an online banking system typically requires zero downtime and rapid rollback.

---

# Why Deployment Strategies Matter

Every software release introduces some level of risk.

Without a deployment strategy:

- Users may experience downtime.
- Faulty releases impact all users immediately.
- Rollbacks become difficult.
- Business-critical services may become unavailable.

Deployment strategies reduce these risks by controlling **how new versions are introduced into production**.

---

# Deployment Strategy Comparison

| Strategy | Downtime | Rollback | Infrastructure Cost | Complexity | Production Usage |
|-----------|----------|----------|---------------------|------------|------------------|
| Recreate | High | Easy | Low | Low | Rare |
| Rolling Update | None | Good | Low | Low | Very Common |
| Blue-Green | None | Excellent | High | Medium | Common |
| Canary | None | Excellent | Medium | High | Very Common |
| A/B Testing | None | Good | Medium | High | Product Teams |
| Shadow Deployment | None | Excellent | High | Very High | Large Enterprises |

---

# 1. Recreate Strategy

The existing application is completely stopped before the new version starts.

```text
Version 1

████████████

↓

Shutdown

↓

No Application Running

↓

Deploy Version 2

████████████
```

### Advantages

- Very simple
- Minimal infrastructure
- Easy rollback

### Disadvantages

- Downtime
- Poor user experience
- Not suitable for production APIs

### Best For

- Internal applications
- Development environments
- Scheduled maintenance windows

---

# 2. Rolling Update

Pods are gradually replaced with newer versions.

```text
Version 1

Pod1
Pod2
Pod3
Pod4

↓

Replace One Pod

↓

Pod1 (v2)
Pod2 (v1)
Pod3 (v1)
Pod4 (v1)

↓

Repeat Until Complete
```

### Advantages

- Zero downtime
- Low infrastructure cost
- Native Kubernetes support

### Disadvantages

- Old and new versions coexist temporarily.
- Rollback is slower than Blue-Green.

### Best For

- REST APIs
- Web applications
- Stateless microservices

---

# 3. Blue-Green Deployment

Two complete production environments exist simultaneously.

```text
               Load Balancer
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
 Blue Environment         Green Environment
   Version 1                Version 2
```

Traffic is switched instantly once the Green environment has been validated.

### Advantages

- Instant rollback
- Zero downtime
- Easy production testing

### Disadvantages

- Requires duplicate infrastructure
- Higher operational cost

### Best For

- Banking
- Healthcare
- E-commerce
- Mission-critical systems

---

# 4. Canary Deployment

A small percentage of users receive the new version first.

```text
100%

↓

95% → Version 1

5% → Version 2

↓

75% → Version 1

25% → Version 2

↓

100% → Version 2
```

Traffic is increased gradually after monitoring application health.

### Advantages

- Lowest deployment risk
- Real production validation
- Gradual rollout

### Disadvantages

- More complex
- Requires traffic management

### Best For

- Large-scale SaaS platforms
- Cloud-native applications
- High-traffic APIs

---

# 5. A/B Testing

Users are intentionally divided into different groups.

Unlike Canary Deployments, this strategy is **not intended for deployment safety**.

It is used to compare different application behavior.

```text
Users

      │

 ┌────┴────┐

 ▼         ▼

Group A   Group B

Version A Version B
```

### Example

- New homepage design
- Different pricing page
- New recommendation engine
- New search algorithm

### Advantages

- Product experimentation
- Business analytics
- User behavior analysis

### Best For

- Product teams
- Marketing
- UX optimization

---

# 6. Shadow Deployment

Production traffic is duplicated.

Only one version responds to users.

```text
Users

↓

Load Balancer

↓

Production

↓

Response Returned


            │

            ▼

Duplicate Request

↓

Shadow Version

↓

Response Ignored
```

The Shadow deployment processes real traffic without affecting users.

### Advantages

- Safest production validation
- Detects hidden production issues
- No customer impact

### Disadvantages

- Highest infrastructure cost
- Operational complexity

### Best For

- Financial systems
- Machine learning inference
- Enterprise platforms

---

# Production Evolution

Most organizations evolve through deployment strategies over time.

```text
Development

↓

Recreate

↓

Rolling Update

↓

Blue-Green

↓

Canary

↓

Progressive Delivery
```

---

# Kubernetes Support

| Strategy | Native Kubernetes | Additional Tools |
|----------|-------------------|------------------|
| Recreate | ✅ | None |
| Rolling Update | ✅ | None |
| Blue-Green | Partial | Argo Rollouts, Service Mesh |
| Canary | Partial | Argo Rollouts, Istio, Flagger |
| A/B Testing | No | Istio, Linkerd |
| Shadow Deployment | No | Istio, Envoy |

---

# Decision Guide

```text
Need Simplicity?

        │

       Yes

        │

        ▼

Rolling Update

        │

       No

        │

Need Instant Rollback?

        │

       Yes

        │

        ▼

Blue-Green

        │

Need Real User Validation?

        │

       Yes

        │

        ▼

Canary

        │

Need Product Experimentation?

        │

       Yes

        │

        ▼

A/B Testing

        │

Need Production Validation Without User Impact?

        │

       Yes

        │

        ▼

Shadow Deployment
```

---

# Real-World Examples

| Company | Common Strategy |
|----------|-----------------|
| Netflix | Canary |
| Google | Canary + Progressive Delivery |
| Amazon | Rolling Update + Canary |
| Spotify | Canary |
| GitHub | Rolling Update |
| Kubernetes Default | Rolling Update |

---

# Choosing the Right Strategy

| Scenario | Recommended Strategy |
|----------|----------------------|
| Internal Tool | Recreate |
| REST API | Rolling Update |
| Enterprise Application | Blue-Green |
| Large SaaS Platform | Canary |
| Product Experiment | A/B Testing |
| Critical Financial Platform | Shadow Deployment |

---

# Best Practices

- Use **Rolling Updates** for most stateless applications.
- Choose **Blue-Green** when instant rollback is essential.
- Use **Canary Deployments** to minimize deployment risk.
- Perform **A/B Testing** only for product experimentation.
- Use **Shadow Deployments** for validating critical systems before release.
- Always monitor application health, logs, and business metrics during deployments.
- Automate deployment pipelines with CI/CD tools.

---

## Key Takeaways

- A deployment strategy determines how new application versions are released into production.
- Kubernetes natively supports **Recreate** and **Rolling Update**, with **Rolling Update** being the default.
- **Blue-Green** and **Canary** deployments reduce deployment risk and improve rollback capabilities.
- **A/B Testing** focuses on product experimentation, while **Shadow Deployments** validate new versions using mirrored production traffic.
- Selecting the appropriate deployment strategy depends on application criticality, business requirements, acceptable risk, and infrastructure capabilities.