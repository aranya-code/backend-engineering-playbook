# Introduction

This chapter contains commonly asked Kubernetes interview questions, ranging from beginner to senior-level concepts.

The questions are grouped by topic to make revision easier.

---

# Section 1 - Kubernetes Fundamentals

## 1. What is Kubernetes?

Kubernetes is an open-source container orchestration platform used to deploy, manage, scale, and monitor containerized applications.

---

## 2. Why do we need Kubernetes?

Kubernetes automates:

- Container deployment
- Scaling
- Self-healing
- Load balancing
- Service discovery
- Rolling updates

---

## 3. What problems does Kubernetes solve?

- Manual container management
- High availability
- Fault tolerance
- Auto scaling
- Zero downtime deployments

---

## 4. What is a Kubernetes Cluster?

A Kubernetes Cluster consists of:

- Control Plane
- One or more Worker Nodes

---

## 5. What is a Worker Node?

A Worker Node is a machine where application Pods run.

---

## 6. What is the Control Plane?

The Control Plane manages the cluster.

It includes:

- API Server
- Scheduler
- Controller Manager
- etcd

---

## 7. What is kubelet?

kubelet is the agent running on every worker node.

It ensures Pods are running correctly.

---

## 8. What is kube-proxy?

kube-proxy manages networking and load balancing between Services and Pods.

---

## 9. What is etcd?

etcd is Kubernetes' distributed key-value database.

It stores the cluster state.

---

## 10. What is kubectl?

kubectl is the Kubernetes CLI used to communicate with the API Server.

---

# Section 2 - Pods

## 11. What is a Pod?

A Pod is the smallest deployable unit in Kubernetes.

---

## 12. Can a Pod contain multiple containers?

Yes.

Containers inside a Pod share:

- Network
- Storage
- Lifecycle

---

## 13. Why are Pods ephemeral?

Pods can be deleted and recreated at any time.

Applications should not depend on Pod IPs or local storage.

---

## 14. What happens if a Pod crashes?

If managed by a ReplicaSet or Deployment,

Kubernetes creates a replacement Pod automatically.

---

## 15. Difference between a Container and a Pod?

| Container | Pod |
|------------|-----|
| Runs application | Wraps one or more containers |
| No orchestration | Kubernetes object |
| Individual runtime | Smallest deployable unit |

---

## 16. What is an Init Container?

A container that runs before the application starts.

Used for setup tasks.

---

## 17. What are Sidecar Containers?

Helper containers running alongside the main application.

Examples

- Logging
- Monitoring
- Proxy

---

## 18. Difference between Liveness and Readiness Probe?

Liveness

Checks if the application is alive.

Readiness

Checks if the application is ready to receive traffic.

---

## 19. What is a Startup Probe?

A probe for slow-starting applications.

---

## 20. Why shouldn't Pods be created directly in production?

Because they lack

- Self-healing
- Scaling
- Rolling updates

Deployments should be used instead.

---

# Section 3 - ReplicaSets & Deployments

## 21. What is a ReplicaSet?

Ensures a specified number of Pods are always running.

---

## 22. What is Self-Healing?

Automatically recreating failed Pods.

---

## 23. How does ReplicaSet identify Pods?

Using Labels and Selectors.

---

## 24. What is a Deployment?

A Deployment manages ReplicaSets and provides rolling updates, scaling, and rollbacks.

---

## 25. Difference between ReplicaSet and Deployment?

ReplicaSet

- Self-healing

Deployment

- Self-healing
- Rolling updates
- Rollbacks
- Version history

---

## 26. What is a Rolling Update?

Replacing Pods gradually without downtime.

---

## 27. What is a Rollback?

Returning to the previous working deployment.

---

## 28. What deployment strategy is used by default?

Rolling Update.

---

## 29. What is Blue-Green Deployment?

Two production environments.

Traffic switches from Blue to Green.

---

## 30. What is Canary Deployment?

Deploying the new version to a small percentage of users before full rollout.

---

# Section 4 - Services

## 31. Why do we need Services?

Pods are temporary.

Services provide stable networking.

---

## 32. What is ClusterIP?

Internal communication only.

---

## 33. What is NodePort?

Exposes applications using a port on every node.

---

## 34. What is LoadBalancer?

Creates a cloud provider load balancer.

---

## 35. What is a Headless Service?

A Service without a Cluster IP.

Used by StatefulSets.

---

## 36. Difference between ClusterIP and NodePort?

ClusterIP

Internal

NodePort

External

---

## 37. Difference between NodePort and LoadBalancer?

NodePort exposes a node port.

LoadBalancer provisions a cloud load balancer.

---

## 38. What is Service Discovery?

Services receive DNS names.

Applications communicate using DNS instead of Pod IPs.

---

## 39. How do Services identify Pods?

Using Labels and Selectors.

---

## 40. What are Endpoints?

Endpoints store Pod IP addresses behind a Service.

---

# Section 5 - Storage

## 41. Why is Persistent Storage needed?

Containers lose local data after restarting.

---

## 42. What is a Persistent Volume?

A storage resource managed by Kubernetes.

---

## 43. What is a Persistent Volume Claim?

A request for storage.

---

## 44. Difference between PV and PVC?

PV

Actual storage.

PVC

Storage request.

---

## 45. What is a StorageClass?

Automates storage provisioning.

---

## 46. Difference between Static and Dynamic Provisioning?

Static

Administrator creates PV.

Dynamic

StorageClass creates PV automatically.

---

## 47. What are Access Modes?

- ReadWriteOnce
- ReadOnlyMany
- ReadWriteMany

---

## 48. What is Reclaim Policy?

Determines what happens to storage after PVC deletion.

