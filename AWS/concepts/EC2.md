# AWS EC2 — Interview Ready Notes

## Amazon EC2 (Elastic Compute Cloud)

### Definition
Amazon EC2 is AWS’s Infrastructure-as-a-Service (IaaS) offering that allows users to provision and manage virtual servers in the cloud.

### Core Capabilities
- Launch virtual machines
- Attach scalable storage
- Configure networking and security
- Auto scaling
- Load balancing

### Common Use Cases
- Hosting web applications
- Backend APIs
- Microservices
- CI/CD runners
- Databases
- Batch processing

---

# EC2 Architecture Components

| Component | Purpose |
|---|---|
| EC2 Instance | Virtual machine |
| EBS | Persistent block storage |
| Security Group | Virtual firewall |
| AMI | Machine template |
| Key Pair | Secure SSH authentication |
| Elastic IP | Static public IP |
| User Data | Bootstrap automation script |

---

# EC2 Instance Naming Convention

Example:
m5.2xlarge

| Part | Meaning |
|---|---|
| m | Instance family/class |
| 5 | Generation/version |
| 2xlarge | Instance size |

### Key Insight
- Newer generations provide better performance and cost optimization.
- Larger sizes provide more CPU, RAM, and networking capacity.

---

# EC2 Instance Types

## 1. General Purpose Instances

### Definition
Balanced compute, memory, and networking resources.

### Characteristics
- Cost-effective
- Flexible
- Suitable for most workloads

### Common Families
- T-series
- M-series

### Use Cases
- Web servers
- REST APIs
- Development environments
- Small databases
- Backend applications

### Example
t2.micro, t3.micro, m5.large

---

## 2. Compute Optimized Instances

### Definition
Instances optimized for CPU-intensive workloads.

### Characteristics
- High-performance processors
- Better compute throughput

### Common Families
- C-series

### Use Cases
- Scientific computing
- Machine learning inference
- Gaming servers
- Media transcoding
- High-performance APIs

### Example
c5.large, c6g.large

---

## 3. Memory Optimized Instances

### Definition
Instances designed for memory-intensive workloads.

### Characteristics
- High RAM capacity
- Fast in-memory processing

### Common Families
- R-series
- X-series

### Use Cases
- Redis/Memcached
- Large relational databases
- Big data analytics
- Real-time processing

### Example
r5.large, r6g.large

---

## 4. Storage Optimized Instances

### Definition
Instances optimized for high disk throughput and low latency storage operations.

### Characteristics
- High IOPS
- Fast sequential read/write operations

### Common Families
- I-series
- D-series

### Use Cases
- OLTP systems
- NoSQL databases
- Data warehousing
- Distributed file systems

### Example
i3.large, d2.large

---

# EC2 Purchasing Options

## 1. On-Demand Instances

### Definition
Pay-as-you-go pricing model.

### Advantages
- No long-term commitment
- Flexible
- Easy to scale

### Best For
- Development
- Testing
- Short-term workloads

---

## 2. Reserved Instances

### Definition
Long-term reservation of EC2 capacity for discounted pricing.

### Duration
- 1 year
- 3 years

### Advantages
- Significant cost savings

### Best For
- Stable production workloads

---

## 3. Savings Plans

### Definition
Commitment-based pricing model offering flexibility across instance families.

### Advantages
- Flexible
- Lower cost than On-Demand

### Best For
- Predictable cloud usage

---

## 4. Spot Instances

### Definition
Unused AWS capacity offered at heavily discounted prices.

### Advantages
- Very low cost

### Limitations
- AWS can terminate instances anytime

### Best For
- Batch jobs
- Fault-tolerant workloads
- Data processing

---

## 5. Dedicated Hosts

### Definition
Entire physical server dedicated to a single customer.

### Use Cases
- Compliance requirements
- License-bound applications

---

## 6. Dedicated Instances

### Definition
Instances running on isolated hardware.

---

## 7. Capacity Reservations

### Definition
Reserve EC2 capacity in a specific Availability Zone.

### Best For
- Mission-critical applications

---

# EC2 Sizing Parameters

## CPU (vCPU)

### Definition
Virtual CPU cores allocated to the instance.

### Important For
- Parallel processing
- Compute-heavy applications

---

## RAM

### Definition
Temporary memory used during execution.

### Important For
- Caching
- Databases
- Large application workloads

---

## Storage

## EBS (Elastic Block Store)

### Definition
Persistent block storage attached to EC2.

### Characteristics
- Network attached
- Persistent after reboot
- Scalable

### Use Cases
- OS storage
- Databases
- Application storage

---

## EFS (Elastic File System)

