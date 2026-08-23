# 07- Docker vs Kubernetes

## Overview

Docker and Kubernetes solve different problems at different layers of the application deployment lifecycle.

**Docker** provides containerization: packaging an application and its runtime dependencies into an isolated, portable execution unit.

**Kubernetes** provides container orchestration: scheduling, networking, scaling, service discovery, health management, rollout management, and recovery for containerized workloads across a cluster.

The common misconception is:

```text
Docker vs Kubernetes
```

as if they were competing technologies.

A more accurate relationship is:

```text
Application
    |
    v
Docker
    |
    v
Container Image
    |
    v
Container Runtime
    |
    v
Kubernetes
    |
    v
Cluster of Compute Nodes
```

Docker can be used without Kubernetes. Kubernetes can run containers without requiring Docker Engine as the node runtime. Modern Kubernetes commonly uses a CRI-compatible runtime such as `containerd` or CRI-O.

For backend system design, the important question is not:

> "Should I use Docker or Kubernetes?"

It is:

> "Do I need container packaging only, or do I need a control plane that continuously manages a distributed set of workloads?"

---

## Containerization

### What It Is

A container packages an application together with the dependencies required to execute it.

For a Python backend:

```text
Container Image
├── Python runtime
├── Application code
├── Python dependencies
├── OS libraries
└── Startup configuration
```

A Dockerfile might look like:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
```

The resulting image can be executed consistently across development, CI, staging, and production environments.

---

## Why Containers Exist

Without containerization, deployment often depends heavily on the underlying host:

```text
Server
├── Python version
├── System packages
├── Application dependencies
├── Environment configuration
└── Runtime configuration
```

Different hosts can produce different behavior.

Containers reduce environmental differences:

```text
                Same Image
                    |
       +------------+------------+
       |            |            |
       v            v            v
   Developer       CI         Production
```

This improves:

- reproducibility
- deployment consistency
- dependency isolation
- rollback capability
- CI/CD reliability
- developer experience

Containerization does not automatically make an application scalable or highly available.

---

## Docker Architecture

A simplified Docker architecture is:

```mermaid
flowchart LR
    Developer[Developer]
    CLI[Docker CLI]
    Engine[Docker Engine]
    Image[Container Image]
    Container[Running Container]
    Registry[Container Registry]

    Developer --> CLI
    CLI --> Engine
    Engine --> Image
    Image --> Container
    CLI --> Registry
    Registry --> Engine
```

Docker commonly consists of:

- Docker CLI
- Docker Engine
- image builder
- image registry
- containers
- volumes
- networks

The Docker image is immutable application packaging. A container is a running instance of that image.

---

## Container Image vs Container

| Concept | Description |
|---|---|
| Image | Immutable package used to create containers |
| Container | Running instance of an image |
| Registry | Repository for storing and distributing images |
| Dockerfile | Instructions for building an image |
| Volume | Persistent storage mechanism |
| Network | Connectivity mechanism between containers |

A single image can create many containers:

```text
                Python API Image
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
    Container 1    Container 2    Container 3
```

---

## Docker Compose

Docker Compose is useful when multiple containers must run together.

A backend application might contain:

```text
Django/FastAPI
      |
      +---- PostgreSQL
      |
      +---- Redis
      |
      +---- Celery Worker
```

A simplified Compose configuration:

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: application
      POSTGRES_USER: application
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

  redis:
    image: redis:8

  worker:
    build: .
    command: celery -A config worker --loglevel=INFO
    depends_on:
      - redis
      - postgres
```

Compose is particularly useful for:

- local development
- integration testing
- small deployments
- development environments
- reproducing multi-service architectures

Compose does not provide the full distributed orchestration capabilities of Kubernetes.

---

## Kubernetes

### What It Is

Kubernetes is a container orchestration platform designed to manage workloads across a cluster.

Instead of manually running:

```text
docker run ...
docker run ...
docker run ...
```

Kubernetes maintains a desired state.

For example:

```text
Desired state:
3 API replicas
```

If one replica crashes:

```text
Before:
API  API  API

Crash:
API  X    API

Kubernetes:
API  API  API
```

The scheduler and controllers work toward restoring the desired state.

---

## Why Kubernetes Exists

Running containers manually becomes increasingly difficult as the number of workloads grows.

A production platform may need:

- dozens or hundreds of services
- multiple replicas
- rolling deployments
- automatic recovery
- service discovery
- load balancing
- horizontal scaling
- configuration management
- secrets
- health checks
- resource limits
- node scheduling
- availability across failure domains

Kubernetes provides primitives for managing these requirements.

---

## Kubernetes Architecture

A simplified Kubernetes architecture:

```mermaid
flowchart TB
    User[Developer / CI/CD]

    subgraph ControlPlane[Control Plane]
        API[Kubernetes API Server]
        Scheduler[Scheduler]
        Controllers[Controllers]
        Store[(etcd)]
    end

    subgraph Cluster[Worker Nodes]
        Node1[Worker Node]
        Node2[Worker Node]
        Node3[Worker Node]
    end

    User --> API
    API --> Store
    API --> Scheduler
    API --> Controllers

    Scheduler --> Node1
    Scheduler --> Node2
    Scheduler --> Node3

    Controllers --> Node1
    Controllers --> Node2
    Controllers --> Node3
```

The major control-plane components include:

| Component | Responsibility |
|---|---|
| API Server | Entry point for Kubernetes API operations |
| etcd | Stores cluster state |
| Scheduler | Selects nodes for Pods |
| Controllers | Continuously reconcile desired and actual state |
| kubelet | Manages Pods on each worker node |
| Container runtime | Runs containers |
| kube-proxy / networking implementation | Supports service networking behavior |

Modern Kubernetes clusters typically use a CRI-compatible runtime such as `containerd`.

---

## Pods

A Pod is Kubernetes' basic scheduling unit.

A Pod can contain one or more containers that share:

- network namespace
- IP address
- local volumes
- lifecycle context

For most backend services:

```text
Pod
└── API Container
```

A multi-container Pod might look like:

```text
Pod
├── Application Container
└── Sidecar Container
```

Containers inside the same Pod are tightly coupled.

Do not use multiple containers in one Pod simply because they belong to the same application. They should generally have a lifecycle or networking relationship that justifies co-location.

---

## Deployment

A Kubernetes Deployment manages replicated stateless workloads.

Example:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend-api
  template:
    metadata:
      labels:
        app: backend-api
    spec:
      containers:
        - name: api
          image: registry.example.com/backend-api:1.4.2
          ports:
            - containerPort: 8000
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "1"
              memory: "512Mi"
```

The Deployment expresses:

```text
I want 3 replicas of backend-api running.
```

Kubernetes controllers continuously work toward that state.

---

## Service Discovery

Pods are ephemeral.

A Pod can be:

- deleted
- recreated
- rescheduled
- assigned a different IP

Therefore, applications should not depend directly on Pod IP addresses.

A Kubernetes Service provides a stable logical endpoint:

```text
Client
  |
  v
Service
  |
  +---- Pod 1
  |
  +---- Pod 2
  |
  +---- Pod 3
```

For example:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-api
spec:
  selector:
    app: backend-api
  ports:
    - port: 80
      targetPort: 8000
```

Applications can use:

```text
http://backend-api
```

instead of tracking individual Pod IPs.

---

## Docker vs Kubernetes

| Capability | Docker | Kubernetes |
|---|---|---|
| Container packaging | Yes | Uses container images |
| Run containers | Yes | Yes, through container runtime |
| Local development | Excellent | Possible but heavier |
| Multi-container development | Docker Compose | Kubernetes manifests |
| Scheduling | Limited | Yes |
| Self-healing | Limited | Yes |
| Service discovery | Docker networking | Kubernetes Services/DNS |
| Horizontal scaling | Limited/manual | Native |
| Rolling deployments | Limited | Native |
| Health management | Basic | Liveness/readiness/startup probes |
| Cluster management | No | Yes |
| Resource scheduling | Basic | Advanced |
| Secrets/configuration | Basic | Native primitives |
| Multi-node orchestration | Not the primary role | Core capability |
| Desired-state reconciliation | No | Core capability |
| Operational complexity | Lower | Significantly higher |