---

## 49. Which workloads require Persistent Volumes?

- Databases
- File Servers
- Stateful Applications

---

## 50. Can Pods survive without Persistent Storage?

Yes.

But data will be lost after restart.

---

# Section 6 - StatefulSets

## 51. What is a StatefulSet?

Manages stateful applications.

---

## 52. Difference between StatefulSet and Deployment?

Deployment

Stateless

StatefulSet

Stateful

---

## 53. Why do StatefulSets need Headless Services?

To provide stable DNS names.

---

## 54. Why do StatefulSets require Persistent Volumes?

To preserve data.

---

## 55. Give examples of Stateful applications.

- MySQL
- PostgreSQL
- MongoDB
- Kafka

---

# Section 7 - ConfigMaps & Secrets

## 56. What is a ConfigMap?

Stores non-sensitive configuration.

---

## 57. What is a Secret?

Stores sensitive information.

---

## 58. Is Base64 encryption?

No.

It is only encoding.

---

## 59. How are ConfigMaps consumed?

- Environment Variables
- Mounted Files

---

## 60. How are Secrets consumed?

- Environment Variables
- Mounted Volumes

---

# Section 8 - Ingress

## 61. What is Ingress?

Routes external HTTP/HTTPS traffic.

---

## 62. Why do we need Ingress?

Single entry point for multiple services.

---

## 63. What is an Ingress Controller?

Implements Ingress routing rules.

---

## 64. Difference between Service and Ingress?

Service

Internal networking.

Ingress

External HTTP routing.

---

## 65. Name popular Ingress Controllers.

- NGINX
- Traefik
- HAProxy
- Kong

---

# Section 9 - Helm

## 66. What is Helm?

Package manager for Kubernetes.

---

## 67. What is a Helm Chart?

A packaged Kubernetes application.

---

## 68. What is a Release?

A deployed instance of a Chart.

---

## 69. What is values.yaml?

Stores configurable values.

---

## 70. What is Chart.yaml?

Stores chart metadata.

---

# Section 10 - kubectl

## 71. Difference between apply and create?

create

Creates only.

apply

Creates or updates.

---

## 72. How do you see Pod logs?

```bash
kubectl logs <pod>
```

---

## 73. How do you enter a running Pod?

```bash
kubectl exec -it <pod> -- bash
```

---

## 74. How do you scale a Deployment?

```bash
kubectl scale deployment app --replicas=5
```

---

## 75. How do you roll back a Deployment?

```bash
kubectl rollout undo deployment app
```

---

# Section 11 - Scenario-Based Questions

## 76. A Pod is in Pending state. What will you check?

- Node availability
- CPU and Memory
- PVC binding
- Events
- Scheduler logs

---

## 77. A Pod is in CrashLoopBackOff.

Possible causes

- Application crash
- Wrong configuration
- Missing Secret
- Missing ConfigMap
- Invalid startup command

---

## 78. ImagePullBackOff error.

Possible causes

- Wrong image
- Private registry
- Missing credentials

---

## 79. Users cannot access the application.

Check

- Service
- Ingress
- Endpoints
- Labels
- Network Policies

---

## 80. Deployment stuck during rollout.

Check

- Readiness Probe
- Image Pull
- Events
- Logs

---

# Section 12 - Senior-Level Questions

## 81. Why is etcd critical?

It stores the entire cluster state.

Losing etcd means losing the cluster configuration.

---

## 82. Why is Deployment preferred over ReplicaSet?

Deployments support

- Rollbacks
- Rolling Updates
- Version History

---

## 83. How does Kubernetes achieve High Availability?

- Multiple replicas
- Self-healing
- Load balancing
- Rolling updates

---

## 84. How would you deploy a Django application?

Deployment

↓

Service

↓

Ingress

↓

ConfigMap

↓

Secret

↓

Persistent Volume (if required)

---

## 85. How would you deploy PostgreSQL?

StatefulSet

↓

PVC

↓

PV

↓

Headless Service

---

## 86. Why shouldn't application configuration be stored in Docker images?

Configuration changes between environments.

Use ConfigMaps and Secrets instead.

---

## 87. Explain Kubernetes architecture in two minutes.

A Kubernetes Cluster contains a Control Plane and Worker Nodes.

The API Server receives requests.

The Scheduler places Pods on Nodes.

The Controller Manager maintains the desired state.

etcd stores cluster configuration.

Worker Nodes run Pods using kubelet and the container runtime.

---

## 88. Explain the Deployment lifecycle.

Deployment

↓

ReplicaSet

↓

Pods

↓

Rolling Update

↓

New ReplicaSet

↓

Rollback if required.

---

## 89. Explain the request flow when a user accesses an application.

```
Internet

↓

Ingress

↓

Service

↓

Pod

↓

Container
```

---

## 90. If you were designing a production Kubernetes cluster, what would you include?

- Multiple Nodes
- Multiple Replicas
- Ingress Controller
- ConfigMaps
- Secrets
- Persistent Volumes
- Monitoring
- Logging
- Resource Limits
- Liveness & Readiness Probes
- RBAC
- Network Policies
- CI/CD Pipeline

---

# Rapid Fire Questions

- What is Kubernetes?
- What is kubectl?
- What is kubelet?
- What is etcd?
- What is a Pod?
- What is a ReplicaSet?
- What is a Deployment?
- What is a Service?
- What is Ingress?
- What is Helm?
- What is a ConfigMap?
- What is a Secret?
- What is a Namespace?
- What is a Persistent Volume?
- What is a StatefulSet?
- What is a Rolling Update?
- What is a Rollback?
- What is a Headless Service?
- What is a StorageClass?
- What is an Init Container?

---

