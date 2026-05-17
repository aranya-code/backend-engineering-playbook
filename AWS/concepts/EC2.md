# AWS EC2 — Interview Ready Notes

## Amazon EC2 (Elastic Compute Cloud)

### Definition
Amazon EC2 is AWS’s core Infrastructure-as-a-Service (IaaS) offering. In simple terms, it's where we rent virtual servers in the cloud. After spending years building systems, I look at EC2 as the fundamental building block for any custom architecture when managed services (like Lambda or Fargate) don't give you enough control.

### Core Capabilities
- Launch virtual machines (giving you complete OS-level access)
- Attach scalable, persistent storage volumes
- Configure granular networking and security boundaries
- Auto scaling (crucial for handling unpredictable API traffic spikes)
- Load balancing (distributing traffic across multiple instances to ensure high availability)

### Common Use Cases
- Hosting web applications and heavy monolithic services
- Backend APIs (perfect for standard Django or DRF deployments)
- Microservices (when container orchestration on native EC2 is required)
- CI/CD runners (spinning up temporary build environments)
- Databases (when you need to self-manage instead of using RDS)
- Batch processing (handling large scheduled data ingestion jobs)

---

# EC2 Architecture Components

| Component | Purpose |
|---|---|
| EC2 Instance | The virtual machine itself. The actual compute muscle. |
| EBS | Persistent block storage. Think of this as the physical hard drive you plug into the server. |
| Security Group | Your instance-level virtual firewall. The first line of defense against unwanted traffic. |
| AMI | Amazon Machine Image. The blueprint or template (OS + pre-installed software) used to launch the instance. |
| Key Pair | Secure SSH authentication mechanism using public-key cryptography. Never lose the private key! |
| Elastic IP | A static public IP address that persists even if you stop and start the instance. |
| User Data | A bootstrap automation script that runs exactly once when the instance is first launched. Great for initial setup. |

---

# EC2 Instance Naming Convention

Example:
m5.2xlarge