---

## Docker and Kubernetes Are Complementary

A common production pipeline looks like:

```text
Developer
   |
   v
Dockerfile
   |
   v
Docker Image
   |
   v
Container Registry
   |
   v
CI/CD
   |
   v
Kubernetes Deployment
   |
   v
Pods
```

For example:

```mermaid
flowchart LR
    Code[Git Repository]
    CI[CI Pipeline]
    Build[Build Image]
    Registry[Container Registry]
    CD[CD / Deployment]
    K8s[Kubernetes]
    Pods[Application Pods]

    Code --> CI
    CI --> Build
    Build --> Registry
    Registry --> CD
    CD --> K8s
    K8s --> Pods
```

Docker-style image tooling creates the deployable artifact. Kubernetes manages where and how that artifact runs.

---

## Kubernetes Desired State

One of Kubernetes' most important architectural concepts is reconciliation.

Suppose the desired state is:

```yaml
replicas: 3
```

Actual state:

```text
Pod 1 -> Running
Pod 2 -> Running
Pod 3 -> CrashLoopBackOff
```

A controller observes:

```text
Desired = 3
Actual  = 2 healthy
```

It works toward:

```text
Desired = 3
Actual  = 3
```

This is fundamentally different from simply executing a deployment command once.

Kubernetes continuously manages the state.

---

## Self-Healing

Self-healing is one of Kubernetes' major advantages.

Consider:

```text
Deployment
   |
   +---- Pod A
   +---- Pod B
   +---- Pod C
```

If Pod B crashes:

```text
Pod A
Pod B X
Pod C
```

The controller detects the discrepancy and creates another Pod:

```text
Pod A
Pod C
Pod D
```

However, Kubernetes cannot automatically fix application-level bugs.

If every newly created Pod crashes because of a bad release:

```text
Deployment
   |
   +---- Pod -> Crash
   +---- Pod -> Crash
   +---- Pod -> Crash
```

Kubernetes can repeatedly restart the workload, but the underlying software defect still requires remediation or rollback.

---

## Health Checks

Kubernetes supports different types of probes.

### Liveness Probe

Determines whether the container should be restarted.

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
```

A liveness endpoint should generally verify that the process is capable of functioning, not that every downstream dependency is healthy.

### Readiness Probe

Determines whether the Pod should receive traffic.

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  periodSeconds: 5
```

A Pod can be alive but not ready.

For example:

```text
Process running
       |
       v
Database unavailable
       |
       v
Readiness = false
       |
       v
Remove Pod from traffic
```

### Startup Probe

Useful for applications that take significant time to initialize.

```yaml
startupProbe:
  httpGet:
    path: /health/startup
    port: 8000
  failureThreshold: 30
  periodSeconds: 10
```

This prevents liveness checks from prematurely restarting a slow-starting application.

---

## Horizontal Scaling

Kubernetes can scale stateless workloads horizontally.

```text
Low traffic:

API
 |
 +---- Pod 1


High traffic:

API
 |
 +---- Pod 1
 +---- Pod 2
 +---- Pod 3
 +---- Pod 4
```

A Horizontal Pod Autoscaler can use resource or custom metrics.

Example:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

CPU utilization alone is not always a good scaling signal.

For APIs, better signals can include:

- request rate
- request latency
- queue depth
- concurrent requests
- application-specific work backlog

---

## Resource Requests and Limits

Kubernetes scheduling depends heavily on resource requests.

```yaml
resources:
  requests:
    cpu: "250m"
    memory: "256Mi"
  limits:
    cpu: "1"
    memory: "512Mi"
```

Requests communicate expected resource requirements.

Limits define upper bounds.

Poorly chosen limits can cause operational problems.

For example:

```text
Memory limit too low
      |
      v
Container exceeds limit
      |
      v
OOMKilled
      |
      v
Pod restarts
```

