# Introduction to EC2 CLI

> Learn how to manage Amazon EC2 instances using the AWS Command Line Interface (AWS CLI). This chapter introduces the EC2 CLI, explains common command patterns, and builds the foundation for managing compute resources in production.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand how AWS CLI interacts with Amazon EC2.
- Navigate EC2 CLI commands.
- Describe EC2 resources.
- Understand EC2 identifiers.
- List instances using AWS CLI.
- Build a foundation for production EC2 management.

---

# Why Learn EC2 CLI?

Amazon EC2 (Elastic Compute Cloud) is one of the core services in AWS.

Backend engineers use EC2 CLI for:

- Launching virtual machines
- Managing production servers
- CI/CD deployments
- Infrastructure automation
- Disaster recovery
- Auto Scaling
- System administration
- Cloud migrations

Although the AWS Console is convenient, production environments rely heavily on automation through the AWS CLI.

---

# How AWS CLI Communicates with EC2

Unlike Amazon S3, EC2 exposes a single API interface through the AWS CLI.

Commands follow the pattern:

```bash
aws ec2 <operation>
```

Examples:

```bash
aws ec2 describe-instances
```

```bash
aws ec2 run-instances
```

```bash
aws ec2 stop-instances
```

```bash
aws ec2 terminate-instances
```

Every EC2 operation maps directly to an AWS API.

---

# Understanding EC2 Resources

Amazon EC2 consists of several resource types.

```text
Amazon EC2
│
├── Instances
├── AMIs
├── EBS Volumes
├── Snapshots
├── Security Groups
├── Key Pairs
├── Elastic IPs
├── Network Interfaces
└── Placement Groups
```

Each resource has its own CLI operations.

---

# EC2 Resource Identifiers

Every EC2 resource has a unique ID.

Examples:

Instance

```text
i-0f5d8c7b9a1234567
```

Volume

```text
vol-0123456789abcdef0
```

Snapshot

```text
snap-0123456789abcdef0
```

Security Group

```text
sg-0123456789abcdef0
```

These identifiers are required by most EC2 commands.

---

# Your First EC2 Command

List every EC2 instance:

```bash
aws ec2 describe-instances
```

This command returns detailed JSON describing every instance.

---

# Understanding the Response

The response contains:

```text
Reservations
    │
    └── Instances
            │
            ├── InstanceId
            ├── InstanceType
            ├── State
            ├── LaunchTime
            ├── PrivateIpAddress
            └── Tags
```

Most automation extracts only the required fields using `--query`.

---

# Display Only Instance IDs

```bash
aws ec2 describe-instances \
--query "Reservations[].Instances[].InstanceId"
```

Example output:

```json
[
    "i-0123456789abcdef0",
    "i-0987654321fedcba0"
]
```

---

# Display Running Instances

```bash
aws ec2 describe-instances \
--filters Name=instance-state-name,Values=running
```

Filtering greatly reduces unnecessary output.

---

# Display Instance Names

```bash
aws ec2 describe-instances \
--query "Reservations[].Instances[].Tags[?Key=='Name'].Value"
```

This retrieves the values of the **Name** tag.

---

# Common Global Options

EC2 commands support the same global options covered in the AWS CLI Basics guide.

Examples:

```bash
aws ec2 describe-instances \
--profile production
```

```bash
aws ec2 describe-instances \
--region ap-south-1
```

```bash
aws ec2 describe-instances \
--output table
```

---

# Production Tip

Before performing any EC2 operation:

```bash
aws sts get-caller-identity
```

Then verify the Region:

```bash
aws configure get region
```

Many operational mistakes occur because engineers are connected to the wrong AWS account or Region.

---

# Architecture Note

```text
Developer
      │
      ▼
AWS CLI
      │
      ▼
Amazon EC2 API
      │
      ▼
EC2 Resources
      │
      ├── Instances
      ├── EBS
      ├── AMIs
      ├── Security Groups
      └── Snapshots
```

The CLI communicates directly with the Amazon EC2 API over HTTPS.

---

# Interview Note

### Question

**What does `aws ec2 describe-instances` return?**

### Answer

It retrieves detailed information about EC2 instances in the specified Region, including instance IDs, state, instance type, networking details, tags, attached storage, and metadata. The response is returned in JSON by default and can be filtered using JMESPath queries.

---

# Key Takeaways

- EC2 CLI commands use the `aws ec2` namespace.
- Every EC2 resource has a unique identifier.
- `describe-instances` is the primary command for querying EC2.
- Use `--query` to reduce large JSON responses.
- Always verify the active AWS account and Region before making changes.

---