| Part | Meaning |
|---|---|
| m | Instance family/class (indicates what it's optimized for) |
| 5 | Generation/version (higher is newer) |
| 2xlarge | Instance size (the amount of raw resources) |

### Key Insight
- Newer generations (like jumping from m4 to m5) almost always provide better performance, newer physical hardware, and surprisingly, cost optimization. Always default to the newest generation unless a specific legacy dependency prevents it.
- Larger sizes provide roughly double the CPU, RAM, and networking capacity of the size below them.

---

# EC2 Instance Types

## 1. General Purpose Instances

### Definition
A balanced ratio of compute, memory, and networking resources.

### Characteristics
- Cost-effective for standard workloads
- Flexible baseline performance
- Suitable for the vast majority of standard web architectures

### Common Families
- T-series (Burstable performance - accumulates CPU credits when idle, uses them when busy)
- M-series (Consistent, fixed performance)

### Use Cases
- Standard web servers
- REST APIs serving typical CRUD operations
- Development and staging environments
- Small, low-traffic databases
- General backend orchestration applications

### Example
t2.micro, t3.micro, m5.large

---

## 2. Compute Optimized Instances

### Definition
Instances heavily optimized for CPU-intensive workloads with a higher ratio of vCPUs to memory.

### Characteristics
- High-performance processors
- Better compute throughput for sustained heavy lifting

### Common Families
- C-series

### Use Cases
- Scientific computing and complex algorithmic problem-solving
- Machine learning inference
- Dedicated gaming servers
- Media transcoding (video/audio processing)
- High-performance APIs processing heavy payloads (e.g., transforming massive JSONs or CSVs)

### Example
c5.large, c6g.large

---

## 3. Memory Optimized Instances

### Definition
Instances designed to deliver fast performance for workloads that process large data sets in memory.

### Characteristics
- High RAM capacity
- Extremely fast in-memory processing capabilities

### Common Families
- R-series
- X-series (Extreme memory)

### Use Cases
- In-memory caches like Redis or Memcached
- Large relational databases
- Big data analytics
- Real-time processing
- Loading large vector databases (like ChromaDB or FAISS) entirely into memory for fast retrieval in RAG architectures.

### Example
r5.large, r6g.large

---

## 4. Storage Optimized Instances

### Definition
Instances optimized for high disk throughput and low latency local storage operations.

### Characteristics
- Extremely high IOPS (Input/Output Operations Per Second)
- Fast sequential read/write operations to local NVMe storage

### Common Families
- I-series
- D-series (Dense storage)

### Use Cases
- OLTP (Online Transaction Processing) systems
- High-performance NoSQL databases (Cassandra, MongoDB)
- Data warehousing
- Distributed file systems

### Example
i3.large, d2.large

---

# EC2 Purchasing Options

## 1. On-Demand Instances

### Definition
The classic pay-as-you-go pricing model, billed by the second (for Linux).

### Advantages
- Zero long-term commitment
- Ultimate flexibility (spin up, destroy, change types instantly)
- Easy to scale horizontally on short notice

### Best For
- Active development and debugging
- Testing new architectural patterns
- Short-term, unpredictable workloads

---

## 2. Reserved Instances

### Definition
A billing discount applied when you commit to reserving EC2 capacity for a long period.

### Duration
- 1 year
- 3 years (Steeper discount)

### Advantages
- Significant cost savings (can be up to 70% cheaper than On-Demand)

### Best For
- Stable, predictable production workloads. If you know that core API backend is going to be running 24/7 for the next year, reserve it.

---

## 3. Savings Plans

### Definition
A more modern, flexible commitment-based pricing model based on a guaranteed dollar-per-hour spend rather than specific instance types.

### Advantages
- Much more flexible than Reserved Instances (you can change instance families or regions depending on the plan)
- Lower cost than On-Demand

### Best For
- Predictable overall cloud usage where the underlying architecture might still evolve.

---

## 4. Spot Instances

### Definition
Bidding on unused, spare AWS capacity offered at heavily discounted prices.

### Advantages
- Extremely low cost (up to 90% discount)

### Limitations
- AWS can (and will) terminate the instances with a mere 2-minute warning if they need the capacity back.

### Best For
- Batch processing jobs
- Highly fault-tolerant, stateless worker queues (like a Celery worker pulling jobs from SQS)
- Massive data processing pipelines that can resume if interrupted

---

## 5. Dedicated Hosts

### Definition
An entire physical server dedicated exclusively for your use.

### Use Cases
- Strict compliance and regulatory requirements
- Bringing your own license (BYOL) for software bound to physical cores/sockets (e.g., old enterprise database licenses).

---

## 6. Dedicated Instances

### Definition
Instances running on hardware strictly isolated at the host hardware level from other AWS accounts, but you don't control the whole physical server.

---

## 7. Capacity Reservations

### Definition
Reserving pure compute capacity in a specific Availability Zone, ensuring the instances will actually be available to launch when you need them, regardless of term commitments.

### Best For
- Mission-critical applications where an "insufficient capacity" error during a scale-up event would be catastrophic.

---

# EC2 Sizing Parameters

## CPU (vCPU)

### Definition
Virtual CPU cores allocated to the instance. This represents the raw processing thread power.

### Important For
- Parallel processing architectures
- Compute-heavy, algorithmic applications

---

## RAM

### Definition
Temporary volatile memory used during execution.

### Important For
- Caching layers
- Databases keeping indexes in memory
- Holding large application contexts or machine learning models in state.

---

## Storage

## EBS (Elastic Block Store)

### Definition
Persistent block storage volumes attached to EC2 over the AWS network.

### Characteristics
- Network attached (meaning there is some inherent latency, though minor)
- Persistent after the EC2 instance is rebooted or stopped
- Highly scalable and snapshot-friendly

### Use Cases
- The primary OS boot drive
- Relational databases
- General application file storage

---

## EFS (Elastic File System)

### Definition
A fully managed, shared NFS file system designed to be mounted by multiple EC2 instances simultaneously.

### Characteristics
- Shared storage across instances and even across Availability Zones
- Automatically scales up and down as you add/remove files
- Distributed filesystem

### Use Cases
- Shared media uploads folder across a fleet of web servers
- Kubernetes (EKS) persistent shared volumes for microservices

---

## Instance Store

### Definition
Temporary, ephemeral physical storage physically attached to the host machine running your virtual machine.

### Characteristics
- Extremely fast (lowest latency possible)
- Ephemeral: Data is permanently lost if the instance is stopped, terminated, or hardware fails. (Reboots are okay).

### Use Cases
- High-speed caching
- Temporary scratch space for data processing
- Buffer storage for load balancers

---

## IOPS (Input/Output Operations Per Second)

### Definition
The metric measuring disk read/write performance. How many transactions the disk can handle per second.

### Important For
- Busy relational databases
- High transaction, low-latency enterprise systems

### Example
gp3 (General Purpose 3) EBS provides:
- A solid baseline of 3000 IOPS, independent of the volume size, which is a massive upgrade over older gp2 volumes.

---

## Networking

### Components
- Public IP (Accessible from the internet)
- Private IP (For internal VPC communication between your microservices)
- Bandwidth constraints
- Network throughput

### Important For
- Overall API latency
- Distributed systems communicating heavily with each other
- Load balancing efficiency

---

## Security Groups

### Definition
A virtual, stateful firewall controlling inbound and outbound traffic at the instance level.

### Characteristics
- Stateful (If you allow a request *in*, the response is automatically allowed *out*, regardless of outbound rules).
- Attached directly to the network interface (ENI) of the instance.
- Scoped to the Region and VPC.

---

## Inbound Rules

### Definition
Controls incoming traffic trying to reach your EC2 instance.

### Example

| Port | Purpose |
|---|---|
| 22 | SSH (Should be locked down to your specific IP, never `0.0.0.0/0`) |
| 80 | HTTP (Standard web traffic) |
| 443 | HTTPS (Secure web traffic, usually terminates at the Load Balancer, not the EC2) |

---

## Outbound Rules

### Definition
Controls outgoing traffic leaving your EC2 instance.

### Default Behavior
- By default, all outbound traffic is allowed. In highly secure enterprise environments, we lock this down to prevent instances from dialing out to malicious servers if compromised.

---

## Important Security Group Concepts

- All inbound traffic is explicitly denied by default. You have to open ports.
- Multiple EC2 instances can (and should) share the same Security Group if they serve the same function (e.g., a "Web-Tier-SG").
- Best practice: Create a dedicated SG for SSH access (e.g., "Bastion-SG") and only attach it when debugging.
- SGs operate outside the EC2 OS, meaning a denied request never even reaches your server's kernel.

---

## Troubleshooting

### Connection Timeout
In my experience, if an API call or SSH attempt just hangs and times out, it is almost always a network firewall issue.

- Security group blocking the port
- NACL (Network Access Control List) dropping the packet
- The instance is in a private subnet with no route to the internet

### Connection Refused
If it rejects the connection immediately, the network allows the traffic, but the server itself says "no".

- The application (like Gunicorn, Node, etc.) crashed and isn't running.
- The service is running but bound to localhost (`127.0.0.1`) instead of all interfaces (`0.0.0.0`).

---

## EC2 User Data

### Definition
A bootstrap shell script that executes with root privileges during the instance's very first startup cycle.

### Purpose
Automate initial server configuration so you don't have to SSH in and configure things manually.

### Common Tasks
- Update OS packages
- Install dependencies (Docker, Python, Git)
- Pull latest application code from a repository
- Start services automatically

### Important Note
It only runs during the *first* boot. If you stop and start the instance later, it won't run again (unless you specifically wipe the state).

### Example

```bash
#!/bin/bash

yum update -y
amazon-linux-extras install docker -y
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

docker run -d -p 80:8000 my-backend-api:latest
```

---

# Additional Interview Notes

## Common Ports

| Port | Protocol | Usage |
|---|---|---|
| 22 | SSH | Secure remote server access |
| 21 | FTP | File Transfer Protocol |
| 20 | FTP Data | FTP data transfer |
| 22 | SFTP | Secure File Transfer |
| 80 | HTTP | Non-secure web traffic |
| 443 | HTTPS | Secure encrypted web traffic |
| 3389 | RDP | Remote Desktop Protocol |

---

## SSH into EC2

### Command

```bash
ssh -i my-key.pem ec2-user@<public-ip>
```

### Common Usernames

| OS | Username |
|---|---|
| Amazon Linux | ec2-user |
| Ubuntu | ubuntu |
| Debian | admin |
| CentOS | centos |
| RHEL | ec2-user or root |

---

## Key Pair

### Definition
A Key Pair consists of:
- Public Key → Stored in AWS EC2 instance
- Private Key (`.pem`) → Stored securely on your local machine

### Important Notes
- Used for SSH authentication
- Never share the `.pem` file
- If lost, you generally cannot recover it directly from AWS

---

## Elastic IP

### Definition
A static public IPv4 address provided by AWS.

### Benefits
- Remains fixed even after instance restart
- Useful for production servers
- Can be remapped to another instance during failover

### Real-world Usage
Often attached to:
- Bastion Hosts
- Production APIs
- Reverse Proxies
- Load Balancers

---

## EBS vs Instance Store

| Feature | EBS | Instance Store |
|---|---|---|
| Persistence | Persistent | Temporary |
| Speed | Fast | Extremely Fast |
| Data Loss on Stop | No | Yes |
| Use Case | Databases, OS disk | Cache, temp processing |
| Network Attached | Yes | No |

---

## Security Group vs NACL

| Feature | Security Group | NACL |
|---|---|---|
| Level | Instance Level | Subnet Level |
| Stateful | Yes | No |
| Rules | Allow Only | Allow + Deny |
| Evaluation | All Rules | Rule Number Order |
| Typical Usage | EC2 protection | Additional subnet security |

### Interview Tip
- Security Groups are stateful
- NACLs are stateless

This is one of the most commonly asked AWS interview questions.

---

# Real-world AWS Recommendations

## Production Best Practices

### EC2
- Use latest generation instances
- Prefer gp3 EBS volumes
- Avoid using root user
- Use IAM Roles instead of hardcoded credentials

### Security
- Never open SSH to `0.0.0.0/0`
- Restrict inbound traffic
- Use HTTPS everywhere
- Rotate keys regularly

### High Availability
- Deploy across multiple Availability Zones
- Use Auto Scaling Groups
- Use Load Balancers
- Store backups with snapshots

### Cost Optimization
- Use Spot Instances for workers
- Use Reserved Instances/Savings Plans for stable workloads
- Stop unused development instances

---

# Frequently Asked Interview Questions

## Q1. Difference between Security Group and NACL?

### Answer
- Security Group works at instance level and is stateful.
- NACL works at subnet level and is stateless.

---

## Q2. Difference between EBS and Instance Store?

### Answer
- EBS is persistent network-attached storage.
- Instance Store is temporary local storage with very high speed.

---

## Q3. What happens if a Security Group blocks traffic?

### Answer
The request never reaches the EC2 operating system because Security Groups operate outside the OS at the virtualization layer.

---

## Q4. Why use Elastic IP?

### Answer
Elastic IP provides a fixed public IP address that remains constant even if the instance restarts.

---

## Q5. What is User Data in EC2?

### Answer
User Data is a bootstrap script executed during the first launch of the EC2 instance for automated setup.

---

# Quick Revision Summary

- EC2 = Virtual server in AWS
- EBS = Persistent storage
- Instance Store = Temporary ultra-fast storage
- Security Group = Stateful firewall
- NACL = Stateless subnet firewall
- Elastic IP = Static public IP
- Key Pair = SSH authentication
- Spot = Cheapest but interruptible
- Reserved = Cheapest for long-term stable workloads
- User Data = Startup automation script
- gp3 = Modern EBS volume with baseline 3000 IOPS