Resource sizing should come from measurements rather than arbitrary values.

---

## Networking

A Kubernetes application typically has several networking layers:

```text
Internet
   |
   v
Load Balancer / Ingress
   |
   v
Kubernetes Service
   |
   v
Pod IP
   |
   v
Application Container
```

For internal communication:

```text
Order Service
     |
     v
order-service.default.svc.cluster.local
     |
     v
Service
     |
     v
Order Pods
```

Kubernetes DNS provides service discovery within the cluster.

---

## Ingress and API Gateways

Kubernetes Services expose workloads within or outside the cluster, but production HTTP routing often requires an ingress controller or gateway.

Typical architecture:

```text
Client
  |
  v
AWS Load Balancer
  |
  v
Ingress / Gateway
  |
  +---- /users  -> User Service
  |
  +---- /orders -> Order Service
  |
  +---- /items  -> Item Service
```

Nginx, AWS Load Balancer Controller, Envoy-based gateways, and other implementations can provide different routing capabilities.

Kubernetes itself is not automatically an API gateway.

---

## Docker Compose vs Kubernetes

| Scenario | Docker Compose | Kubernetes |
|---|---:|---:|
| Local development | Excellent | Usually excessive |
| Small multi-container application | Excellent | Possible |
| Production single-host deployment | Possible | Usually excessive |
| Multi-node workloads | Limited | Excellent |
| Auto-healing | Limited | Excellent |
| Autoscaling | Limited | Excellent |
| Rolling deployments | Limited | Excellent |
| Service discovery | Good for local environments | Strong |
| Operational complexity | Low | High |
| Learning curve | Low | High |

A useful development progression is:

```text
Docker
   |
   v
Docker Compose
   |
   v
Container Registry
   |
   v
Managed Kubernetes
```

Do not introduce Kubernetes simply because the application uses multiple containers.

---

## When Docker Is Enough

Docker is often sufficient when:

- one or a few services are deployed
- traffic is predictable
- deployments are relatively simple
- a managed platform handles orchestration
- the organization does not need Kubernetes-specific capabilities
- operational simplicity is a priority

Examples include:

```text
Docker
  |
  v
AWS ECS / Fargate
```

or:

```text
Docker
  |
  v
Managed container platform
```

In these architectures, Docker provides the container artifact while another service handles orchestration.

---

## When Kubernetes Is Justified

Kubernetes becomes more attractive when the organization needs:

- many independently deployed services
- sophisticated scheduling
- multiple replicas
- automated rollouts
- service discovery
- workload autoscaling
- workload isolation
- multi-node orchestration
- custom networking
- standardized platform engineering
- portability across Kubernetes environments

The organizational requirement matters as much as the technical requirement.

Kubernetes introduces substantial operational complexity.

---

## Stateful Workloads

Kubernetes is strongest for stateless workloads.

A Django or FastAPI API can generally be modeled as:

```text
Container
   |
   +---- Stateless application code
```

State should normally live outside the Pod:

```text
API Pods
   |
   +---- PostgreSQL
   +---- Redis
   +---- S3
   +---- Kafka
```

Stateful systems can run on Kubernetes using mechanisms such as StatefulSets and persistent volumes, but this requires substantially more operational consideration.

Examples:

- PostgreSQL
- Kafka
- Elasticsearch
- Redis

For many organizations, managed services are preferable for critical stateful infrastructure.

---

## Storage

Containers are generally ephemeral.

Writing important data into a container filesystem is unsafe because the container can disappear.

Bad architecture:

```text
API Container
    |
    v
Local filesystem
    |
    X
Container deleted
    |
    X
Data lost
```

Better:

```text
API
 |
 +---- PostgreSQL
 +---- S3
 +---- EFS / Persistent Storage where appropriate
```

For Kubernetes, persistent storage can be exposed through PersistentVolumes and PersistentVolumeClaims.

---

## Configuration and Secrets

Do not bake production secrets into Docker images.

Bad:

```dockerfile
ENV DATABASE_PASSWORD=super-secret-password
```

Prefer external secret management.

