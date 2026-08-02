# Kubernetes Fundamentals

## Overview

This section covers the most frequently asked **Kubernetes Fundamentals** interview questions. These questions are commonly asked in Backend Developer, DevOps Engineer, Platform Engineer, and Cloud Engineer interviews.

The questions progress from beginner-level concepts to intermediate topics, helping you build a solid understanding of Kubernetes fundamentals.

---

# Why These Questions Matter

Interviewers ask Kubernetes fundamentals to evaluate whether you understand:

- Why Kubernetes exists
- Container orchestration concepts
- Kubernetes architecture
- Basic Kubernetes resources
- Production deployment concepts
- Cloud-native application development

A strong understanding of these fundamentals forms the basis for answering more advanced Kubernetes interview questions.

---

# Beginner Questions

## 1. What is Kubernetes?

**Answer**

Kubernetes (K8s) is an open-source container orchestration platform that automates the deployment, scaling, networking, and management of containerized applications.

It helps ensure applications remain highly available, scalable, and resilient across a cluster of machines.

---

## 2. Why do we need Kubernetes?

**Answer**

Managing containers manually becomes difficult as applications grow.

Kubernetes provides:

- Automatic deployment
- Auto-healing
- Scaling
- Load balancing
- Service discovery
- Rolling updates
- Self-healing

---

## 3. What problems does Kubernetes solve?

**Answer**

Kubernetes solves problems such as:

- Managing thousands of containers
- High availability
- Automatic scaling
- Service discovery
- Load balancing
- Zero-downtime deployments
- Resource management
- Infrastructure portability

---

## 4. What is a Kubernetes Cluster?

**Answer**

A Kubernetes Cluster is a group of machines working together to run containerized applications.

It consists of:

- Control Plane
- Worker Nodes

---

## 5. What is the Control Plane?

**Answer**

The Control Plane manages the entire Kubernetes cluster.

It makes scheduling decisions, manages cluster state, and ensures the desired state matches the actual state.

Major components include:

- API Server
- Scheduler
- Controller Manager
- etcd

---

## 6. What is a Worker Node?

**Answer**

Worker Nodes execute application workloads.

Each worker node runs:

- kubelet
- kube-proxy
- Container Runtime
- Application Pods

---

## 7. What is a Pod?

**Answer**

A Pod is the smallest deployable unit in Kubernetes.

A Pod contains one or more containers that share:

- Network namespace
- Storage
- IP address

Pods are temporary (ephemeral) and can be recreated if they fail.

---

## 8. Can multiple containers run inside one Pod?

**Answer**

Yes.

Multiple containers can run inside a single Pod.

They:

- Share networking
- Share storage
- Communicate using localhost

Common examples include:

- Logging sidecars
- Service mesh proxies
- Monitoring agents

---

## 9. What is kubectl?

**Answer**

`kubectl` is the official Kubernetes command-line tool.

It is used to:

- Create resources
- Update resources
- Delete resources
- View logs
- Debug applications
- Inspect cluster status

---

## 10. What is YAML in Kubernetes?

**Answer**

YAML files describe the desired state of Kubernetes resources.

They define:

- Pods
- Deployments
- Services
- ConfigMaps
- Secrets
- Ingress

---

# Intermediate Questions

## 11. What is the difference between Docker and Kubernetes?

**Answer**

Docker creates and runs containers.

Kubernetes manages containers across multiple machines.

Docker handles **containerization**, while Kubernetes handles **orchestration**.

---

## 12. What is container orchestration?

**Answer**

Container orchestration is the automated management of containers.

It includes:

- Scheduling
- Scaling
- Networking
- Health monitoring
- Resource allocation
- Deployment

Kubernetes is the most widely used container orchestration platform.

---

## 13. What is the desired state in Kubernetes?

**Answer**

The desired state is the configuration defined by the user.

Kubernetes continuously compares:

Desired State

vs

Actual State

If differences exist, Kubernetes automatically reconciles them.

Example:

Desired:

```text
3 Pods
```

Actual:

```text
2 Pods
```

Kubernetes automatically creates another Pod.

