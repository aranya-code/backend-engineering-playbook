# 13 - Production CI/CD Pipeline

A production-oriented CI/CD skeleton combining testing, container image publishing,
concurrency control, immutable image tags, and a separately approved deployment.

## Architecture

```text
Pull Request
    |
    v
Tests
    |
main ----> Build/Publish Image ----> Deployment
                                  |
                           Production Environment
```

## Concepts

- CI vs CD separation
- Build once, deploy many
- Concurrency
- GHCR
- Immutable SHA tags
- Environment protection
- Manual deployment
- Rollback-ready artifact identity
