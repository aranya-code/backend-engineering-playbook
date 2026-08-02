# What is Minikube?

**Minikube** is a tool that allows you to run a **single-node Kubernetes cluster** on your local machine.

It is designed for:

- Learning Kubernetes
- Local Development
- Testing Applications
- Experimenting with Kubernetes Features

Instead of renting cloud infrastructure, Minikube lets you create a Kubernetes cluster on your laptop.

---

# Why Do We Need Minikube?

Creating a production Kubernetes cluster requires multiple machines and complex setup.

Minikube simplifies this by creating a local cluster that includes all the essential Kubernetes components.

Without Minikube

```
Need Cloud Infrastructure

↓

Multiple Servers

↓

Networking Setup

↓

Storage Setup
```

With Minikube

```
Laptop

↓

Minikube

↓

Single Node Kubernetes Cluster
```

---

# Minikube Architecture

```
              Local Computer

                    │

              Minikube Cluster

                    │

      ┌─────────────────────────┐

      │     Control Plane       │

      │                         │

      │    Worker Node          │

      │                         │

      │      Pods               │

      └─────────────────────────┘
```

Minikube combines the Control Plane and Worker Node into a single machine.

---

# Features of Minikube

- Single-node Kubernetes Cluster
- Easy Installation
- Lightweight
- Supports Multiple Drivers
- Built-in Dashboard
- Addons Support
- Local Image Registry
- Works Offline

---

# System Requirements

Minimum

- 2 CPUs
- 2 GB RAM
- 20 GB Free Disk Space

Recommended

- 4 CPUs
- 8 GB RAM
- SSD Storage

---

# Prerequisites

Before installing Minikube, install:

- Docker (Recommended Driver)
- VirtualBox (Optional)
- Hyper-V (Windows)
- kubectl

Verify Docker

```bash
docker --version
```

Verify kubectl

```bash
kubectl version --client
```

---

# Installing Minikube

### Windows (Chocolatey)

```powershell
choco install minikube
```

---

### macOS (Homebrew)

```bash
brew install minikube
```

---

### Linux

```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64

sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

---

# Verify Installation

```bash
minikube version
```

Example

```
minikube version: v1.xx.x
```

---

# Starting a Cluster

Start the default cluster

```bash
minikube start
```

Specify Docker Driver

```bash
minikube start --driver=docker
```

Specify Kubernetes Version

```bash
minikube start --kubernetes-version=v1.30.0
```

---

# Check Cluster Status

```bash
minikube status
```

Example

```
host: Running

kubelet: Running

apiserver: Running

kubeconfig: Configured
```

---

# Verify Cluster

View Nodes

```bash
kubectl get nodes
```

Example

```
NAME

minikube

STATUS

Ready
```

---

# View Cluster Information

```bash
kubectl cluster-info
```

Displays

- API Server
- CoreDNS
- Cluster Endpoints

---

# Stopping the Cluster

```bash
minikube stop
```

The cluster is stopped but not deleted.

---

# Starting Again

```bash
minikube start
```

---

# Deleting the Cluster

```bash
minikube delete
```

This removes the entire cluster.

---

# Kubernetes Dashboard

Minikube provides a built-in Kubernetes Dashboard.

Start Dashboard

```bash
minikube dashboard
```

The browser opens automatically.

Dashboard allows you to

- View Pods
- View Deployments
- View Services
- View Logs
- Scale Applications

---

# Minikube Dashboard Architecture

```
Browser

↓

Dashboard

↓

API Server

↓