---

## 14. What is self-healing?

**Answer**

Self-healing means Kubernetes automatically restores failed workloads.

Examples:

- Restart failed containers
- Replace failed Pods
- Reschedule Pods to healthy nodes
- Restart unhealthy applications

---

## 15. What is auto-scaling?

**Answer**

Auto-scaling automatically adjusts application resources based on demand.

Types include:

- Horizontal Pod Autoscaler (HPA)
- Vertical Pod Autoscaler (VPA)
- Cluster Autoscaler

---

## 16. What is a Namespace?

**Answer**

Namespaces divide a Kubernetes cluster into logical environments.

Common namespaces:

- default
- kube-system
- kube-public
- custom namespaces

Namespaces help organize resources and provide isolation.

---

## 17. What are Labels?

**Answer**

Labels are key-value pairs attached to Kubernetes resources.

Example:

```yaml
labels:
  app: backend
  env: production
```

Labels help organize, group, and select resources.

---

## 18. What are Selectors?

**Answer**

Selectors identify resources based on labels.

Example:

```yaml
selector:
  app: backend
```

Services and ReplicaSets use selectors to locate Pods.

---

## 19. What is Helm?

**Answer**

Helm is the package manager for Kubernetes.

It simplifies:

- Installing applications
- Upgrading applications
- Version management
- Configuration reuse

Applications are packaged as **Helm Charts**.

---

## 20. What is Minikube?

**Answer**

Minikube is a lightweight local Kubernetes cluster used for development, learning, and testing.

It allows developers to experiment with Kubernetes on a single machine.

---

# Advanced Questions

## 21. Why are Pods considered ephemeral?

**Answer**

Pods are designed to be temporary.

If a Pod fails, Kubernetes creates a new Pod instead of repairing the existing one.

Applications should therefore avoid storing persistent data inside Pods.

---

## 22. Why shouldn't applications store data inside Pods?

**Answer**

Pod storage is temporary.

When a Pod is deleted or recreated, its local filesystem is lost.

Persistent data should be stored using:

- Persistent Volumes
- Persistent Volume Claims
- External databases

---

## 23. Why does Kubernetes use declarative configuration?

**Answer**

Instead of specifying individual commands, users define the desired state in YAML manifests.

Kubernetes continuously works to ensure the cluster matches that declared configuration.

This approach enables consistency, repeatability, and easier automation.

---

## 24. What is reconciliation in Kubernetes?

**Answer**

Reconciliation is the process by which Kubernetes continuously compares the desired state with the actual state and takes corrective actions whenever they differ.

This control loop is a core principle of Kubernetes.

---

## 25. What are the advantages of Kubernetes?

**Answer**

Major advantages include:

- High availability
- Auto-healing
- Automatic scaling
- Rolling updates
- Rollbacks
- Load balancing
- Service discovery
- Infrastructure portability
- Efficient resource utilization
- Strong ecosystem support

---

# Common Mistakes

- Saying Kubernetes replaces Docker (it orchestrates containers; it doesn't replace container technology).
- Assuming Pods are permanent.
- Confusing Pods with containers.
- Forgetting that Kubernetes manages the desired state.
- Assuming one Pod always contains one container.
- Thinking Kubernetes automatically stores persistent data.

---

# Interview Tips

- Explain concepts before giving examples.
- Distinguish clearly between containers, Pods, and Deployments.
- Remember that Pods are ephemeral.
- Understand the difference between orchestration and containerization.
- Know the role of the Control Plane and Worker Nodes.
- Be able to explain the Kubernetes reconciliation loop.
- Relate answers to real-world production scenarios whenever possible.

---

## Key Takeaways

- Kubernetes is a container orchestration platform designed to automate deployment, scaling, and management of containerized applications.
- A Kubernetes cluster consists of a Control Plane and one or more Worker Nodes.
- Pods are the smallest deployable units and are designed to be ephemeral.
- Kubernetes follows a declarative model, continuously reconciling the desired state with the actual state.
- Understanding these fundamentals provides the foundation for more advanced Kubernetes topics and technical interviews.