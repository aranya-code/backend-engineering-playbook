# EC2 Basics

# What is Amazon EC2?

Amazon EC2 (Elastic Compute Cloud) is AWS's core Infrastructure-as-a-Service (IaaS) offering. It provides resizable virtual servers (instances) in the cloud, giving you full OS-level control over compute resources.

EC2 is the foundational building block of AWS. Almost every AWS service — from ECS to RDS to Lambda — runs on EC2 infrastructure under the hood.

---

# EC2 Architecture

```text
AWS Region (e.g., us-east-1)
│
├── Availability Zone (us-east-1a)
│   │
│   ├── Physical Host (Nitro System)
│   │   ├── Hypervisor (Nitro Hypervisor)
│   │   │   ├── EC2 Instance (your virtual machine)
│   │   │   │   ├── vCPUs (virtual CPUs allocated from host)
│   │   │   │   ├── RAM (memory allocated from host)
│   │   │   │   ├── ENI (Elastic Network Interface → private IP, SG)
│   │   │   │   ├── EBS Volume (network-attached persistent storage)
│   │   │   │   └── Instance Store (local NVMe, if supported)
│   │   │   └── ...other instances on same host
│   │   └── Nitro Cards (offload networking, EBS, monitoring)
│   │
│   └── ...more hosts
│
├── Availability Zone (us-east-1b)
│   └── ...
└── ...
```

---

# Core Components

| Component | Purpose | Key Detail |
|-----------|---------|------------|
| EC2 Instance | The virtual machine itself | Runs on Nitro or Xen hypervisor |
| AMI | Amazon Machine Image — OS + software blueprint | Used to launch instances, can be custom or AWS-provided |
| EBS Volume | Persistent network-attached block storage | AZ-scoped, survives instance stop/terminate |
| Security Group | Stateful virtual firewall at the ENI level | Allow rules only, no deny rules |
| Key Pair | SSH public/private key authentication | Private key never stored by AWS |
| Elastic IP | Static public IPv4 address | Free when attached to running instance |
| User Data | Bootstrap script executed on first launch | Runs as root, 16 KB limit |
| IAM Role | Permissions for the instance (via Instance Profile) | Replaces access keys on instances |
| Placement Group | Controls physical placement of instances | Cluster, Spread, or Partition strategies |

---

# EC2 Instance Lifecycle

```text
                    ┌──────────┐
           launch   │          │   terminate
     ┌─────────────►│ pending  ├────────────────────────────────┐
     │              │          │                                │
     │              └────┬─────┘                                │
     │                   │                                      │
     │                   ▼                                      ▼
     │              ┌──────────┐     stop          ┌──────────────────┐
     │              │          ├──────────────┐     │                  │
     │              │ running  │              │     │  shutting-down   │
     │              │          │◄─────────┐   │     │                  │
     │              └────┬─────┘  start   │   │     └────────┬─────────┘
     │                   │                │   │              │
     │                   │ stop           │   │              ▼
     │                   ▼                │   │     ┌──────────────────┐
     │              ┌──────────┐          │   │     │                  │
     │              │          │          │   │     │   terminated     │
     │              │ stopping ├──────────┘   │     │                  │
     │              │          │              │     └──────────────────┘
     │              └────┬─────┘              │
     │                   │                    │
     │                   ▼                    │
     │              ┌──────────┐              │
     │              │          ├──────────────┘
     └──────────────┤ stopped  │
                    │          │
                    └──────────┘
```

**Key State Behaviors:**
- **Pending → Running**: Instance is booting. User Data executes. EBS volumes are attached. ENI gets an IP.
- **Running → Stopping**: Instance is shutting down. Public IPv4 is released (unless Elastic IP).
- **Stopped**: No compute charges. EBS charges continue. RAM contents are lost.
- **Stopped → Running (Start)**: May launch on a different physical host. Gets a new public IP.
- **Terminated**: Instance and root EBS volume (if delete-on-termination=true) are destroyed permanently.

---

# AMIs (Amazon Machine Images)

An AMI is a template containing the OS, application code, and configuration used to launch instances.

## AMI Types

| Type | Description | Use Case |
|------|-------------|----------|
| AWS-Provided | Amazon Linux 2023, Ubuntu, Windows Server | Quick starts, standard workloads |
| AWS Marketplace | Third-party software pre-installed (licensed) | Commercial software (Splunk, WordPress) |
| Community AMIs | Public AMIs from other users | Caution — verify trustworthiness |
| Custom AMIs | Your own images baked from a configured instance | Production deployments, golden images |

## Custom AMI Workflow

