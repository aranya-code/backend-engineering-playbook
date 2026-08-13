# EFS (Elastic File System)

## Definition

A fully managed, elastic **NFS (Network File System)** designed to be mounted concurrently by many EC2 instances (and other compute, like Lambda and ECS/EKS) across multiple Availability Zones simultaneously — a genuine distributed filesystem, not a shared block device.

## Core Characteristics

- **Multi-AZ, multi-client by design** — unlike EBS Multi-Attach (a narrow exception requiring the application to coordinate writes itself), EFS is built from the ground up as a real distributed filesystem handling concurrent access from many clients correctly
- **Elastic** — storage capacity grows and shrinks automatically as files are added and removed; there's no volume size to provision or manage ahead of time
- **Fully managed** — AWS handles the underlying distributed storage infrastructure entirely

## Performance Modes

| Mode | Best For |
|---|---|
| General Purpose (default) | The right choice for the vast majority of workloads — lowest per-operation latency |
| Max I/O | Very high levels of aggregate throughput/operations across thousands of concurrent clients, at the cost of slightly higher per-operation latency — a narrow, specific use case |

## Throughput Modes

| Mode | Behavior |
|---|---|
| Bursting | Throughput scales with the amount of data stored, with the ability to burst above baseline using credits — similar in spirit to T-series CPU credits |
| Provisioned | Throughput is set independently of storage size, for workloads needing high throughput on a small amount of data |
| Elastic | Automatically scales throughput up or down based on actual workload activity, without needing to provision or predict a specific level — the current recommended default for unpredictable workloads |

## Storage Classes

EFS supports **lifecycle management**, automatically moving files between storage classes based on access patterns — Standard (frequent access) down to Infrequent Access (IA) tiers, meaningfully reducing cost for data that's written once and rarely read again, without any change to the application's access pattern or file paths.

## EFS Access Points

Application-specific entry points into a shared EFS filesystem, each with its own enforced POSIX user/group identity and a specific root directory within the filesystem. This lets multiple applications safely share one EFS filesystem while each seeing only its own designated subdirectory, with permissions enforced at the access point level — a common pattern for multi-tenant or multi-application shared storage.

## EBS vs. EFS

| Feature | EBS | EFS |
|---|---|---|
| Mount target | Single instance (or Multi-Attach io1/io2, narrowly) | Many instances, many AZs, concurrently |
| Availability Zone | Single AZ | Spans multiple AZs natively |
| Capacity management | Manually provisioned/resized | Fully elastic, automatic |
| Protocol | Block-level | NFS (file-level) |
| Typical cost | Cheaper per GB | More expensive per GB, offset by IA storage classes for cold data |
| Best use | Databases, boot volumes | Shared media, container persistent volumes, multi-instance shared state |

## Use Cases

- A shared uploads/media directory across a fleet of web servers behind a load balancer
- Kubernetes (EKS) or ECS persistent volumes shared across multiple pods/tasks
- Shared configuration or content that multiple, independently-scaling services need concurrent access to

## Senior-Level Considerations

- EFS is the right default answer for "I need storage multiple instances can all write to concurrently" — reaching for EBS Multi-Attach instead almost always indicates a misunderstanding of what Multi-Attach actually guarantees (attachment, not write coordination)
- Elastic throughput mode has largely reduced the historical need to carefully model Bursting-mode credit behavior in advance, similar to how T-series CPU credits require monitoring — for new EFS filesystems today, Elastic throughput is usually the simplest, safest default unless cost modeling specifically favors Provisioned for a known, steady workload
- Lifecycle management to IA storage classes is a straightforward, low-effort cost optimization for any EFS filesystem holding data with a genuine "hot then cold" access pattern (logs, historical uploads) — worth enabling by default rather than only after noticing a large storage bill
