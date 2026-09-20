# 02- Instance Types

## Overview

An EC2 instance type defines the compute characteristics available to an EC2 instance, including vCPUs, memory, networking capability, EBS bandwidth, and, for some families, local storage or accelerators.

Instance type selection is a capacity-planning decision. For backend workloads, the correct choice depends on the application's actual resource profile rather than simply choosing the largest or cheapest instance.

A Django API, FastAPI service, Celery worker, Kafka consumer, image-processing worker, and machine-learning workload can have very different resource requirements even when they run the same operating system.

The goal is to select an instance family and size that provides sufficient performance, predictable scaling behavior, and an acceptable cost profile.

---

## What an EC2 Instance Type Defines

An instance type describes a particular combination of virtualized hardware resources.

Typical characteristics include:

| Characteristic | What it represents |
|---|---|
| vCPUs | Virtual CPU capacity available to the instance |
| Memory | RAM available to applications |
| Network performance | Network throughput and packet-processing capability |
| EBS bandwidth | Maximum bandwidth available for EBS I/O |
| Instance storage | Local ephemeral storage when provided |
| Architecture | CPU architecture such as x86 or Arm |
| Accelerators | GPU or other specialized hardware on applicable families |
| Network interfaces | Supported network interface and networking capabilities |

The instance type is therefore more than a CPU/memory pair. Two instances with similar vCPU and memory counts can have materially different network, storage, architecture, and performance characteristics.

---

## Instance Type Naming

AWS instance types use a structured naming convention.

A simplified example is:

```text
m7i.2xlarge
```

The name can be interpreted conceptually as:

```text
m     -> instance family
7     -> generation
i     -> processor/platform characteristic
2xlarge -> size
```

The exact suffix semantics vary between families, so instance names should be interpreted using the AWS specifications for the particular family rather than assuming every suffix has the same meaning.

Common family categories include:

| Family category | Typical purpose |
|---|---|
| General purpose | Balanced compute and memory |
| Compute optimized | CPU-intensive workloads |
| Memory optimized | Memory-intensive workloads |
| Storage optimized | High-throughput or high-IOPS local-storage workloads |
| Accelerated computing | GPU and specialized accelerator workloads |

---

## General Purpose Instances

General purpose families provide a relatively balanced combination of compute, memory, networking, and storage capabilities.

They are commonly suitable for:

- Django applications
- FastAPI services
- REST APIs
- gRPC services
- Nginx
- Microservices
- CI/CD workloads
- Development environments
- Small to medium application servers
- General-purpose Celery workers

A typical backend architecture may start with a general-purpose family and then move to a more specialized family after observing actual workload behavior.

For example:

```text
                    Load Balancer
                    /           \
                   /             \
                  v               v
          General Purpose    General Purpose
              EC2                 EC2
               |                   |
           FastAPI             FastAPI
               |                   |
               +--------+----------+
                        |
                     PostgreSQL
```

The key advantage is flexibility. The limitation is that a balanced configuration may not be optimal when one resource is consistently the bottleneck.

---

## Compute Optimized Instances

Compute optimized families are designed for workloads where CPU capacity is the dominant requirement.

Typical examples include:

- CPU-heavy data processing
- High-throughput application servers
- Video or media processing
- Scientific computation
- Certain build workloads
- CPU-intensive Celery workers
- High-volume request processing

For example:

```text
                    Task Queue
                        |
                        v
              Compute-Optimized EC2
                 /      |      \
                v       v       v
             Worker  Worker  Worker
                |
             CPU-heavy
             processing
```

A compute-optimized instance is useful when monitoring shows sustained CPU pressure while memory remains sufficient.

Simply moving to a compute-optimized family is not a substitute for identifying inefficient application code.

---

## Memory Optimized Instances

Memory optimized families are designed for workloads requiring large amounts of RAM.

Typical workloads include:

- Large in-memory caches
- Memory-intensive data processing
- Large application working sets
- In-memory databases
- Analytics workloads
- Applications with large datasets retained in memory

For backend applications, memory pressure can come from:

- Large Python object graphs
- High worker concurrency
- Large response processing
- Caching
- Data transformation
- JVM-based services
- Large connection pools

