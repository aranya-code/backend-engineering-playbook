# Deployment Strategies

## Overview

Deploying a new version of an application without affecting users is one of the primary goals of Kubernetes. A **Deployment Strategy** defines how Kubernetes replaces old application instances with new ones during an update.

Choosing the right deployment strategy helps minimize downtime, reduce deployment risks, and ensure a smooth user experience.

Kubernetes supports **Rolling Updates** natively, while other strategies such as **Recreate**, **Blue-Green**, and **Canary** are implemented using additional configurations or external tools.

---

## Why Deployment Strategies Matter

A good deployment strategy helps:

- Minimize application downtime
- Reduce deployment failures
- Perform safe rollbacks
- Validate new releases before full deployment
- Improve application availability

---

## Common Deployment Strategies

| Strategy | Downtime | Risk | Native Support |
|----------|----------|------|----------------|
| Recreate | Yes | High | ✅ |
| Rolling Update | No | Low | ✅ |
| Blue-Green | No | Very Low | Partial |
| Canary | No | Very Low | Partial |

---

# Recreate Strategy

## Overview

The **Recreate** strategy completely shuts down the existing version before deploying the new version.

```text
Old Pods Running

↓

Terminate All Old Pods

↓

Create New Pods
```

---

## Advantages

- Very simple deployment process
- No version compatibility issues
- Easy to understand

---

## Disadvantages

- Application downtime
- Unsuitable for highly available systems

---

## Use Cases

- Internal tools
- Development environments
- Applications where brief downtime is acceptable

---

## Example

```yaml
strategy:
  type: Recreate
```

---

# Rolling Update Strategy

## Overview

A **Rolling Update** gradually replaces old Pods with new Pods.

Instead of replacing all Pods at once, Kubernetes updates them in batches.

This is the **default deployment strategy**.

```text
Old Pods

● ● ● ●

↓

● ● ● ○

↓

● ● ○ ○

↓

● ○ ○ ○

↓

○ ○ ○ ○

(New Version)
```

---

## Advantages

- Zero or minimal downtime
- Safe deployment
- Easy rollback
- Default Kubernetes behavior

---

## Disadvantages

- Old and new versions run simultaneously
- Applications must support backward compatibility

---

## Example

```yaml
strategy:
  type: RollingUpdate
```

---

## Rolling Update Parameters

### maxUnavailable

Maximum number of Pods that may be unavailable during the update.

Example:

```yaml
maxUnavailable: 1
```

---

### maxSurge

Maximum number of additional Pods created during the update.

Example:

```yaml
maxSurge: 1
```

---

## Example Configuration

```yaml
strategy:
  type: RollingUpdate

  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 1
```

---

# Blue-Green Deployment

## Overview

A **Blue-Green Deployment** maintains two identical production environments.

```text
Blue Environment
(Current Version)

Green Environment
(New Version)
```

Initially:

```text
Traffic

↓

Blue
```

After validation:

```text
Traffic

↓

Green
```

The old environment remains available for rollback.

---

## Advantages

- Near-zero downtime
- Instant rollback
- Safe production deployments

---

## Disadvantages

- Requires duplicate infrastructure
- Higher resource cost

---

## Common Use Cases

- Financial systems
- Banking applications
- Healthcare platforms
- Mission-critical APIs

---

# Canary Deployment

## Overview

A **Canary Deployment** releases the new version to a small percentage of users before rolling it out to everyone.

Example:

```text
90%

↓

Old Version

10%

↓

New Version
```

If everything works correctly:

```text
50%

↓

New Version

↓

100%
```

---

## Advantages

- Lower deployment risk
- Easy validation
- Real user testing
- Reduced production impact

---

## Disadvantages

- More complex
- Requires traffic routing
- Often uses Ingress or Service Mesh

---

## Common Use Cases

- Large-scale SaaS platforms
- E-commerce applications
- High-traffic APIs

---

# Strategy Comparison

| Strategy | Downtime | Rollback | Complexity |
|----------|----------|----------|------------|
| Recreate | High | Easy | Low |
| Rolling Update | None | Easy | Low |
| Blue-Green | None | Instant | Medium |
| Canary | None | Gradual | High |

---

# Rollback

If a deployment fails:

```bash
kubectl rollout undo deployment backend-api
```

Check rollout history:

```bash
kubectl rollout history deployment backend-api
```

View rollout status:

```bash
kubectl rollout status deployment backend-api
```

---

# Deployment Workflow

```text
Developer

↓

Build Image

↓

Push Image

↓

Update Deployment

↓

Rolling Update

↓

Health Checks

↓

Application Available
```

---

# Best Practices

- Use Rolling Updates for most applications.
- Configure Readiness Probes before enabling rolling updates.
- Monitor application metrics during deployments.
- Keep deployments small and incremental.
- Test rollback procedures regularly.
- Use Blue-Green or Canary deployments for critical production systems.

---

# Common Problems

| Problem | Cause |
|----------|-------|
| Downtime | Recreate strategy |
| Failed rollout | Application startup failure |
| Stuck deployment | Readiness Probe failures |
| Mixed versions | Rolling update in progress |
| Slow deployment | Conservative rollout settings |

---

# Interview Tips

- **Rolling Update** is Kubernetes' default deployment strategy.
- **Recreate** deletes old Pods before creating new ones, causing downtime.
- **Blue-Green** uses two production environments and enables instant rollback.
- **Canary** gradually exposes the new version to a subset of users before full rollout.
- `maxSurge` controls extra Pods created during an update.
- `maxUnavailable` controls how many Pods may be unavailable during an update.
- `kubectl rollout undo` reverts a Deployment to its previous version.

---

## Key Takeaways

- Deployment strategies determine how application updates are rolled out in Kubernetes.
- Rolling Updates provide zero or minimal downtime and are the default strategy for most workloads.
- Recreate deployments are simple but introduce downtime.
- Blue-Green and Canary deployments reduce deployment risk and improve production safety.
- Rollback capabilities and health checks are essential components of a reliable deployment process.
- Selecting the appropriate deployment strategy depends on application requirements, availability goals, and acceptable deployment risk.