```text
1. Launch base instance (e.g., Amazon Linux 2023)
2. Install and configure software (Python, Nginx, app code)
3. Test thoroughly
4. Create AMI (Instance → Actions → Create Image)
   └── Creates EBS snapshots of all attached volumes
5. Launch new instances from custom AMI
   └── Boots in seconds (no install/config needed)
```

## Cross-Region AMI Copy
AMIs are region-scoped. To use an AMI in another region, you must copy it:
- Copy creates new EBS snapshots in the target region
- The copied AMI gets a new AMI ID
- Use case: multi-region deployments, disaster recovery

---

# Placement Groups

Placement groups control how EC2 instances are distributed across physical hardware.

## Cluster Placement Group

```text
┌─────────────────────────────────────┐
│     Single Rack / Low Latency       │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  │
│  │ i-1 │ │ i-2 │ │ i-3 │ │ i-4 │  │
│  └─────┘ └─────┘ └─────┘ └─────┘  │
│     10 Gbps+ inter-instance         │
└─────────────────────────────────────┘
```
- All instances on same rack, same AZ
- Lowest network latency (10–25 Gbps between instances)
- Risk: rack failure = all instances fail
- Use case: HPC, tightly-coupled distributed computing, ML training

## Spread Placement Group

```text
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Rack A   │  │ Rack B   │  │ Rack C   │
│ ┌─────┐  │  │ ┌─────┐  │  │ ┌─────┐  │
│ │ i-1 │  │  │ │ i-2 │  │  │ │ i-3 │  │
│ └─────┘  │  │ └─────┘  │  │ └─────┘  │
└─────────┘  └─────────┘  └─────────┘
```
- Each instance on a separate physical rack (separate power, network)
- Maximum 7 instances per AZ per placement group
- Use case: critical applications requiring HA (e.g., primary/secondary databases)

## Partition Placement Group

```text
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Partition 1   │  │ Partition 2   │  │ Partition 3   │
│ ┌───┐ ┌───┐  │  │ ┌───┐ ┌───┐  │  │ ┌───┐ ┌───┐  │
│ │i-1│ │i-2│  │  │ │i-3│ │i-4│  │  │ │i-5│ │i-6│  │
│ └───┘ └───┘  │  │ └───┘ └───┘  │  │ └───┘ └───┘  │
│ (Shared rack) │  │ (Shared rack) │  │ (Shared rack) │
└──────────────┘  └──────────────┘  └──────────────┘
  Isolated from      Isolated from      Isolated from
  other partitions   other partitions   other partitions
```
- Up to 7 partitions per AZ. Instances within a partition may share hardware.
- Partitions are on different racks (failure in Partition 1 won't affect Partition 2)
- Use case: distributed workloads that are partition-aware (Kafka, Cassandra, HDFS)

---

# EC2 Nitro System

The Nitro System is the modern hardware and software platform for EC2 instances, replacing the older Xen hypervisor.

**What Nitro Does:**
- Offloads networking, storage (EBS), and monitoring to dedicated Nitro Cards
- The hypervisor is extremely lightweight — nearly bare-metal performance
- Enables features: EBS encryption by default, enhanced networking (ENA), higher IOPS

**Why It Matters:**
- All modern instance types (M5, C5, R5, T3, and newer) are Nitro-based
- Required for some features: EBS Multi-Attach, io2 Block Express, bare metal instances
- Better price-performance than older Xen-based instances

---

# Hibernate vs Stop

| Behavior | Stop | Hibernate |
|----------|------|-----------|
| RAM contents | Lost | Saved to root EBS volume |
| Boot time | Full OS boot | Resume from RAM (faster) |
| Processes | Terminated | Preserved (continue where they left off) |
| Root volume | Must be EBS | Must be EBS, encrypted, large enough for RAM |
| Max duration | Unlimited | 60 days |
| Use case | Standard stop/start | Long-initialization apps (large in-memory caches) |

---

# Common Mistakes

- Using the default VPC and security group for production workloads.
- Not using IAM roles — instead putting access keys on EC2 instances.
- Launching all instances in a single AZ (no fault tolerance).
- Using Amazon Linux 1 or outdated AMIs with known vulnerabilities.
- Not baking custom AMIs — relying on User Data for complex installations (slow boot time).
- Forgetting that stopped instances still incur EBS charges.

---

# Key Takeaways

- EC2 provides full OS-level control over virtual machines running on AWS infrastructure.
- Modern instances run on the Nitro System which offloads networking/storage to dedicated hardware.
- AMIs are the deployment artifact — bake custom AMIs for fast, consistent launches.
- Placement Groups control physical placement: Cluster (latency), Spread (HA), Partition (distributed).
- Instance state transitions affect billing, IP addresses, and data persistence.
- Always use IAM roles (not access keys) and private subnets (not public) for production instances.

---