For example, a Python service using multiple worker processes may consume significantly more memory than expected because each process maintains its own application state.

A useful sizing principle is:

```text
Memory requirement
    =
Application working set
+ Worker/process overhead
+ Runtime overhead
+ OS overhead
+ Safety margin
```

Do not size a memory-intensive service based only on its average memory usage. Account for traffic spikes and concurrency.

---

## Storage Optimized Instances

Storage optimized families target workloads requiring high-performance local storage.

Potential workloads include:

- High-throughput data processing
- Local caching
- Search workloads
- Large temporary datasets
- Distributed data-processing systems
- Applications specifically designed around local NVMe storage

Instance store is generally ephemeral. Data stored there should therefore be considered replaceable unless the application has an explicit replication and recovery strategy.

This makes storage-optimized instances different from simply attaching a large EBS volume.

```text
Storage Optimized EC2

        EC2
         |
   +-----+------+
   |            |
CPU/Memory   Local Storage
                |
             Ephemeral
```

If data must survive instance replacement, evaluate EBS, S3, or a managed data service instead.

---

## Accelerated Computing

Accelerated computing instances provide specialized hardware such as GPUs or other accelerators.

Typical workloads include:

- Machine learning inference
- Model training
- GPU-based computation
- Graphics processing
- Specialized scientific workloads

These instances can be significantly more expensive than general-purpose compute, so they should be selected only when the workload benefits from the accelerator.

A Python backend that merely performs ordinary API processing does not automatically benefit from GPU-backed instances.

---

## CPU Architecture

EC2 supports different processor architectures, including:

- x86
- Arm

AWS Graviton-based instances use Arm processors.

Architecture selection can affect:

- Application compatibility
- Container images
- Native Python packages
- Operating-system packages
- Compiled dependencies
- Performance
- Cost

For example, a Python application using packages with native extensions should be tested on the target architecture.

A Docker image built for x86 cannot necessarily run unchanged on an Arm-based EC2 environment.

A multi-platform container build may be required:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t example-api:latest \
  --push .
```

Before moving an existing production workload between architectures, validate:

- Base images
- Native dependencies
- Database drivers
- Python wheels
- Monitoring agents
- Security agents
- Third-party binaries

---

## Instance Size

Within an instance family, different sizes provide different resource levels.

Conceptually:

```text
small
  |
medium
  |
large
  |
xlarge
  |
2xlarge
  |
4xlarge
```

Larger sizes generally provide more resources, but the exact scaling characteristics depend on the family.

For production workloads, do not assume that doubling instance size will always double application throughput.

Performance can be constrained by:

- Application architecture
- Database latency
- Lock contention
- Network dependencies
- External APIs
- Storage performance
- Python concurrency model
- Connection limits
- Load-balancer behavior

---

## vCPUs and Backend Workloads

vCPUs represent virtual CPU capacity exposed to the instance.

For backend services, CPU requirements depend on the workload.

CPU-intensive workloads may include:

- JSON serialization at high volume
- Compression
- Encryption
- Image processing
- Data transformation
- CPU-heavy business logic
- Background workers

I/O-heavy workloads may spend significant time waiting on:

- PostgreSQL
- Redis
- S3
- External APIs
- Network services
- Disk operations

Increasing CPU capacity does not necessarily solve an I/O bottleneck.

For example:

```text
FastAPI
   |
   +--> CPU usage: 25%
   |
   +--> Database latency: high
```

Moving to an instance with twice as many CPUs may have little effect because the bottleneck is the database.

---

## Memory and Python Applications

Python backend services require careful memory planning because application processes can consume substantial memory under concurrency.

For example, a deployment might use:

```text
EC2 Instance
    |
    +-- Uvicorn/Gunicorn worker 1
    +-- Uvicorn/Gunicorn worker 2
    +-- Uvicorn/Gunicorn worker 3
    +-- Uvicorn/Gunicorn worker 4
    |
    +-- Nginx
    +-- Monitoring agents
    +-- OS
