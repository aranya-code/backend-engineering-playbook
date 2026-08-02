# Image Pull Problems

## Overview

Every Kubernetes application depends on container images. Before a Pod can start, Kubernetes must successfully download its container image from a container registry.

If Kubernetes cannot pull the image, the Pod will never start. Image-related problems are among the most common deployment failures in Kubernetes and are usually caused by incorrect image names, invalid tags, authentication failures, or registry connectivity issues.

This guide explains the most common image pull errors, how to diagnose them, and how to resolve them.

---

# Why Image Pull Problems Occur

Image pull failures typically happen because of:

- Incorrect image name
- Invalid image tag
- Private registry authentication failure
- Registry unavailable
- Missing imagePullSecrets
- Network connectivity issues
- Image deleted from registry

---

# ErrImagePull

## Symptoms

```text
STATUS

ErrImagePull
```

The container runtime attempted to download the image but failed.

---

## Common Causes

- Wrong image name
- Wrong image tag
- Image does not exist
- Registry unavailable
- Authentication failure

---

## Investigation

Describe the Pod:

```bash
kubectl describe pod <pod-name>
```

Example:

```text
Failed to pull image
```

---

## Resolution

- Verify image name
- Verify image tag
- Push missing image
- Verify registry connectivity
- Configure authentication

---

# ImagePullBackOff

## Symptoms

```text
STATUS

ImagePullBackOff
```

Kubernetes repeatedly retries pulling the image after previous failures.

---

## Workflow

```text
Image Pull

↓

Failed

↓

Retry

↓

Retry

↓

ImagePullBackOff
```

---

## Investigation

```bash
kubectl describe pod <pod-name>
```

Review Events.

---

## Resolution

Resolve the original image pull problem.

ImagePullBackOff is not the root cause—it is the retry state.

---

# Invalid Image Name

## Symptoms

```text
Failed to pull image
```

---

## Example

Incorrect:

```text
ngnix:latest
```

Correct:

```text
nginx:latest
```

---

## Investigation

Review the Deployment:

```bash
kubectl describe deployment
```

---

## Resolution

Correct the image reference.

---

# Image Tag Not Found

## Symptoms

```text
manifest unknown
```

or

```text
tag not found
```

---

## Possible Causes

- Incorrect tag
- Tag deleted
- CI/CD published a different version

---

## Investigation

Verify the image tag in your container registry.

---

## Resolution

Update the Deployment with a valid image tag.

Example:

```yaml
image: backend-api:v1.2.0
```

---

# Private Registry Authentication Failure

## Symptoms

```text
Unauthorized

Authentication required
```

---

## Possible Causes

- Missing imagePullSecret
- Expired credentials
- Wrong registry username/password

---

## Investigation

Describe the Pod:

```bash
kubectl describe pod <pod-name>
```

List Secrets:

```bash
kubectl get secrets
```

---

## Resolution

Create an image pull secret:

```bash
kubectl create secret docker-registry registry-secret \
--docker-server=<registry-url> \
--docker-username=<username> \
--docker-password=<password>
```

Reference it:

```yaml
imagePullSecrets:
- name: registry-secret
```

---

# Registry Unreachable

## Symptoms

```text
connection refused

timeout
```

---

## Possible Causes

- Registry outage
- Network issue
- DNS failure
- Firewall

---

## Investigation

Test registry access:

```bash
kubectl exec -it <pod-name> -- sh
```

Example:

```bash
wget https://registry.example.com
```

---

## Resolution

- Verify network connectivity
- Verify DNS
- Verify firewall rules
- Check registry health

---

# Missing imagePullSecrets

## Symptoms

Pods cannot download private images.

---

## Investigation

Describe Pod:

```bash
kubectl describe pod
```

Check Deployment:

```bash
kubectl get deployment -o yaml
```

---

## Resolution

Ensure:

```yaml
imagePullSecrets:
- name: registry-secret
```

is configured.

---

# Wrong Image Repository

## Symptoms

```text
repository not found
```

---

## Example

Incorrect:

```text
company/backend
```

Correct:

```text
company/backend-api
```

---

## Investigation

Verify repository name in your registry.

---

## Resolution

Update Deployment with the correct repository.

---

# Image Exists Locally But Not in Registry

## Symptoms

Application works locally.

Fails in Kubernetes.

---

## Possible Causes

Image was built locally but never pushed.

---

## Investigation

Verify:

```text
docker images
```

Check registry.

---

## Resolution

Push the image:

```bash
docker push company/backend-api:v1
```

Redeploy the application.

---

# Wrong Image Architecture

## Symptoms

Container starts then immediately exits.

Possible message:

```text
exec format error
```

---

## Possible Causes

- ARM image on AMD64 node
- AMD64 image on ARM node

---

## Investigation

Check image architecture.

Check node architecture:

```bash
kubectl get nodes -o wide
```

---

## Resolution

Build a multi-platform image.

Example:

```bash
docker buildx build \
--platform linux/amd64,linux/arm64
```

---

# CI/CD Published Wrong Image

## Symptoms

Deployment succeeds.

Application behaves unexpectedly.

---

## Investigation

Verify:

```text
Current image

↓

Deployment YAML

↓

Registry

↓

CI/CD Pipeline
```

---

## Resolution

- Verify pipeline output
- Pin image versions
- Avoid latest tag

---

# Latest Tag Issues

## Symptoms

Different environments run different versions.

---

## Problem

Avoid:

```yaml
image: backend-api:latest
```

---

## Recommended

```yaml
image: backend-api:v1.5.3
```

Versioned tags provide reproducible deployments.

---

# Image Pull Troubleshooting Workflow

```text
Image Pull Failed
        │
        ▼
Describe Pod
        │
        ▼
Review Events
        │
        ▼
Verify Image Name
        │
        ▼
Verify Image Tag
        │
        ▼
Check Registry Access
        │
        ▼
Check Authentication
        │
        ▼
Verify imagePullSecrets
        │
        ▼
Redeploy
```

---

# Useful Commands

```bash
kubectl describe pod <pod-name>

kubectl get events

kubectl get deployment

kubectl get secrets

kubectl describe deployment

kubectl rollout restart deployment <deployment-name>
```

---

# Best Practices

- Never use the `latest` tag in production.
- Use semantic versioning for container images.
- Store registry credentials as Kubernetes Secrets.
- Regularly verify image availability.
- Use immutable image tags.
- Test image pulls before production deployments.
- Automate image publishing with CI/CD.

---

# Interview Tips

- **ErrImagePull** is the initial image download failure.
- **ImagePullBackOff** is Kubernetes repeatedly retrying after the initial failure.
- Always check Pod Events using `kubectl describe pod`.
- Use `imagePullSecrets` for private registries.
- Avoid using `latest` in production because it makes deployments unpredictable.

---

## Key Takeaways

- Image pull failures prevent Pods from starting and are among the most common Kubernetes deployment issues.
- `ErrImagePull` indicates an initial image retrieval failure, while `ImagePullBackOff` represents Kubernetes' retry mechanism.
- Incorrect image names, invalid tags, authentication failures, and registry connectivity issues are the most frequent causes.
- Using immutable image tags, proper registry authentication, and automated CI/CD pipelines significantly reduces image-related deployment problems.