# Kubernetes Architecture

## Overview

This section covers Kubernetes Architecture interview questions, focusing on how a Kubernetes cluster is structured and how its components work together to manage containerized applications.

Interviewers frequently ask architecture questions to assess whether you understand the responsibilities of the Control Plane, Worker Nodes, scheduling process, and cluster communication.

A solid understanding of Kubernetes architecture is essential for designing, deploying, and troubleshooting production workloads.

---

# Why These Questions Matter

Architecture questions help interviewers evaluate your understanding of:

- Kubernetes cluster components
- Control Plane responsibilities
- Worker Node responsibilities
- Pod scheduling
- Cluster communication
- High availability
- Application deployment workflow

These concepts form the backbone of every Kubernetes cluster.

---

# Beginner Questions

## 1. What are the main components of a Kubernetes cluster?

**Answer**

A Kubernetes cluster consists of two major parts:

- Control Plane
- Worker Nodes

The Control Plane manages the cluster, while Worker Nodes run the application workloads.

---

## 2. What is the Control Plane?

**Answer**

The Control Plane is the management layer of Kubernetes.

It is responsible for:

- Managing cluster state
- Scheduling Pods
- Monitoring workloads
- Processing API requests
- Maintaining the desired state

Core components include:

- API Server
- Scheduler
- Controller Manager
- etcd

---

## 3. What is a Worker Node?

**Answer**

A Worker Node is a machine that runs application Pods.

Each Worker Node contains:

- kubelet
- kube-proxy
- Container Runtime
- Pods

Worker Nodes receive instructions from the Control Plane.

---

## 4. What is the Kubernetes API Server?

**Answer**

The API Server is the entry point to the Kubernetes cluster.

Every command such as:

```bash
kubectl apply
kubectl get pods
kubectl delete pod
```

is processed by the API Server.

It validates requests and stores cluster information in etcd.

---

## 5. What is etcd?

**Answer**

etcd is Kubernetes' distributed key-value database.

It stores:

- Cluster configuration
- Resource definitions
- Secrets
- ConfigMaps
- Deployment information
- Current cluster state

Without etcd, Kubernetes cannot maintain the cluster state.

---

## 6. What is the Scheduler?

**Answer**

The Scheduler decides which Worker Node should run a Pod.

It evaluates:

- Available CPU
- Available Memory
- Resource Requests
- Node Affinity
- Taints and Tolerations
- Scheduling policies

The Scheduler only selects a node; it does not start the container.

---

## 7. What is the Controller Manager?

**Answer**

The Controller Manager continuously monitors the cluster and ensures the actual state matches the desired state.

Examples:

- Creates missing Pods
- Removes extra Pods
- Handles ReplicaSets
- Monitors Nodes

It implements Kubernetes' reconciliation loop.

---

## 8. What is kubelet?

**Answer**

kubelet is the primary agent running on every Worker Node.

Its responsibilities include:

- Communicating with the API Server
- Creating Pods
- Monitoring containers
- Reporting Pod status
- Restarting failed containers

---

## 9. What is kube-proxy?

**Answer**

kube-proxy manages networking on Worker Nodes.

It:

- Maintains network rules
- Enables Service communication
- Performs load balancing
- Routes traffic to Pods

---

## 10. What is a Container Runtime?

**Answer**

The Container Runtime runs containers on Worker Nodes.

Common runtimes include:

- containerd
- CRI-O

The runtime pulls container images and starts containers.

---

# Intermediate Questions

## 11. How does Kubernetes schedule a Pod?

**Answer**

The scheduling process is:

```text
Pod Created

↓

API Server

↓

Scheduler

↓

Worker Node Selected

↓

kubelet

↓

Container Runtime

↓

Pod Running
```

---

## 12. How does kubectl communicate with the cluster?

**Answer**

The workflow is:

```text
kubectl

↓

API Server

↓

etcd / Controllers / Scheduler

↓

Worker Node

↓

Pod
```

`kubectl` never communicates directly with Worker Nodes.

---

## 13. Which component stores the cluster state?

**Answer**