In Kubernetes:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
type: Opaque
stringData:
  DATABASE_URL: postgresql://user:password@db.internal/app
```

For production AWS environments, consider integrating with services such as:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- IAM roles for service accounts / workload identity mechanisms

Kubernetes Secrets are not equivalent to a dedicated enterprise secret-management system.

---

## Security Considerations

Container security should be designed at multiple layers.

### Image Security

Use:

- minimal base images
- pinned dependencies
- vulnerability scanning
- trusted registries
- regular image updates
- multi-stage builds where useful

Example:

```dockerfile
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

USER 10001

CMD ["python", "-m", "src"]
```

Running as a non-root user reduces the impact of container compromise.

### Kubernetes Security

Use:

- RBAC
- network policies
- least-privilege service accounts
- Pod Security controls
- secret management
- resource limits
- image admission policies where appropriate
- encrypted communication
- restricted container capabilities

Never assume that being inside a Kubernetes cluster means a workload is trusted.

---

## Reliability and High Availability

For a production API:

```yaml
spec:
  replicas: 3
```

is only a starting point.

The Pods should also be distributed across failure domains where appropriate.

A resilient architecture may look like:

```text
                 Load Balancer
                      |
        +-------------+-------------+
        |             |             |
        v             v             v
      AZ-A          AZ-B          AZ-C
        |             |             |
      Pod 1         Pod 2         Pod 3
```

Use:

- multiple replicas
- Pod anti-affinity or topology spread constraints
- readiness probes
- graceful shutdown
- PodDisruptionBudgets
- multi-AZ node groups
- resilient downstream dependencies

Three replicas on the same node do not provide meaningful node-level high availability.

---

## Rolling Deployments

Kubernetes can gradually replace old Pods with new ones.

```text
Version 1:
v1 v1 v1

Deployment:
v1 v1 v2

Deployment:
v1 v2 v2

Deployment:
v2 v2 v2
```

This reduces deployment disruption.

However, safe rollouts require:

- readiness probes
- backward-compatible APIs
- database migration compatibility
- graceful shutdown
- appropriate rollout strategy
- observability
- rollback capability

A rolling deployment cannot fix an incompatible database migration.

---

## Database Migration Strategy

Suppose version 1 expects:

```text
column: name
```

and version 2 expects:

```text
column: full_name
```

During a rolling deployment, both versions may temporarily run.

A safe migration often uses an expand-and-contract approach:

```text
Phase 1
Add new column

Phase 2
Deploy application that writes both columns

Phase 3
Backfill data

Phase 4
Switch reads

Phase 5
Remove old column
```

This is particularly important when Kubernetes maintains multiple application replicas during deployment.

---

## Observability

A production Kubernetes platform should monitor both infrastructure and applications.

### Application Metrics

Track:

- request rate
- latency
- error rate
- saturation
- queue depth
- database latency
- cache hit rate

### Kubernetes Metrics

Track:

- Pod restarts
- CPU usage
- memory usage
- OOM kills
- node utilization
- scheduling failures
- replica availability
- deployment status

### Logs

Centralize application logs rather than depending on local container filesystems.

### Traces

Distributed tracing becomes increasingly valuable as the architecture grows:

```text
Client
 |
 v
API
 |
 +---- User Service
 |
 +---- Order Service
       |
       +---- PostgreSQL
```

A trace can connect these operations into one request path.

---

## Cost Considerations

Kubernetes has an operational and financial cost.

Costs may include:

- control-plane charges depending on platform
- worker nodes
- load balancers
- persistent storage
- networking
- observability infrastructure
- logging
- monitoring
- engineering time
- platform maintenance

A simple application may be cheaper and easier to operate on a managed container platform.

The total cost of ownership is more important than the raw infrastructure bill.

---

## Kubernetes on AWS

A common AWS architecture is:

```text
                    Internet
                       |
                       v
                Route 53 / DNS
                       |
                       v
               AWS Load Balancer
                       |
                       v
                  Kubernetes
                    /     \
                   /       \
             AZ-A           AZ-B
              |              |
           Pods            Pods
              \              /
               \            /
                 PostgreSQL
                RDS / Aurora
                       |
                     Redis
               ElastiCache