```

If each application worker consumes 500 MB under realistic load, four workers already require approximately:

```text
4 × 500 MB = 2 GB
```

Additional memory is required for the OS, Nginx, agents, temporary allocations, caches, and traffic spikes.

This is why worker count should not be chosen independently of instance memory.

---

## Network Performance

EC2 instance types have different networking capabilities.

Network performance matters for:

- High-throughput APIs
- gRPC services
- Kafka consumers/producers
- Service-to-service communication
- S3 transfers
- Database traffic
- Load-balanced applications

A service can have sufficient CPU and memory but still experience throughput limitations because of networking.

For distributed backend systems:

```text
EC2
 |
 +--> PostgreSQL
 +--> Redis
 +--> Kafka
 +--> S3
 +--> External APIs
```

The aggregate network workload can become significant.

When evaluating instance types, consider both bandwidth and packet-processing requirements rather than looking only at advertised maximum throughput.

---

## EBS Performance

EC2 instance types can have different EBS bandwidth capabilities.

This matters when applications depend heavily on EBS-backed storage.

For example:

```text
Application
     |
     v
EC2
     |
     v
EBS Volume
     |
     v
Database / Files / Processing
```

A high-performance EBS volume does not automatically mean the application can consume that performance.

The effective performance can be constrained by:

- EBS volume configuration
- EC2 EBS bandwidth
- IOPS
- Queue depth
- Application I/O pattern
- Operating-system configuration

Both the volume and the instance need to be evaluated.

---

## Burstable Instances

Burstable instances are designed for workloads whose CPU demand is generally moderate but periodically increases.

These instances use CPU credits to support burst behavior.

They can be useful for:

- Development environments
- Low-to-moderate traffic services
- Small internal applications
- Workloads with intermittent CPU spikes

They require more careful consideration for consistently CPU-intensive workloads.

A common mistake is deploying a continuously CPU-heavy production service on a burstable instance simply because its initial cost is lower.

Monitor CPU utilization and CPU credit behavior before relying on burstable capacity for production workloads.

---

## Selecting an Instance Type

A practical selection process should begin with workload characteristics.

### Identify the Workload

Determine whether the application is primarily:

- CPU-bound
- Memory-bound
- Network-bound
- Storage-bound
- Accelerator-bound
- Mixed

### Measure the Existing System

Collect:

- CPU utilization
- Memory utilization
- Network throughput
- Disk throughput
- Disk latency
- Request rate
- Request latency
- Error rate
- Worker utilization
- Queue depth

### Select Candidate Families

Choose one or more families that match the dominant bottleneck.

### Load Test

Test realistic traffic rather than synthetic CPU-only workloads.

### Compare Cost

Compare:

```text
Cost per instance
+
Associated storage
+
Network/data transfer
+
Load balancing
+
Monitoring
+
Expected scaling requirements
```

### Validate in Production

After deployment, continue monitoring. Instance selection is an operational decision, not a one-time configuration.

---

## Workload-to-Family Mapping

| Workload | Likely starting point | Main consideration |
|---|---|---|
| Django/FastAPI API | General purpose | Balanced CPU/memory |
| Nginx reverse proxy | General purpose | Network and connection volume |
| CPU-heavy Celery workers | Compute optimized | CPU utilization |
| Memory-heavy Python service | Memory optimized | Working-set size |
| Large in-memory cache | Memory optimized | RAM capacity |
| Local high-throughput processing | Storage optimized | Local I/O |
| ML inference | Accelerated computing | Accelerator utilization |
| Development server | General purpose or burstable | Cost and intermittent load |
| CI build workers | General purpose or compute optimized | Build CPU/memory profile |
| Kafka workload | Workload-dependent | Network, storage, CPU, memory |

These are starting points rather than universal recommendations.

---

## Instance Selection Example

Suppose a FastAPI service has the following production profile:

| Metric | Observation |
|---|---:|
| Average CPU | 35% |
| Peak CPU | 55% |
| Average memory | 70% |
| Peak memory | 88% |
| Network | Moderate |
| EBS I/O | Low |
| Request latency | Stable |

The primary concern is memory rather than CPU.

Moving to a significantly more CPU-heavy instance may not address the actual bottleneck.

A better approach is to:

1. Identify memory-consuming processes.
2. Check application worker count.
3. Investigate memory growth.
4. Measure peak memory under realistic load.
5. Evaluate a larger or memory-oriented instance.
6. Compare cost and performance.
7. Verify behavior under peak traffic.

This is an example of **evidence-based instance selection**.

---

## Instance Types and Auto Scaling

Instance type selection also affects horizontal scaling.

Suppose a service requires 8 vCPUs of total compute capacity.

You could deploy:

```text
Option A
2 × 4-vCPU instances
```

or:

```text
Option B
4 × 2-vCPU instances
```

The better architecture depends on:

- Failure isolation
- Application concurrency
- Load-balancer behavior
- Startup time
- Scaling granularity
- Cost
- Memory requirements
- Deployment strategy

Smaller instances can provide finer-grained scaling and smaller failure domains.

Larger instances can reduce management overhead and may provide better price/performance for some workloads.

There is no universal rule that one approach is always better.

---

## High Availability Considerations

Instance size and availability are separate concerns.

A very large instance does not automatically provide high availability.

For example:

```text
Incorrect assumption:

