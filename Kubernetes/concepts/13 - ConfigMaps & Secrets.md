# Introduction

Applications require configuration to run.

Examples include:

- Database Host
- Database Port
- API URLs
- Log Level
- Feature Flags
- Passwords
- API Keys
- JWT Secrets

Hardcoding these values inside the application code is a bad practice.

Kubernetes provides two resources to manage configuration:

- **ConfigMap** → Non-sensitive configuration
- **Secret** → Sensitive configuration

---

# Why Not Hardcode Configuration?

Suppose your application contains

```python
DATABASE_HOST = "localhost"
DATABASE_PASSWORD = "admin123"
```

Problems

- Difficult to change
- Not environment-specific
- Credentials exposed
- Requires rebuilding the application

Instead,

```
Application

↓

ConfigMap

↓

Secret
```

The application reads configuration at runtime.

---

# ConfigMap

A **ConfigMap** stores **non-sensitive configuration data** as key-value pairs.

Examples

- API URL
- Database Host
- Port Numbers
- Environment Name
- Log Level
- Feature Flags

Think of ConfigMap as the application's **configuration file**.

---

# ConfigMap Architecture

```
Application

↓

ConfigMap

↓

Configuration Data
```

---

# ConfigMap Example

```yaml
apiVersion: v1
kind: ConfigMap

metadata:
  name: app-config

data:
  APP_NAME: Backend API
  LOG_LEVEL: INFO
  DATABASE_HOST: mysql-service
  DATABASE_PORT: "3306"
```

---

# Viewing ConfigMaps

List ConfigMaps

```bash
kubectl get configmaps
```

Short form

```bash
kubectl get cm
```

Describe ConfigMap

```bash
kubectl describe configmap app-config
```

---

# Creating ConfigMap

Using YAML

```bash
kubectl apply -f configmap.yaml
```

Using CLI

```bash
kubectl create configmap app-config \
--from-literal=LOG_LEVEL=INFO
```

---

# Using ConfigMap as Environment Variables

```yaml
env:

- name: LOG_LEVEL

  valueFrom:

    configMapKeyRef:

      name: app-config

      key: LOG_LEVEL
```

Application

```
LOG_LEVEL

↓

INFO
```

---

# Using ConfigMap as a Volume

Instead of environment variables,

ConfigMaps can be mounted as files.

```
Pod

↓

ConfigMap

↓

Mounted File
```

Example

```yaml
volumes:

- name: config-volume

  configMap:

    name: app-config
```

---

# Advantages of ConfigMaps

- Decouple configuration from code
- Easy updates
- Reusable
- Environment-specific
- Kubernetes-native

---

# What is a Secret?

A **Secret** stores sensitive information.

Examples

- Passwords
- API Keys
- JWT Secret
- OAuth Tokens
- SSH Keys
- Certificates

Never store sensitive information in a ConfigMap.

---

# Secret Architecture

```
Application

↓

Secret

↓

Sensitive Data
```

---

# Secret Example

```yaml
apiVersion: v1

kind: Secret

metadata:
  name: db-secret

type: Opaque

data:

  username: YWRtaW4=

  password: cGFzc3dvcmQ=
```

The values are Base64 encoded.

---

# Why Base64?

Secrets are Base64 encoded for data formatting and transport.

**Important: Base64 encoding is *not encryption*.**

To protect Secrets in production:

- Enable encryption at rest in `etcd`
- Use RBAC
- Consider external secret managers

---

# Secret Types

Kubernetes supports multiple Secret types.

| Type | Purpose |
|------|----------|
| Opaque | Generic secret |
| kubernetes.io/dockerconfigjson | Docker Registry Credentials |
| kubernetes.io/tls | TLS Certificates |
| kubernetes.io/basic-auth | Username & Password |
| kubernetes.io/ssh-auth | SSH Keys |
| kubernetes.io/service-account-token | Service Account Token |

---

# Creating a Secret

Using CLI

```bash
kubectl create secret generic db-secret \
--from-literal=username=admin \
--from-literal=password=admin123
```

---

Using YAML

```yaml
apiVersion: v1

kind: Secret

metadata:
  name: db-secret

type: Opaque

stringData:

  username: admin

  password: admin123
```

> **Tip:** `stringData` is easier to use than manually Base64 encoding values. Kubernetes encodes them automatically.

---