```

Amazon EKS provides managed Kubernetes control-plane capabilities while customers still manage or configure significant parts of the worker and workload infrastructure depending on the chosen operating model.

AWS-managed services can reduce operational burden:

| Requirement | Typical AWS Service |
|---|---|
| Kubernetes | EKS |
| Container registry | ECR |
| Relational database | RDS / Aurora |
| Object storage | S3 |
| Redis-compatible cache | ElastiCache |
| DNS | Route 53 |
| Load balancing | ELB / ALB / NLB |
| Secrets | Secrets Manager |
| Metrics/logging | CloudWatch and ecosystem tooling |

---

## CI/CD Pipeline

A production deployment pipeline might be:

```mermaid
flowchart LR
    Git[Git Push]
    Test[Tests]
    Build[Build Container]
    Scan[Security Scan]
    Push[Push to Registry]
    Deploy[Deploy]
    Rollout[Rolling Rollout]
    Verify[Health Verification]

    Git --> Test
    Test --> Build
    Build --> Scan
    Scan --> Push
    Push --> Deploy
    Deploy --> Rollout
    Rollout --> Verify
```

Example image workflow:

```bash
docker build -t backend-api:${GIT_SHA} .
docker push registry.example.com/backend-api:${GIT_SHA}
```

Use immutable image tags such as Git commit SHAs rather than relying exclusively on:

```text
latest
```

Immutable tags make deployments and rollbacks easier to reason about.

---

## Operational Complexity

Docker:

```text
Developer
   |
   v
Image
   |
   v
Container
```

Kubernetes:

```text
Developer
   |
   v
Image
   |
   v
Registry
   |
   v
Deployment
   |
   v
Scheduler
   |
   v
Nodes
   |
   v
Pods
   |
   v
Services
   |
   v
Ingress
   |
   v
Autoscaler
   |
   v
Monitoring
```

Kubernetes solves more problems, but therefore introduces more concepts and more operational failure modes.

This is an important architectural trade-off.

---

## Common Mistakes

### Treating Kubernetes as a Replacement for Docker

Kubernetes is an orchestration platform, not simply a more powerful Docker command.

### Using Kubernetes for Every Application

A small application may not justify the operational complexity.

### Running Databases in Kubernetes Without a Reason

Stateful workloads require additional operational expertise.

Managed databases are often simpler.

### Using `latest` in Production

Mutable image tags make deployments difficult to reproduce.

Prefer immutable version identifiers.

### Running Everything as Root

Containers should use a non-root user whenever possible.

### Ignoring Resource Requests

Without appropriate requests, scheduling and autoscaling behavior can become unpredictable.

### Missing Readiness Probes

A running process is not necessarily ready to serve traffic.

### Treating Liveness as Dependency Health

If a database is temporarily unavailable, restarting every API Pod may make the outage worse.

### Storing State Inside Containers

Containers are disposable. Persistent application state belongs in durable infrastructure.

### Assuming Three Replicas Means High Availability

If all three replicas run on one node or one failure domain, the architecture still has a major single point of failure.

### Overusing Sidecars

Sidecars can provide useful capabilities, but every additional container increases resource consumption and operational complexity.

---

## Interview Traps

### "Kubernetes Runs Docker Containers"

Historically common terminology, but technically incomplete.

Kubernetes uses the Container Runtime Interface and can run containers through runtimes such as `containerd` and CRI-O.

### "Docker Is an Orchestrator"

Docker provides container tooling. Docker Swarm is Docker's orchestration technology, but Docker Engine itself should not be treated as equivalent to Kubernetes.

### "Kubernetes Automatically Makes Applications Highly Available"

Kubernetes provides primitives for high availability, but the application architecture still needs:

- replicas
- proper scheduling
- resilient dependencies
- health checks
- graceful shutdown
- failure-domain distribution

### "Pods Are Virtual Machines"

Pods are not VMs.

They are Kubernetes scheduling and execution units built around containers and shared namespaces/resources.

### "A Deployment Is a Pod"

A Deployment manages ReplicaSets, which manage Pods.

Conceptually:

```text
Deployment
    |
    v
