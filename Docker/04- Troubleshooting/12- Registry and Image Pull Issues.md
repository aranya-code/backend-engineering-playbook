# Registry and Image Pull Issues

## Overview

Docker registries are repositories used to store and distribute Docker images. Public registries like Docker Hub and private registries such as Amazon ECR, Azure Container Registry (ACR), Google Artifact Registry (GAR), GitHub Container Registry (GHCR), and Harbor enable teams to share container images securely.

Image pull failures are commonly caused by authentication issues, incorrect image names or tags, network connectivity problems, rate limiting, certificate errors, and registry availability.

This guide covers the most common registry and image pull issues, explains how to diagnose them, and provides practical solutions and preventive best practices.

---

## Common Registry and Image Pull Issues

| Issue | Severity |
|--------|----------|
| Image not found | High |
| Access denied | High |
| Authentication failure | High |
| Docker Hub rate limit exceeded | Medium |
| Network timeout | Medium |
| TLS/SSL certificate errors | High |
| Private registry unreachable | High |
| Invalid image tag | Medium |
| Manifest unknown | Medium |
| Slow image pulls | Low |

---

# Issue 1: Image Not Found

## Symptoms

```text
pull access denied for my-image, repository does not exist
```

or

```text
repository does not exist
```

---

## Possible Causes

- Incorrect image name.
- Repository does not exist.
- Typographical error.
- Wrong registry.

---

## How to Diagnose

Verify the image name:

```bash
docker pull nginx
```

Inspect the Dockerfile:

```dockerfile
FROM my-image
```

---

## Solutions

Use the correct repository name.

Verify the image exists in the registry.

Specify the registry if necessary.

Example:

```bash
docker pull docker.io/library/nginx:latest
```

---

## Prevention

- Copy image names directly from the registry.
- Use official images whenever possible.

---

# Issue 2: Access Denied

## Symptoms

```text
pull access denied
```

or

```text
requested access to the resource is denied
```

---

## Possible Causes

- Private repository.
- Insufficient permissions.
- Wrong Docker account.

---

## How to Diagnose

Check authentication:

```bash
docker login
```

Verify repository permissions.

---

## Solutions

Authenticate with the correct account:

```bash
docker login
```

Ensure your account has permission to access the repository.

---

## Prevention

Grant least-privilege access to private repositories.

---

# Issue 3: Authentication Failure

## Symptoms

```text
unauthorized: authentication required
```

---

## Possible Causes

- Incorrect credentials.
- Expired access token.
- Registry authentication expired.

---

## How to Diagnose

Logout:

```bash
docker logout
```

Login again:

```bash
docker login
```

---

## Solutions

Re-authenticate.

Use updated credentials.

For cloud registries, refresh authentication tokens.

---

## Prevention

Rotate credentials regularly.

Use short-lived authentication tokens.

---

# Issue 4: Docker Hub Rate Limit Exceeded

## Symptoms

```text
toomanyrequests
```

---

## Possible Causes

- Too many anonymous pulls.
- CI/CD pipelines pulling images frequently.

---

## How to Diagnose

Review the error message.

Check Docker Hub usage.

---

## Solutions

Authenticate before pulling:

```bash
docker login
```

Mirror frequently used images locally.

Use a private registry for production.

---

## Prevention

Avoid anonymous image pulls.

Cache images in CI/CD pipelines.

---

# Issue 5: Network Timeout

## Symptoms

```text
context deadline exceeded
```

or

```text
i/o timeout
```

---

## Possible Causes

- Internet connectivity problems.
- Corporate proxy.
- DNS failure.
- Firewall restrictions.

---

## How to Diagnose

Test connectivity:

```bash
ping registry-1.docker.io
```

Test HTTPS:

```bash
curl https://registry-1.docker.io
```

---

## Solutions

Verify internet connectivity.

Configure proxy settings if required.

Restart Docker.

---

## Prevention

Use reliable DNS servers.

Monitor network connectivity.

---

# Issue 6: TLS or SSL Certificate Errors

## Symptoms

