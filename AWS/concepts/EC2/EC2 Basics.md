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
