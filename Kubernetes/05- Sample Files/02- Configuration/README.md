# Kubernetes Configuration Examples

## Overview

The **Configuration** folder demonstrates how Kubernetes manages application configuration using **ConfigMaps** and **Secrets**.

One of the core principles of cloud-native applications is **externalizing configuration**, which means keeping configuration outside the application code and container image. Kubernetes provides ConfigMaps for non-sensitive configuration and Secrets for sensitive information such as passwords, API keys, and certificates.

These examples show how to create ConfigMaps and Secrets, inject them into Deployments, and follow production-ready configuration management practices.

---

# Why This Section Matters

Hardcoding configuration inside an application makes deployments difficult and inflexible.

Kubernetes allows the same container image to be deployed across multiple environments by changing only the external configuration.

This approach provides:

- Environment-specific configuration
- Secure credential management
- Easier application deployments
- Better DevOps practices
- Improved security
- Simplified maintenance

---

# Files in This Folder

| File | Description |
|------|-------------|
| **01- ConfigMap.yaml** | Creates a ConfigMap containing non-sensitive application configuration. |
| **02- Secret.yaml** | Creates a Secret containing sensitive information such as passwords and API keys. |
| **03- Deployment-With-ConfigMap.yaml** | Deploys an application that loads configuration from a ConfigMap. |
| **04- Deployment-With-Secret.yaml** | Deploys an application that securely consumes Kubernetes Secrets. |
| **05- Deployment-With-ConfigMap-Secret.yaml** | Demonstrates a production-ready Deployment using both ConfigMaps and Secrets together. |

---

# Learning Path

Study the examples in the following order.

```text
ConfigMap
     │
     ▼
Secret
     │
     ▼
Deployment + ConfigMap
     │
     ▼
Deployment + Secret
     │
     ▼
Deployment + ConfigMap + Secret
```

---

# Configuration Architecture

```text
                   Kubernetes
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
   ConfigMap                      Secret
        │                             │
        │                             │
        └──────────────┬──────────────┘
                       ▼
                 Deployment
                       │
                       ▼
                  ReplicaSet
                       │
                       ▼
                      Pods
                       │
                       ▼
                 Application
```

---

# ConfigMap vs Secret

| Feature | ConfigMap | Secret |
|----------|-----------|---------|
| Stores | Non-sensitive configuration | Sensitive configuration |
| Examples | Hostnames, Ports, Feature Flags | Passwords, API Keys, Tokens |
| Encoding | Plain text | Base64 encoded |
| Production Recommendation | Yes | Yes (prefer external Secret Managers for production) |

---

# What You'll Learn

After completing this section, you'll understand how to:

- Create ConfigMaps
- Create Secrets
- Inject configuration into Pods
- Inject sensitive credentials securely
- Use environment variables
- Separate configuration from code
- Follow Kubernetes configuration best practices

---

# Typical Production Pattern

A production backend application typically separates configuration like this:

### ConfigMap

```text
Application Name

Environment

Hostnames

Ports

Log Levels

Feature Flags

Cache Settings
```

### Secret

```text
Database Password

JWT Secret

OAuth Tokens

API Keys

Redis Password

Certificates
```

---

# Recommended Workflow

For each example:

1. Read the comments in the YAML file.
2. Create the resource.
3. Verify the resource.
4. Inspect the created ConfigMap or Secret.
5. Deploy the example application.
6. Verify that the environment variables are available.
7. Modify a configuration value.
8. Restart the Deployment and observe the changes.

---

# Frequently Used Commands

Create a ConfigMap

```bash
kubectl apply -f 01-ConfigMap.yaml
```

Create a Secret

```bash
kubectl apply -f 02-Secret.yaml
```

View ConfigMaps

```bash
kubectl get configmaps
```

View Secrets

```bash
kubectl get secrets
```

Describe a ConfigMap

```bash
kubectl describe configmap backend-config
```

Describe a Secret

```bash
kubectl describe secret backend-secret
```

View Pod Environment Variables

```bash
kubectl exec -it <pod-name> -- env
```

Restart a Deployment

```bash
kubectl rollout restart deployment backend-api
```

---

# Navigation

| Step | File | Purpose |
|------|------|---------|
| 01 | **01- ConfigMap.yaml** | Learn how to store application configuration. |
| 02 | **02- Secret.yaml** | Learn how to securely store sensitive information. |
| 03 | **03- Deployment-With-ConfigMap.yaml** | Inject configuration into a Deployment. |
| 04 | **04- Deployment-With-Secret.yaml** | Inject Secrets into a Deployment securely. |
| 05 | **05- Deployment-With-ConfigMap-Secret.yaml** | Build a production-ready Deployment using both ConfigMaps and Secrets. |

---

# Best Practices

- Store only non-sensitive values in ConfigMaps.
- Store credentials exclusively in Secrets.
- Never hardcode passwords inside container images.
- Use meaningful names for ConfigMaps and Secrets.
- Keep environment-specific configuration outside the application code.
- Rotate Secrets regularly.
- Enable Kubernetes Encryption at Rest.
- Use external Secret Managers for production environments.
- Restart Deployments after updating ConfigMaps or Secrets if the application reads configuration only during startup.

---

## Key Takeaways

- ConfigMaps and Secrets enable externalized configuration, making applications portable across environments.
- ConfigMaps should be used for non-sensitive settings, while Secrets are intended for confidential data.
- Production Kubernetes applications commonly consume both ConfigMaps and Secrets within the same Deployment.
- Separating configuration from application code improves security, maintainability, and deployment flexibility.