```text
x509: certificate signed by unknown authority
```

---

## Possible Causes

- Self-signed certificates.
- Invalid CA configuration.
- Expired certificates.

---

## How to Diagnose

Inspect certificate details.

Review Docker daemon logs.

---

## Solutions

Install trusted CA certificates.

Update expired certificates.

Configure Docker to trust the registry.

---

## Prevention

Use certificates issued by trusted Certificate Authorities.

Monitor certificate expiration dates.

---

# Issue 7: Private Registry Unreachable

## Symptoms

```text
connection refused
```

or

```text
no route to host
```

---

## Possible Causes

- Registry offline.
- Firewall blocking access.
- DNS issues.

---

## How to Diagnose

Ping registry server.

Verify registry service.

Test using:

```bash
curl https://registry.example.com/v2/
```

---

## Solutions

Restart the registry.

Verify firewall rules.

Restore network connectivity.

---

## Prevention

Monitor registry availability.

Deploy highly available registry infrastructure.

---

# Issue 8: Invalid Image Tag

## Symptoms

```text
manifest unknown
```

---

## Possible Causes

- Incorrect tag.
- Image version removed.
- Typographical error.

---

## How to Diagnose

Attempt to pull another tag:

```bash
docker pull nginx:latest
```

---

## Solutions

Use an existing tag.

Avoid relying on unpublished versions.

---

## Prevention

Pin production deployments to tested image tags.

---

# Issue 9: Manifest Unknown

## Symptoms

```text
manifest unknown
```

---

## Possible Causes

- Tag does not exist.
- Incorrect image architecture.
- Image deleted.

---

## How to Diagnose

Inspect repository tags.

Verify architecture compatibility.

---

## Solutions

Pull a valid tag.

Verify platform compatibility:

```bash
docker pull --platform linux/amd64 nginx
```

---

## Prevention

Maintain consistent image tagging.

Avoid deleting production image tags.

---

# Issue 10: Slow Image Pulls

## Symptoms

Image downloads are significantly slower than expected.

---

## Possible Causes

- Large image size.
- Slow network.
- Registry congestion.
- Geographically distant registry.

---

## How to Diagnose

Monitor pull progress:

```bash
docker pull nginx
```

Check image size:

```bash
docker images
```

---

## Solutions

Use smaller base images.

Mirror images closer to deployment environments.

Optimize image size using multi-stage builds.

---

## Prevention

Keep images lightweight.

Use local image caches where appropriate.

---

# Diagnostic Commands Cheat Sheet

| Purpose | Command |
|---------|---------|
| Login to registry | `docker login` |
| Logout | `docker logout` |
| Pull image | `docker pull` |
| Push image | `docker push` |
| List images | `docker images` |
| Inspect image | `docker image inspect` |
| View image history | `docker history` |
| Check Docker configuration | `docker info` |
| Test registry connectivity | `curl https://registry.example.com/v2/` |
| Check network connectivity | `ping registry-1.docker.io` |

---

# Best Practices

- Authenticate before pulling from public or private registries.
- Use official or trusted container images.
- Pin image versions instead of relying on `latest` for production deployments.
- Enable image caching in CI/CD pipelines.
- Mirror frequently used images in private registries.
- Regularly scan images for vulnerabilities.
- Monitor registry availability and certificate expiration.
- Keep Docker credentials secure and rotate access tokens periodically.

---

# Related Topics

- Docker Images
- Docker Registries
- Docker CLI
- Image Build Failures
- Docker Compose
- Docker Swarm
- Permission and Security Issues

---

## Key Takeaways

- Most registry and image pull failures are caused by authentication issues, incorrect image names or tags, network problems, or registry availability.
- `docker login`, `docker pull`, and `docker image inspect` are the primary tools for diagnosing registry-related issues.
- Always use trusted registries, authenticated access, and pinned image versions for production deployments.
- Private registries improve reliability, security, and deployment performance in enterprise environments.
- Regular monitoring, vulnerability scanning, and image caching help ensure fast, secure, and reliable image distribution.