# AWS X-Ray with EKS & Kubernetes

Amazon Elastic Kubernetes Service (EKS) supports AWS X-Ray for tracing containerized applications running inside Kubernetes clusters.

Applications running in Kubernetes can generate traces using the X-Ray SDK, while the X-Ray Daemon collects and uploads trace data to AWS.

------------------------------------------------------------------------

# Why Use X-Ray with Kubernetes?

Modern Kubernetes applications typically consist of many microservices.

AWS X-Ray helps developers:

- Trace requests across pods
- Analyze service latency
- Detect failures
- Visualize dependencies
- Monitor distributed applications

------------------------------------------------------------------------

# Architecture

```text
Client

↓

Ingress Controller

↓

Kubernetes Service

↓

Application Pod

↓

X-Ray SDK

↓

X-Ray Daemon

↓

AWS X-Ray
```

------------------------------------------------------------------------

# Deployment Options

There are two common deployment models.

## Sidecar Container

Each application pod contains:

```text
Pod

├── Application Container

└── X-Ray Daemon Container
```

Each pod manages its own trace uploads.

------------------------------------------------------------------------

## DaemonSet

The X-Ray Daemon runs once per Kubernetes node.

```text
Node

├── Application Pods

└── X-Ray Daemon
```

Multiple application pods communicate with the same daemon.

------------------------------------------------------------------------

# Using OpenTelemetry

AWS recommends OpenTelemetry for new applications.

OpenTelemetry can:

- Collect traces
- Export traces to AWS X-Ray
- Collect metrics
- Collect logs

This provides a unified observability solution.

------------------------------------------------------------------------

# Trace Flow

```text
User

↓

Ingress

↓

Service

↓

Application Pod

↓

SDK

↓

Daemon

↓

AWS X-Ray
```

------------------------------------------------------------------------

# IAM Permissions

Applications require permission to publish traces.

Common approaches include:

- IAM Roles for Service Accounts (IRSA)
- Node IAM Roles

------------------------------------------------------------------------

# Monitoring

Combine X-Ray with:

- Amazon CloudWatch
- Container Insights
- Prometheus
- Grafana

This provides comprehensive observability.

------------------------------------------------------------------------

# Real-World Example

A Kubernetes-based shopping platform contains:

```text
Frontend

↓

Product Service

↓

Order Service

↓

Payment Service

↓

Amazon RDS
```

X-Ray identifies that the Payment Service consistently introduces high latency during checkout, helping engineers focus optimization efforts.

------------------------------------------------------------------------

# Best Practices

- Use OpenTelemetry for new projects.
- Deploy the daemon using a DaemonSet or sidecar.
- Instrument every microservice.
- Monitor trace latency.
- Enable IAM Roles for Service Accounts (IRSA).

------------------------------------------------------------------------

# Key Takeaways

- Amazon EKS integrates with AWS X-Ray.
- Sidecar and DaemonSet are common deployment models.
- OpenTelemetry is the recommended observability framework for modern Kubernetes workloads.
- X-Ray provides end-to-end tracing across Kubernetes microservices.