Cluster Resources
```

---

# Minikube Addons

Minikube includes several built-in addons.

View Addons

```bash
minikube addons list
```

---

Enable Ingress

```bash
minikube addons enable ingress
```

---

Enable Metrics Server

```bash
minikube addons enable metrics-server
```

---

Enable Dashboard

```bash
minikube addons enable dashboard
```

---

Disable Addon

```bash
minikube addons disable ingress
```

---

# Accessing Applications

Suppose a Service is running.

Instead of manually finding the IP,

Run

```bash
minikube service <service-name>
```

Example

```bash
minikube service nginx-service
```

The application opens in the browser.

---

# Minikube IP

View Cluster IP

```bash
minikube ip
```

Example

```
192.168.49.2
```

Useful for accessing NodePort services.

---

# SSH into Minikube

```bash
minikube ssh
```

Useful for

- Viewing files
- Checking logs
- Debugging

---

# Docker Environment

Build Docker images directly inside Minikube.

```bash
minikube docker-env
```

For Docker CLI

```bash
eval $(minikube docker-env)
```

Now Docker builds images inside Minikube.

---

# Load Local Images

Instead of pushing to Docker Hub,

Load directly

```bash
minikube image load my-app:latest
```

This saves development time.

---

# Useful Commands

| Command | Description |
|----------|-------------|
| `minikube start` | Start cluster |
| `minikube stop` | Stop cluster |
| `minikube delete` | Delete cluster |
| `minikube status` | Cluster status |
| `minikube ip` | Cluster IP |
| `minikube ssh` | SSH into cluster |
| `minikube dashboard` | Open Dashboard |
| `minikube addons list` | List addons |
| `minikube service <service>` | Open Service |
| `minikube logs` | View Minikube logs |

---

# Typical Development Workflow

```
Start Minikube

↓

Deploy Application

↓

Verify Pods

↓

Access Service

↓

Modify YAML

↓

kubectl apply

↓

Test Application

↓

Stop Cluster
```

---

# Common Problems

## Minikube Won't Start

Possible Causes

- Docker not running
- Virtualization disabled
- Insufficient RAM
- Unsupported driver

Check

```bash
minikube logs
```

---

## Node Not Ready

Run

```bash
kubectl get nodes
```

Restart

```bash
minikube stop

minikube start
```

---

## Service Not Accessible

Check

```bash
kubectl get svc
```

Then

```bash
minikube service <service-name>
```

---

## Dashboard Doesn't Open

Restart Dashboard

```bash
minikube dashboard
```

---

# Best Practices

✔ Use Docker as the Minikube driver whenever possible.

✔ Enable Metrics Server for resource monitoring.

✔ Enable Ingress when learning networking.

✔ Use `minikube image load` for locally built images.

✔ Stop Minikube when not in use to save system resources.

✔ Delete and recreate the cluster if it becomes inconsistent during learning.

---

# Minikube vs Production Cluster

| Minikube | Production Cluster |
|-----------|--------------------|
| Single Node | Multiple Nodes |
| Local Machine | Cloud / On-Premises |
| Development & Learning | Production Workloads |
| Lightweight | Highly Available |
| Free | Infrastructure Cost |

---

# Interview Questions

## What is Minikube?

Minikube is a tool that creates a local single-node Kubernetes cluster for development, testing, and learning.

---

## Why is Minikube used?

It allows developers to run Kubernetes locally without needing a cloud-based cluster.

---

## Can Minikube be used in production?

No.

Minikube is intended for development and testing. Production environments typically use multi-node clusters such as Amazon EKS, Azure AKS, Google GKE, or self-managed Kubernetes.

---

## How do you access a Service in Minikube?

Using:

```bash
minikube service <service-name>
```

or by accessing the NodePort using the Minikube IP.

---

## What are Minikube Addons?

Addons are optional components such as Ingress, Metrics Server, and the Kubernetes Dashboard that can be enabled to extend cluster functionality.

---

# Key Takeaways

- Minikube provides a local single-node Kubernetes cluster.
- It combines the Control Plane and Worker Node into one environment.
- It is ideal for learning, development, and testing.
- Supports Docker, VirtualBox, Hyper-V, and other drivers.
- Includes useful features such as the Dashboard, Addons, and local image loading.
- Minikube is not intended for production use.
- It is the easiest way to practice Kubernetes commands and deploy applications locally.