### Definition
Managed shared file system for multiple EC2 instances.

### Characteristics
- Shared storage
- Scalable
- Distributed filesystem

### Use Cases
- Shared media uploads
- Kubernetes shared storage

---

## Instance Store

### Definition
Temporary physical storage attached directly to host machine.

### Characteristics
- Extremely fast
- Data lost after instance stop/termination

### Use Cases
- Caching
- Temporary processing

---

## IOPS (Input/Output Operations Per Second)

### Definition
Measure of disk read/write performance.

### Important For
- Databases
- High transaction systems

### Example
gp3 EBS provides:
- Baseline 3000 IOPS

---

## Networking

### Components
- Public IP
- Private IP
- Bandwidth
- Network throughput

### Important For
- API performance
- Distributed systems
- Load balancing

---

## Security Groups

### Definition
Virtual firewall controlling inbound and outbound traffic for EC2 instances.

### Characteristics
- Stateful
- Attached at instance level
- Region + VPC scoped

---

## Inbound Rules

### Definition
Controls incoming traffic to EC2.

### Example
| Port | Purpose |
|---|---|
| 22 | SSH |
| 80 | HTTP |
| 443 | HTTPS |

---

## Outbound Rules

### Definition
Controls outgoing traffic from EC2.

### Default Behavior
- All outbound traffic allowed

---

## Important Security Group Concepts

- All inbound traffic blocked by default
- Multiple EC2 instances can share same SG
- Best practice: separate SG for SSH access
- SG operates outside EC2 instance

---

## Troubleshooting

### Connection Timeout
Usually indicates:
- Security group issue
- NACL issue
- Network routing problem

### Connection Refused
Usually indicates:
- Application not running
- Service not listening on port

---

## EC2 User Data

### Definition
Bootstrap script executed during instance startup.

### Purpose
Automate initial server configuration.

### Common Tasks
- Install packages
- Update OS
- Configure services
- Pull application code

### Important Note
Typically runs only during first boot.

### Example
```bash
#!/bin/bash
yum update -y
yum install docker -y
systemctl start docker
```

---

## Common Ports

| Port | Protocol | Purpose |
|---|---|---|
| 22 | SSH | Secure remote login |
| 21 | FTP | File transfer |
| 22 | SFTP | Secure file transfer |
| 80 | HTTP | Unsecured web traffic |
| 443 | HTTPS | Secure web traffic |
| 3389 | RDP | Windows remote desktop |

---

## SSH Access to EC2

### Requirements
- Public IP
- Correct username
- Matching PEM key
- Port 22 open in SG

### Common Usernames

| AMI | Username |
|---|---|
| Amazon Linux | ec2-user |
| Ubuntu | ubuntu |
| Debian | admin |
| CentOS | centos |

---

## Key Pair

### Definition
Authentication mechanism for secure EC2 access.

### Components
- Public key stored in AWS
- Private key (.pem) stored locally

### Best Practices
- Never commit PEM files to GitHub
- Restrict PEM file permissions
- Store securely

---

## Elastic IP

### Definition
Static public IPv4 address for EC2.

### Use Cases
- Stable server endpoints
- Production deployments

---

# Interview-Level Comparisons

## EBS vs Instance Store

| Feature | EBS | Instance Store |
|---|---|---|
| Persistence | Persistent | Temporary |
| Speed | Moderate | Very Fast |
| Network Attached | Yes | No |
| Best For | Databases | Cache/temp data |

---

## Security Group vs NACL

| Feature | Security Group | NACL |
|---|---|---|
| Level | Instance | Subnet |
| Stateful | Yes | No |
| Allow/Deny | Allow only | Allow & Deny |

---

## Real-world Recommendations

| Use Case | Recommended Instance |
|---|---|
| Small backend app | t2.micro |
| Production API | t3.medium |
| ML workloads | c5.large |
| Redis cache | r5.large |
| Heavy DB | i3.large |

---

## Important Interview Points

- EC2 is region-specific.
- Security Groups are stateful.
- EBS is persistent storage.
- User Data automates bootstrapping.
- Spot instances are interruptible.
- T-series instances are burstable.
- Public subnet instances can have public IPs.
- Private subnet instances require NAT for internet access.

---

## Quick Revision Summary

| Concept | One-Line Explanation |
|---|---|
| EC2 | Virtual machine in AWS |
| AMI | Machine template |
| EBS | Persistent disk |
| EFS | Shared filesystem |
| Security Group | Instance firewall |
| User Data | Startup automation script |
| IOPS | Disk performance metric |
| Spot Instance | Cheap interruptible VM |
| Elastic IP | Static public IP |
| Key Pair | SSH authentication mechanism |