**etcd**

It is the single source of truth for the Kubernetes cluster.

---

## 14. Which component actually starts a Pod?

**Answer**

The Scheduler chooses the Worker Node.

The **kubelet** on that Worker Node instructs the **Container Runtime** to start the Pod.

---

## 15. What happens if a Worker Node fails?

**Answer**

The Control Plane detects that the node is unhealthy.

Pods running on that node are recreated on healthy Worker Nodes (if managed by a Deployment or ReplicaSet).

This ensures high availability.

---

## 16. What happens if the Scheduler fails?

**Answer**

Existing Pods continue running.

However, new Pods cannot be scheduled until the Scheduler becomes available again.

---

## 17. Can a cluster have multiple Worker Nodes?

**Answer**

Yes.

Production clusters often contain dozens or even hundreds of Worker Nodes.

Adding Worker Nodes increases:

- Capacity
- Scalability
- Fault tolerance

---

## 18. Can a cluster have multiple Control Plane nodes?

**Answer**

Yes.

Production environments often use multiple Control Plane nodes for high availability.

This prevents a single point of failure.

---

# Advanced Questions

## 19. Explain the Kubernetes reconciliation loop.

**Answer**

Kubernetes continuously compares:

```text
Desired State

↓

Actual State
```

If differences are detected:

- Missing Pods are recreated.
- Failed Pods are restarted.
- Replica counts are corrected.
- Node failures are handled.

This continuous monitoring process is called the **reconciliation loop**.

---

## 20. Why is the API Server considered the heart of Kubernetes?

**Answer**

Every component communicates through the API Server.

Examples:

- kubectl
- Scheduler
- Controller Manager
- kubelet

It acts as the central communication hub of the cluster.

---

## 21. Why is etcd so important?

**Answer**

etcd stores the entire cluster configuration.

If etcd is lost without a backup:

- Deployments
- Services
- Secrets
- ConfigMaps
- Cluster state

may be permanently lost.

Regular etcd backups are a production best practice.

---

## 22. How do Worker Nodes communicate with the Control Plane?

**Answer**

Worker Nodes communicate using the **kubelet**, which periodically reports status and receives instructions from the API Server.

Communication is secure and authenticated.

---

## 23. Which component performs load balancing?

**Answer**

Within the cluster, **kube-proxy** distributes traffic among Pods that belong to a Service.

External load balancing is typically handled by cloud load balancers or Ingress controllers.

---

## 24. What is the difference between the Scheduler and kubelet?

**Answer**

| Scheduler | kubelet |
|-----------|----------|
| Chooses the Worker Node | Runs on the Worker Node |
| Makes scheduling decisions | Starts and monitors containers |
| Runs in the Control Plane | Runs on every Worker Node |

---

## 25. Explain the complete lifecycle of deploying a Pod.

**Answer**

```text
kubectl apply

↓

API Server

↓

etcd

↓

Scheduler

↓

Worker Node Selected

↓

kubelet

↓

Container Runtime

↓

Container Starts

↓

Pod Running
```

---

# Common Mistakes

- Confusing the Scheduler with kubelet.
- Saying the API Server starts Pods directly.
- Forgetting that etcd stores the cluster state.
- Assuming kubectl communicates directly with Worker Nodes.
- Mixing up Control Plane and Worker Node responsibilities.

---

# Interview Tips

- Be able to explain the purpose of each Control Plane component.
- Remember that the Scheduler selects a node, while kubelet starts the Pod.
- Understand the end-to-end Pod deployment workflow.
- Mention high availability when discussing Control Plane architecture.
- Draw simple architecture diagrams during whiteboard interviews if possible.

---

## Key Takeaways

- A Kubernetes cluster consists of a **Control Plane** and one or more **Worker Nodes**.
- The API Server is the central communication hub for all cluster operations.
- etcd stores the cluster's desired and current state.
- The Scheduler selects the most appropriate Worker Node, while kubelet starts and manages Pods.
- Understanding Kubernetes architecture is essential for troubleshooting, designing scalable systems, and succeeding in Kubernetes interviews.