ReplicaSet
    |
    v
Pods
```

### "Kubernetes Autoscaling Means Adding Servers"

There are multiple scaling layers:

```text
HPA
 |
 v
More Pods
 |
 v
Cluster capacity exhausted
 |
 v
Node autoscaling
 |
 v
More Nodes
```

Pod scaling and node scaling are different mechanisms.

---

## Decision Framework

Use the following questions before choosing the platform.

| Question | Docker / Compose | Kubernetes |
|---|---|---|
| Is this primarily local development? | Strong choice | Usually unnecessary |
| Is the workload small? | Strong choice | Potentially excessive |
| Do we need multiple replicas? | Possible | Strong choice |
| Do we need automated scheduling? | No | Yes |
| Do we need sophisticated autoscaling? | Limited | Strong choice |
| Do we need rolling deployments? | Limited | Strong choice |
| Do we need cluster-wide service discovery? | Limited | Strong choice |
| Does the team have Kubernetes expertise? | Not required | Important |
| Is operational simplicity a priority? | Strong choice | Weaker |
| Is there a large microservice platform? | Possible | Often appropriate |
| Can a managed container platform provide orchestration? | Often enough | May avoid Kubernetes |

A senior engineer should treat operational complexity as a first-class architecture constraint.

---

## Production Architecture Guidelines

For a typical Python backend, a reasonable progression is:

```text
Stage 1
Django / FastAPI
        |
        v
Docker
```

Then:

```text
Stage 2
Django / FastAPI
        |
        v
Docker Compose
        |
        +---- PostgreSQL
        +---- Redis
```

Then, when scale and organizational requirements justify it:

```text
Stage 3

                    Load Balancer
                         |
                         v
                    Kubernetes
                   /    |    \
                  /     |     \
               API    Worker   Consumer
                |       |        |
                +-------+--------+
                        |
                  Managed Services
                /        |        \
          PostgreSQL    Redis     Kafka
```

The progression should be driven by requirements rather than technology popularity.

---

## Practical Checklist

Before adopting Kubernetes, verify:

- [ ] The application actually requires orchestration.
- [ ] The team can operate Kubernetes reliably.
- [ ] Container images are reproducible and immutable.
- [ ] Images are scanned for vulnerabilities.
- [ ] Containers run as non-root where practical.
- [ ] Resource requests and limits are defined.
- [ ] Readiness, liveness, and startup probes are appropriate.
- [ ] Application state is stored outside Pods.
- [ ] Secrets are managed securely.
- [ ] Multiple replicas are used where required.
- [ ] Pods are distributed across appropriate failure domains.
- [ ] Rolling deployments are tested.
- [ ] Database migrations are deployment-safe.
- [ ] Logs, metrics, and traces are centralized.
- [ ] Autoscaling signals reflect actual workload demand.
- [ ] Graceful shutdown is implemented.
- [ ] CI/CD uses immutable image versions.
- [ ] Rollback procedures are tested.
- [ ] Disaster recovery requirements are documented.
- [ ] Kubernetes operational cost is justified by the workload.

## Key Takeaways

- **Docker packages applications into portable containers; Kubernetes orchestrates containerized workloads across distributed infrastructure.**
- **Docker and Kubernetes are complementary rather than direct alternatives: Docker-style images provide deployment artifacts while Kubernetes manages scheduling, scaling, networking, health, and lifecycle.**
- **Kubernetes should be introduced when orchestration requirements justify its operational complexity; small applications often benefit more from simpler managed container platforms.**
- **Production Kubernetes requires deliberate design for resource limits, health probes, networking, secrets, security, observability, failure-domain distribution, deployment safety, and graceful shutdown.**
- **High availability and scalability are architectural properties, not automatic consequences of using Kubernetes; replicas, resilient dependencies, autoscaling, and failure-domain-aware scheduling must be designed explicitly.**