1 × very large EC2
        =
High availability
```

A more resilient design might use:

```text
                 Load Balancer
                 /           \
                v             v
          EC2 Instance A   EC2 Instance B
              AZ-A             AZ-B
```

The application can then tolerate the loss of one instance more effectively.

When selecting instance types, consider how the chosen size affects the number of instances required for normal operation and failure scenarios.

---

## Instance Type Selection and Kubernetes

When EC2 provides worker nodes for Kubernetes, instance selection becomes a node-capacity decision.

For example:

```text
EKS Cluster
    |
    +-- Node Group
          |
          +-- EC2
          +-- EC2
          +-- EC2
```

Node sizing affects:

- Pod density
- CPU requests
- Memory requests
- DaemonSet overhead
- Cluster autoscaling behavior
- Bin packing efficiency

An instance that looks inexpensive in isolation may become inefficient if Kubernetes schedules workloads poorly because of its CPU-to-memory ratio.

For containerized workloads, evaluate instance types based on the resource requests and limits of the workloads they will host.

---

## Instance Type Selection and Docker

Docker itself does not change the underlying EC2 capacity.

If an EC2 instance has:

```text
4 vCPUs
8 GB RAM
```

all containers running on the instance share those resources.

For example:

```text
EC2
 |
 +-- Nginx
 +-- FastAPI
 +-- Celery
 +-- Monitoring Agent
```

Resource limits should be considered where appropriate.

For production container workloads, avoid assuming that the host has unlimited resources simply because containers abstract the application environment.

---

## Instance Type Selection and Celery

Celery workers can have very different resource profiles depending on task behavior.

CPU-bound tasks may benefit from compute-optimized instances.

Memory-heavy tasks may require memory-optimized instances.

I/O-heavy tasks may not benefit significantly from additional CPU.

For example:

```text
Celery
 |
 +-- Image processing      -> CPU-heavy
 +-- Large CSV processing  -> CPU + memory
 +-- API synchronization   -> Network/I/O-heavy
 +-- Database processing   -> Database/I/O-dependent
```

A single worker node type may therefore be inefficient for unrelated task categories.

Separate worker pools can use different instance families when workload characteristics justify the additional operational complexity.

---

## Monitoring Instance Type Performance

After deployment, monitor both utilization and application outcomes.

Useful infrastructure signals include:

- CPU utilization
- CPU credit balance for burstable instances
- Network throughput
- EBS throughput
- EBS latency
- EBS queue behavior
- Memory utilization when collected
- Instance status checks

Application-level signals include:

- Requests per second
- p50/p95/p99 latency
- HTTP 5xx rate
- Worker saturation
- Queue depth
- Database latency
- Cache latency

A good instance type should support the required application performance with sufficient headroom.

---

## Right-Sizing

Right-sizing means selecting capacity appropriate to the workload.

Oversizing can result in:

- Unnecessary cost
- Low resource utilization
- Poor scaling efficiency

Undersizing can result in:

- High latency
- Resource exhaustion
- Increased error rates
- Frequent scaling events
- Poor reliability

The objective is not maximum utilization at all times.

Production systems need sufficient headroom for:

- Traffic spikes
- Background jobs
- Deployments
- Dependency latency
- Failures
- Scaling delays

---

## Cost Considerations

Instance cost should be evaluated together with operational behavior.

For example:

```text
Large Instance
    |
    +-- Lower instance count
    +-- Larger failure domain
    +-- Coarser scaling

