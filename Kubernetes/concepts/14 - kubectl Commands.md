# What is kubectl?

`kubectl` (pronounced **cube-control**) is the official **Command Line Interface (CLI)** for Kubernetes.

It allows users to interact with the Kubernetes API Server to create, update, delete, and manage Kubernetes resources.

Think of `kubectl` as the **primary management tool** for Kubernetes clusters.

```
Developer

↓

kubectl

↓

API Server

↓

Kubernetes Cluster
```

---

# Why Do We Need kubectl?

Without kubectl

- Difficult to manage resources
- Manual API calls
- No automation

With kubectl

- Create resources
- Delete resources
- Update resources
- Debug applications
- Monitor clusters
- Scale applications

---

# kubectl Command Syntax

```bash
kubectl <command> <resource> <name> [flags]
```

Example

```bash
kubectl get pods
```

```
kubectl

↓

get

↓

pods
```

---

# Cluster Commands

## View Cluster Information

```bash
kubectl cluster-info
```

Example Output

```
Kubernetes control plane

CoreDNS

Metrics Server
```

---

## Check Kubernetes Version

```bash
kubectl version
```

Client Version

Server Version

---

## View Nodes

```bash
kubectl get nodes
```

Short Form

```bash
kubectl get no
```

Example

```
NAME           STATUS
master         Ready
worker-1       Ready
worker-2       Ready
```

---

## Describe Node

```bash
kubectl describe node worker-1
```

Displays

- CPU
- Memory
- Labels
- Taints
- Capacity
- Conditions

---

# Namespace Commands

View Namespaces

```bash
kubectl get namespaces
```

Short Form

```bash
kubectl get ns
```

Create Namespace

```bash
kubectl create namespace development
```

Delete Namespace

```bash
kubectl delete namespace development
```

Switch Namespace

```bash
kubectl config set-context --current --namespace=development
```

---

# Pod Commands

View Pods

```bash
kubectl get pods
```

Short Form

```bash
kubectl get po
```

View Pods in All Namespaces

```bash
kubectl get pods -A
```

View Wide Output

```bash
kubectl get pods -o wide
```

Watch Pod Changes

```bash
kubectl get pods -w
```

Describe Pod

```bash
kubectl describe pod nginx-pod
```

Delete Pod

```bash
kubectl delete pod nginx-pod
```

Delete All Pods

```bash
kubectl delete pods --all
```

---

# Deployment Commands

View Deployments

```bash
kubectl get deployments
```

Short Form

```bash
kubectl get deploy
```

Describe Deployment

```bash
kubectl describe deployment nginx
```

Delete Deployment

```bash
kubectl delete deployment nginx
```

Scale Deployment

```bash
kubectl scale deployment nginx --replicas=5
```

Restart Deployment

```bash
kubectl rollout restart deployment nginx
```

---

# Rollout Commands

View Rollout Status

```bash
kubectl rollout status deployment nginx
```

View Rollout History

```bash
kubectl rollout history deployment nginx
```

Rollback Deployment

```bash
kubectl rollout undo deployment nginx
```

Rollback to Specific Revision

```bash
kubectl rollout undo deployment nginx --to-revision=2
```

---

# ReplicaSet Commands

View ReplicaSets

```bash
kubectl get rs
```

Describe ReplicaSet

```bash
kubectl describe rs nginx
```

Scale ReplicaSet

```bash
kubectl scale rs nginx --replicas=4
```

Delete ReplicaSet

```bash
kubectl delete rs nginx
```

---

# Service Commands

View Services

```bash
kubectl get svc
```

Describe Service

```bash
kubectl describe svc backend-service
```

Delete Service

```bash
kubectl delete svc backend-service
```

View Endpoints

```bash
kubectl get endpoints
```

---

# ConfigMap Commands

View ConfigMaps

```bash
kubectl get configmaps
```

Short Form

```bash
kubectl get cm
```

Describe ConfigMap

```bash
kubectl describe cm app-config
```

Delete ConfigMap

```bash
kubectl delete cm app-config
```

---

# Secret Commands

View Secrets

```bash
kubectl get secrets
```

Describe Secret

```bash
kubectl describe secret db-secret
```

Delete Secret

```bash
kubectl delete secret db-secret
```

---

# Persistent Storage Commands

View Persistent Volumes

```bash
kubectl get pv
```

View Persistent Volume Claims

```bash
kubectl get pvc
```

View Storage Classes

```bash
kubectl get storageclass
```

Short Form

```bash
kubectl get sc
```

---

# Logs

View Logs

```bash
kubectl logs nginx-pod
```

Follow Logs

```bash
kubectl logs -f nginx-pod
```

Previous Container Logs

```bash
kubectl logs --previous nginx-pod
```

Specific Container Logs

```bash
kubectl logs nginx-pod -c app
```

---

# Execute Commands Inside a Pod

Open Bash

```bash
kubectl exec -it nginx-pod -- bash
```

Open Shell

```bash
kubectl exec -it nginx-pod -- sh
```

Run Single Command

```bash
kubectl exec nginx-pod -- ls
```

---

# Port Forwarding

Forward Local Port