# Viewing Secrets

List Secrets

```bash
kubectl get secrets
```

Describe Secret

```bash
kubectl describe secret db-secret
```

View YAML

```bash
kubectl get secret db-secret -o yaml
```

---

# Using Secrets as Environment Variables

```yaml
env:

- name: DB_PASSWORD

  valueFrom:

    secretKeyRef:

      name: db-secret

      key: password
```

---

# Using Secrets as Volumes

Secrets can also be mounted as files.

```
Pod

↓

Secret

↓

Volume

↓

Certificate
```

Example

```yaml
volumes:

- name: secret-volume

  secret:

    secretName: db-secret
```

---

# ConfigMap vs Secret

| ConfigMap | Secret |
|------------|---------|
| Non-sensitive data | Sensitive data |
| Plain text | Base64 encoded |
| Stores configuration | Stores credentials |
| API URLs | Passwords |
| Feature Flags | Tokens |
| Database Host | API Keys |

---

# Configuration Flow

```
Developer

↓

ConfigMap

↓

Pod

↓

Application
```

Sensitive data

```
Developer

↓

Secret

↓

Pod

↓

Application
```

---

# Real-World Example

A Django application requires:

Configuration

```
DEBUG

DATABASE_HOST

DATABASE_PORT

LOG_LEVEL
```

Store these in

```
ConfigMap
```

Sensitive information

```
DATABASE_PASSWORD

SECRET_KEY

JWT_SECRET

AWS_ACCESS_KEY

AWS_SECRET_KEY
```

Store these in

```
Secret
```

---

# ConfigMap + Secret Together

```
Deployment

↓

Pod

├── ConfigMap

└── Secret

↓

Application
```

The application receives both non-sensitive configuration and sensitive credentials.

---

# Production Best Practices

✔ Never hardcode passwords.

✔ Use ConfigMaps for configuration.

✔ Use Secrets for credentials.

✔ Prefer `stringData` when writing Secret manifests.

✔ Restrict Secret access with RBAC.

✔ Enable encryption at rest for Secrets in `etcd`.

✔ Rotate credentials regularly.

✔ Use external secret managers (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault) for production workloads.

---

# Useful Commands

Create ConfigMap

```bash
kubectl create configmap app-config \
--from-literal=APP_ENV=production
```

Create Secret

```bash
kubectl create secret generic db-secret \
--from-literal=password=admin123
```

List ConfigMaps

```bash
kubectl get cm
```

List Secrets

```bash
kubectl get secrets
```

Describe ConfigMap

```bash
kubectl describe configmap app-config
```

Describe Secret

```bash
kubectl describe secret db-secret
```

Delete ConfigMap

```bash
kubectl delete configmap app-config
```

Delete Secret

```bash
kubectl delete secret db-secret
```

---

# Common Mistakes

❌ Storing passwords in ConfigMaps

❌ Hardcoding credentials in source code

❌ Committing Secret YAML files with real credentials to Git

❌ Assuming Base64 encoding is encryption

❌ Giving every Pod access to every Secret

---

# Interview Questions

## What is a ConfigMap?

A ConfigMap stores non-sensitive configuration data for Kubernetes applications as key-value pairs.

---

## What is a Secret?

A Secret stores sensitive information such as passwords, API keys, tokens, and certificates.

---

## Difference between ConfigMap and Secret?

ConfigMaps store non-sensitive configuration.

Secrets store sensitive information and are Base64 encoded.

---

## Is a Kubernetes Secret encrypted?

Not by default.

Secrets are Base64 encoded. To secure them, enable encryption at rest and use RBAC or external secret management solutions.

---

## How can ConfigMaps and Secrets be consumed by Pods?

They can be injected as:

- Environment variables
- Mounted files (Volumes)

---

## Why should configuration be separated from application code?

Separating configuration from code improves portability, security, and makes it easier to deploy the same application across development, testing, and production environments.

---

# Key Takeaways

- ConfigMaps store non-sensitive configuration.
- Secrets store sensitive data such as passwords and API keys.
- Pods can consume ConfigMaps and Secrets as environment variables or mounted volumes.
- Never hardcode configuration or credentials in application code.
- Base64 encoding is **not** encryption.
- Protect Secrets using RBAC, encryption at rest, and external secret management in production.
- ConfigMaps and Secrets help keep applications portable, secure, and environment-independent.