Smaller Instances
    |
    +-- Higher instance count
    +-- Smaller failure domains
    +-- Finer scaling
```

The cheapest individual instance does not necessarily produce the lowest application cost.

Compare cost against:

- Throughput
- Latency
- Number of instances required
- Scaling behavior
- Failure recovery
- Operational complexity

For predictable long-running workloads, evaluate applicable commitment-based purchasing options.

For interruptible workloads, Spot Instances may be appropriate when the application can tolerate interruption.

---

## Common Mistakes

### Choosing the Largest Instance

More capacity does not automatically mean better architecture.

A large instance may hide inefficient code, poor database queries, or inappropriate concurrency.

### Choosing Only by vCPU

CPU is only one resource dimension.

Memory, networking, EBS bandwidth, architecture, and workload behavior must also be considered.

### Ignoring Architecture Compatibility

Moving from x86 to Arm can expose compatibility problems in:

- Native Python packages
- Docker images
- OS packages
- Monitoring agents
- Third-party binaries

Test the complete software stack before changing architecture.

### Ignoring Memory Headroom

A service operating at 90% memory utilization under normal traffic has little room for traffic spikes or temporary allocations.

### Treating Benchmark Results as Universal

A benchmark using synthetic CPU load does not necessarily represent a real API workload.

Benchmark the actual application path.

### Assuming Bigger Means Faster

An application may be constrained by PostgreSQL, Redis, network latency, or external APIs rather than EC2 CPU.

### Ignoring Scaling Granularity

One very large instance may provide less flexible scaling than several smaller instances behind a load balancer.

### Ignoring EBS and Network Limits

Selecting a high-performance EBS volume or a powerful application server does not guarantee that the complete EC2 configuration can sustain the desired I/O or network workload.

---

## Production Recommendations

For production instance selection:

- Start with the workload rather than the instance catalog.
- Identify the dominant resource bottleneck.
- Select an appropriate instance family.
- Validate CPU architecture compatibility.
- Load test realistic application traffic.
- Monitor CPU, memory, network, and storage behavior.
- Leave capacity headroom for normal traffic spikes.
- Evaluate horizontal scaling before simply increasing instance size.
- Use multiple Availability Zones for critical workloads.
- Re-evaluate instance sizing after significant workload changes.
- Include infrastructure and application metrics in capacity decisions.
- Compare cost per unit of useful application capacity, not only cost per instance.

---

## Interview Considerations

### Why not use the largest EC2 instance?

Because capacity should match the workload. Oversized instances increase cost and can create larger failure domains while failing to address bottlenecks outside CPU or memory.

### How do you choose between general purpose and compute optimized?

Measure the workload. If CPU is consistently the limiting resource while memory and other resources are sufficient, compute-optimized instances may be appropriate. A balanced workload may fit a general-purpose family better.

### When would you use a memory-optimized instance?

When the workload has a large memory working set or consistently experiences memory pressure that cannot be solved through application optimization or scaling.

### Does a larger instance guarantee higher API throughput?

No. API throughput can be constrained by databases, caches, network dependencies, storage, application locks, worker configuration, or external services.

### What should you consider when moving from x86 to Arm?

Validate the operating system, container images, native dependencies, Python packages, monitoring agents, third-party binaries, and application performance on the target architecture.

### How does instance size affect Auto Scaling?

Larger instances provide more capacity per node but result in coarser scaling increments. Smaller instances can provide finer-grained scaling and smaller failure domains, at the cost of potentially higher instance-management overhead.

---

## Key Takeaways

- EC2 instance types define a combination of CPU, memory, networking, storage, architecture, and other hardware characteristics; selecting by vCPU alone is insufficient.
- Choose the instance family based on the workload's dominant resource constraint and validate the choice using realistic application measurements.
- General-purpose, compute-optimized, memory-optimized, storage-optimized, and accelerated instances serve materially different workload profiles.
- Instance sizing should be considered together with horizontal scaling, Availability Zones, application architecture, and failure tolerance.
- Production right-sizing requires continuous monitoring of infrastructure utilization, application performance, scaling behavior, and cost.