```bash
kubectl port-forward pod/nginx-pod 8080:80
```

Forward Service

```bash
kubectl port-forward svc/backend-service 8080:80
```

Useful during local development.

---

# Apply Resources

Create or Update

```bash
kubectl apply -f deployment.yaml
```

Apply Entire Folder

```bash
kubectl apply -f .
```

---

# Delete Resources

Delete YAML

```bash
kubectl delete -f deployment.yaml
```

Delete Everything in Folder

```bash
kubectl delete -f .
```

---

# Generate YAML

Generate Pod YAML

```bash
kubectl run nginx \
--image=nginx \
--dry-run=client \
-o yaml
```

Generate Deployment YAML

```bash
kubectl create deployment nginx \
--image=nginx \
--dry-run=client \
-o yaml
```

Useful for creating starter manifests.

---

# Edit Resources

Edit Deployment

```bash
kubectl edit deployment nginx
```

Edit Service

```bash
kubectl edit service backend
```

---

# View Resource YAML

```bash
kubectl get pod nginx-pod -o yaml
```

Deployment

```bash
kubectl get deployment nginx -o yaml
```

Service

```bash
kubectl get svc backend -o yaml
```

---

# Debugging Commands

View Events

```bash
kubectl get events
```

Sort Events

```bash
kubectl get events --sort-by=.metadata.creationTimestamp
```

Debug Pod

```bash
kubectl debug nginx-pod -it --image=busybox
```

---

# Resource Usage

Requires Metrics Server.

View Node Usage

```bash
kubectl top nodes
```

View Pod Usage

```bash
kubectl top pods
```

---

# Label Commands

Add Label

```bash
kubectl label pod nginx app=frontend
```

Remove Label

```bash
kubectl label pod nginx app-
```

---

# Annotation Commands

Add Annotation

```bash
kubectl annotate pod nginx owner=aranya
```

Remove Annotation

```bash
kubectl annotate pod nginx owner-
```

---

# Context Commands

View Contexts

```bash
kubectl config get-contexts
```

Current Context

```bash
kubectl config current-context
```

Switch Context

```bash
kubectl config use-context production
```

---

# Common Output Options

Wide Output

```bash
kubectl get pods -o wide
```

YAML Output

```bash
kubectl get pod nginx -o yaml
```

JSON Output

```bash
kubectl get pod nginx -o json
```

Custom Columns

```bash
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase
```

---

# Helpful Aliases

```bash
alias k=kubectl
```

Examples

```bash
k get pods
```

```bash
k get svc
```

```bash
k get deploy
```

---

# Frequently Used Short Names

| Full Name | Short Name |
|------------|------------|
| pods | po |
| services | svc |
| deployments | deploy |
| replicasets | rs |
| namespaces | ns |
| configmaps | cm |
| persistentvolumeclaims | pvc |
| storageclasses | sc |
| nodes | no |

---

# kubectl Workflow

```
Developer

↓

kubectl apply

↓

API Server

↓

Scheduler

↓

Worker Node

↓

Pods Running
```

---

# Best Practices

✔ Prefer `kubectl apply` over `kubectl create` for declarative resource management.

✔ Use `kubectl describe` when troubleshooting.

✔ Check logs before restarting Pods.

✔ Use `kubectl rollout status` after deployments.

✔ Use `kubectl get events` to investigate cluster issues.

✔ Store YAML manifests in Git.

✔ Use namespaces to organize workloads.

---

# Common Troubleshooting Commands

| Problem | Command |
|----------|----------|
| Pod not starting | `kubectl describe pod <pod-name>` |
| View logs | `kubectl logs <pod-name>` |
| Enter Pod | `kubectl exec -it <pod-name> -- bash` |
| Check events | `kubectl get events` |
| Check rollout | `kubectl rollout status deployment <name>` |
| Check node health | `kubectl get nodes` |
| View resource usage | `kubectl top pods` |

---

# Interview Questions

## What is kubectl?

`kubectl` is the official command-line tool used to communicate with the Kubernetes API Server and manage Kubernetes resources.

---

## What is the difference between `kubectl apply` and `kubectl create`?

- `kubectl create` creates a new resource and fails if it already exists.
- `kubectl apply` creates the resource if it doesn't exist or updates it if it does, making it suitable for declarative management.

---

## How do you view logs from a Pod?

```bash
kubectl logs <pod-name>
```

---

## How do you access a running container?

```bash
kubectl exec -it <pod-name> -- bash
```

---

## How do you roll back a Deployment?

```bash
kubectl rollout undo deployment <deployment-name>
```

---

## How do you scale a Deployment?

```bash
kubectl scale deployment <deployment-name> --replicas=<count>
```

---

# Key Takeaways

- `kubectl` is the primary CLI for managing Kubernetes.
- It communicates with the Kubernetes API Server.
- Use `kubectl apply` for declarative resource management.
- `kubectl describe` and `kubectl logs` are essential troubleshooting commands.
- `kubectl exec` allows you to inspect running containers.
- `kubectl rollout` manages deployment updates and rollbacks.
- Learn the short resource names (`po`, `svc`, `deploy`, `rs`, `ns`, etc.) to improve productivity.