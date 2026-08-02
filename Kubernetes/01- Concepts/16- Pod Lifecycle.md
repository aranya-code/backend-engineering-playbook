# Pod Lifecycle

## Overview

A **Pod** is the smallest deployable unit in Kubernetes. Every Pod goes through a well-defined lifecycle, from creation to termination. Understanding the Pod lifecycle helps you troubleshoot application failures, design resilient workloads, and prepare for Kubernetes interviews.

Unlike virtual machines, Pods are **ephemeral**. They are created, scheduled, run, and eventually terminated. If a Pod fails, Kubernetes usually replaces it with a new Pod instead of repairing the existing one.

---

## Why Pod Lifecycle Matters

Understanding the Pod lifecycle helps you:

- Debug Pod startup issues
- Diagnose scheduling failures
- Monitor application health
- Configure readiness and liveness probes
- Handle graceful shutdowns
- Understand Deployment and ReplicaSet behavior

---

## Pod Lifecycle Overview

The lifecycle of a Pod can be divided into several stages:

```text
Pod Created
      │
      ▼
Pending
      │
      ▼
Container Image Pulled
      │
      ▼
Running
      │
      ▼
Succeeded / Failed
      │
      ▼
Terminating
```

---

## Pod Phases

A Pod's status is represented by its **Phase**.

### 1. Pending

The Pod has been accepted by Kubernetes but is not yet running.

Common reasons include:

- Waiting for a node
- Image being downloaded
- Persistent Volume not attached
- Insufficient cluster resources

Example:

```bash
kubectl get pods
```

Output:

```text
NAME         READY   STATUS    RESTARTS   AGE
nginx-pod    0/1     Pending   0          5s
```

---

### 2. Running

The Pod has been scheduled to a node.

At least one container is running or starting.

Example:

```text
STATUS: Running
```

Running does **not** always mean the application is ready to serve traffic.

That is determined by the **Readiness Probe**.

---

### 3. Succeeded

All containers completed successfully.

Usually seen in:

- Jobs
- Batch processing
- Database migration Pods

Example:

```text
STATUS: Completed
```

---

### 4. Failed

One or more containers terminated unsuccessfully.

Possible reasons:

- Application crash
- Invalid command
- Missing configuration
- Image issue

Example:

```text
STATUS: Error
```

---

### 5. Unknown

The Kubernetes API cannot determine the Pod status.

Usually caused by:

- Node communication failure
- Network partition
- Node crash

---

## Pod Conditions

Besides phases, Pods also expose **Conditions**.

Common conditions include:

| Condition | Meaning |
|-----------|----------|
| PodScheduled | Assigned to a node |
| Initialized | Init containers completed |
| ContainersReady | Containers are ready |
| Ready | Pod can receive traffic |

View them using:

```bash
kubectl describe pod nginx
```

---

## Pod Creation Process

When you create a Pod, Kubernetes performs several steps.

```text
User creates Pod
        │
        ▼
API Server receives request
        │
        ▼
Scheduler selects a node
        │
        ▼
Kubelet starts containers
        │
        ▼
Container Runtime pulls image
        │
        ▼
Containers start
        │
        ▼
Pod becomes Running
```

---

## Container States

Each container inside a Pod has its own state.

### Waiting

The container has not started.

Common reasons:

- ImagePullBackOff
- ErrImagePull
- ContainerCreating

---

### Running

The container is actively executing.

Example:

```text
State: Running
```

---

### Terminated

The container has stopped.

Information includes:

- Exit code
- Start time
- Finish time
- Reason

Example:

```text
State: Terminated
Reason: Completed
Exit Code: 0
```

---

## Restart Policy

Pods define how Kubernetes should restart containers.

Available policies:

| Restart Policy | Description |
|---------------|-------------|
| Always | Always restart (default for Deployments) |
| OnFailure | Restart only after failure |
| Never | Never restart |

Example:

```yaml
restartPolicy: OnFailure
```

---

## Pod Deletion Process

Deleting a Pod is not immediate.

Steps:

```text
Delete Command
      │
      ▼
Termination Signal (SIGTERM)
      │
      ▼
Grace Period
      │
      ▼
Containers Stop
      │
      ▼
Pod Removed
```

Default graceful termination period:

```text
30 seconds
```

Can be configured:

```yaml
terminationGracePeriodSeconds: 60
```

---

## Graceful Shutdown

When Kubernetes deletes a Pod:

1. Sends a **SIGTERM**
2. Application finishes current work
3. Connections close gracefully
4. Resources are released
5. Pod exits
6. Kubernetes sends **SIGKILL** if the timeout expires

This prevents:

- Lost requests
- Database corruption
- Partial transactions

---

## Init Containers

Init Containers run **before** application containers.

They are commonly used to:

- Download configuration
- Wait for a database
- Perform setup tasks
- Initialize data

Example flow:

```text
Init Container
      │
      ▼
Completed
      │
      ▼
Main Container Starts
```

---

## Sidecar Containers

A Pod can contain multiple containers.

Example:

```text
Pod
├── Application Container
├── Logging Sidecar
└── Monitoring Sidecar
```

Common sidecars:

- Fluent Bit
- Envoy Proxy
- Metrics exporters

---

## Viewing Pod Lifecycle

List Pods:

```bash
kubectl get pods
```

Watch lifecycle changes:

```bash
kubectl get pods -w
```

Describe a Pod:

```bash
kubectl describe pod nginx
```

View events:

```bash
kubectl get events
```

View logs:

```bash
kubectl logs nginx
```

---

## Common Lifecycle Problems

| Problem | Possible Cause |
|----------|----------------|
| Pending | No available node |
| ImagePullBackOff | Invalid image |
| CrashLoopBackOff | Application crash |
| ErrImagePull | Registry issue |
| CreateContainerConfigError | Missing Secret or ConfigMap |
| ContainerCreating | Waiting for resources |
| OOMKilled | Memory limit exceeded |

---

## Best Practices

- Keep Pods stateless whenever possible.
- Use Deployments instead of standalone Pods.
- Configure resource requests and limits.
- Use Readiness and Liveness probes.
- Handle SIGTERM properly in applications.
- Store persistent data in Persistent Volumes.
- Monitor Pod events during debugging.
- Use labels for efficient Pod management.

---

## Interview Tips

- A Pod is **ephemeral**, not permanent.
- Kubernetes replaces failed Pods rather than repairing them.
- A Pod phase is different from a container state.
- Running does not always mean Ready.
- Pods receive a SIGTERM before termination.
- Restart policies control container restart behavior.
- Init Containers always finish before application containers start.
- Sidecar containers share the same Pod and network namespace.

---

## Key Takeaways

- A Pod progresses through well-defined lifecycle phases from creation to termination.
- The main Pod phases are **Pending**, **Running**, **Succeeded**, **Failed**, and **Unknown**.
- Container states (Waiting, Running, Terminated) provide more detailed execution information than Pod phases.
- Kubernetes uses restart policies and graceful termination to improve application reliability.
- Init containers prepare the environment before the main application starts, while sidecars extend Pod functionality.
- Understanding the Pod lifecycle is essential for troubleshooting, designing resilient applications, and succeeding in Kubernetes interviews.