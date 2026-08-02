# What is Helm?

Helm is the **package manager for Kubernetes**.

It helps you package, install, upgrade, and manage Kubernetes applications using reusable templates.

Think of Helm as:

- **apt** for Ubuntu
- **yum** for RHEL
- **npm** for Node.js
- **pip** for Python

But for **Kubernetes**.

---

# Why Helm?

Suppose your application consists of:

- Deployment
- Service
- ConfigMap
- Secret
- Ingress
- Persistent Volume
- Horizontal Pod Autoscaler

Without Helm

```
deployment.yaml
service.yaml
configmap.yaml
secret.yaml
ingress.yaml
volume.yaml

kubectl apply -f ...
kubectl apply -f ...
kubectl apply -f ...
...
```

Managing many YAML files quickly becomes difficult.

---

With Helm

```
helm install my-app mychart/
```

Everything is deployed together.

---

# Problems Helm Solves

Without Helm

- Hundreds of YAML files
- Duplicate configurations
- Manual updates
- Difficult versioning
- Hard rollbacks

Helm provides

- Packaging
- Versioning
- Templates
- Rollbacks
- Dependency management
- Easy upgrades

---

# Helm Terminology

| Term | Description |
|--------|-------------|
| Chart | Kubernetes application package |
| Repository | Collection of Charts |
| Release | Running instance of a Chart |
| Values | Configuration supplied to a Chart |
| Template | Reusable YAML with variables |

---

# What is a Helm Chart?

A Helm Chart is a **bundle of Kubernetes YAML templates**.

Think of it as a blueprint for an application.

A Chart may include

- Deployment
- Service
- ConfigMap
- Secret
- Ingress
- Persistent Volume
- ServiceAccount

Instead of managing many YAML files separately, Helm packages them into one reusable unit.

---

# Helm Chart Structure

```
mychart/

├── Chart.yaml
├── values.yaml
├── charts/
├── templates/
└── .helmignore
```

---

# Chart.yaml

Contains metadata about the Chart.

Example

```yaml
apiVersion: v2
name: mychart
description: Demo application
version: 1.0.0
appVersion: "1.0"
```

Contains

- Chart Name
- Version
- Description
- Dependencies
- Maintainer

---

# values.yaml

Stores configuration values used by templates.

Example

```yaml
replicaCount: 3

image:
  repository: nginx
  tag: latest

service:
  type: ClusterIP
  port: 80
```

Instead of modifying templates, we update `values.yaml`.

---

# templates/

Contains the Kubernetes manifest templates.

Examples

```
deployment.yaml

service.yaml

configmap.yaml

secret.yaml

ingress.yaml
```

These files contain placeholders that Helm replaces during deployment.

Example

```yaml
replicas: {{ .Values.replicaCount }}
```

---

# charts/

Contains dependent Helm Charts.

Example

```
My Application

↓

MySQL Chart

↓

Redis Chart

↓

Prometheus Chart
```

Dependencies can be installed automatically.

---

# .helmignore

Works like `.gitignore`.

Specifies files Helm should ignore when packaging a Chart.

---

# What is a Release?

A Release is a deployed instance of a Helm Chart.

Example

Chart

```
nginx-chart
```

Installed as

```
production-nginx
```

Installed again

```
staging-nginx
```

One Chart can have multiple Releases.

---

# Helm Workflow

```
Developer

↓

Helm Chart

↓

helm install

↓

Kubernetes Cluster

↓

Release
```

---

# Helm Architecture

```
                 Helm CLI
                     │
                     │
             Helm Chart
                     │
         ┌───────────┴───────────┐
         │                       │
    values.yaml           templates/
         │                       │
         └───────────┬───────────┘
                     │
          Render Kubernetes YAML
                     │
                     ▼
            Kubernetes API Server
                     │
                     ▼
             Kubernetes Resources
```

---

# Template Engine

Helm uses the **Go Template Engine**.

Templates allow dynamic configuration.

Example

```yaml
replicas: {{ .Values.replicaCount }}
```

If

```yaml
replicaCount: 5
```

Generated YAML

```yaml
replicas: 5
```

---

# Why Templates?

Without Templates

```
deployment-dev.yaml

deployment-qa.yaml

deployment-prod.yaml
```

Three nearly identical files.

With Helm

One template.

Different `values.yaml` files.

---

# Installing a Chart

```bash
helm install myapp mychart
```

---

# Listing Releases

```bash
helm list
```

---

# Upgrading a Release

```bash
helm upgrade myapp mychart
```

---

# Rolling Back

```bash
helm rollback myapp 1
```

Rollback restores a previous release version.

---

# Uninstalling

```bash
helm uninstall myapp
```

---

# Real-World Example

Suppose you deploy a Django application.

Resources required

```
Deployment

↓

Service

↓

ConfigMap

↓

Secret

↓

Ingress

↓

PVC
```

Instead of maintaining six separate YAML files, Helm packages them into a single Chart.

Deploying becomes as simple as

```bash
helm install django-app .
```

---

# Helm Repository

A Helm Repository stores Charts.

Examples

- Bitnami
- Grafana
- Prometheus Community
- Elastic

Adding a repository

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
```

Updating repositories

```bash
helm repo update
```

Searching Charts

```bash
helm search repo nginx
```

---

# Advantages of Helm

- Reusable templates
- Environment-specific configurations
- Easy upgrades
- Rollbacks
- Dependency management
- Version control
- Faster deployments
- Reduced YAML duplication

---

# Limitations

- Adds another abstraction layer.
- Templates can become complex.
- Debugging rendered templates may require extra effort.

---

# Helm vs kubectl

| kubectl | Helm |
|----------|------|
| Applies raw YAML | Deploys packaged applications |
| No package management | Package management |
| Manual updates | Easy upgrades |
| Manual rollback | Built-in rollback |
| No dependency management | Dependency management |

---

# Interview Questions

## What is Helm?

Helm is the package manager for Kubernetes that simplifies deploying and managing Kubernetes applications using reusable Charts.

---

## What is a Helm Chart?

A Helm Chart is a collection of Kubernetes resource templates packaged as a reusable application.

---

## What is a Release?

A Release is a deployed instance of a Helm Chart.

---

## What is values.yaml?

It stores configurable values used by Helm templates, allowing the same Chart to be reused across different environments.

---

## What is Chart.yaml?

It contains metadata about the Helm Chart, such as its name, version, description, and dependencies.

---

## Why is Helm used?

Helm reduces YAML duplication, simplifies deployments, enables versioning, supports rollbacks, and manages application dependencies.

---

# Key Takeaways

- Helm is the package manager for Kubernetes.
- A Chart is a packaged Kubernetes application.
- A Release is a running instance of a Chart.
- `Chart.yaml` contains Chart metadata.
- `values.yaml` stores configurable values.
- The `templates/` directory contains parameterized Kubernetes manifests.
- The `charts/` directory stores dependent Charts.
- Helm uses the Go Template Engine.
- Helm simplifies deployment, upgrades, and rollbacks of Kubernetes applications.