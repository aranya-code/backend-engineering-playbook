# Cheat Sheet & Interview Guide

> A quick reference for the most commonly used Amazon EC2 CLI commands, production workflows, troubleshooting techniques, and interview questions. This chapter is designed to serve as a day-to-day operational guide for Backend Engineers, DevOps Engineers, and Cloud Engineers.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall commonly used EC2 CLI commands.
- Perform day-to-day EC2 administration.
- Troubleshoot common EC2 issues.
- Follow production operational workflows.
- Prepare for AWS and Backend Engineering interviews.

---

# Why a Cheat Sheet?

Even experienced AWS engineers rarely memorize every CLI command.

Instead, they remember:

- Command patterns
- Operational workflows
- Troubleshooting procedures
- AWS best practices

This chapter provides a practical reference for daily use.

---

# Command Syntax

General syntax:

```bash
aws ec2 <operation> [options]
```

Example:

```bash
aws ec2 describe-instances
```

---

# Instance Management Commands

## List All Instances

```bash
aws ec2 describe-instances
```

---

## List Running Instances

```bash
aws ec2 describe-instances \
--filters Name=instance-state-name,Values=running
```

---

## Launch an Instance

```bash
aws ec2 run-instances \
--image-id ami-0123456789abcdef0 \
--instance-type t3.micro
```

---

## Start an Instance

```bash
aws ec2 start-instances \
--instance-ids i-0123456789abcdef0
```

---

## Stop an Instance

```bash
aws ec2 stop-instances \
--instance-ids i-0123456789abcdef0
```

---

## Reboot an Instance

```bash
aws ec2 reboot-instances \
--instance-ids i-0123456789abcdef0
```

---

## Terminate an Instance

```bash
aws ec2 terminate-instances \
--instance-ids i-0123456789abcdef0
```

---

## Wait Until Running

```bash
aws ec2 wait instance-running \
--instance-ids i-0123456789abcdef0
```

---

## Wait Until Stopped

```bash
aws ec2 wait instance-stopped \
--instance-ids i-0123456789abcdef0
```

---

## Wait Until Terminated

```bash
aws ec2 wait instance-terminated \
--instance-ids i-0123456789abcdef0
```

---

# AMI Commands

## List Amazon AMIs

```bash
aws ec2 describe-images \
--owners amazon
```

---

## List Your AMIs

```bash
aws ec2 describe-images \
--owners self
```

---

## Create an AMI

```bash
aws ec2 create-image \
--instance-id i-0123456789abcdef0 \
--name "backend-v1"
```

---

## Deregister an AMI

```bash
aws ec2 deregister-image \
--image-id ami-0123456789abcdef0
```

---

# EBS Commands

## List Volumes

```bash
aws ec2 describe-volumes
```

---

## Create Volume

```bash
aws ec2 create-volume \
--availability-zone ap-south-1a \
--size 20 \
--volume-type gp3
```

---

## Attach Volume

```bash
aws ec2 attach-volume \
--volume-id vol-0123456789abcdef0 \
--instance-id i-0123456789abcdef0 \
--device /dev/xvdf
```

---

## Detach Volume

```bash
aws ec2 detach-volume \
--volume-id vol-0123456789abcdef0
```

---

## Modify Volume

```bash
aws ec2 modify-volume \
--volume-id vol-0123456789abcdef0 \
--size 100
```

---

# Snapshot Commands

## Create Snapshot

```bash
aws ec2 create-snapshot \
--volume-id vol-0123456789abcdef0 \
--description "Daily Backup"
```

---

## List Snapshots

```bash
aws ec2 describe-snapshots \
--owner-ids self
```

---

## Delete Snapshot

```bash
aws ec2 delete-snapshot \
--snapshot-id snap-0123456789abcdef0
```

---

# Security Group Commands

## List Security Groups

```bash
aws ec2 describe-security-groups
```

---

## Create Security Group

```bash
aws ec2 create-security-group
```

---

## Add Inbound Rule

```bash
aws ec2 authorize-security-group-ingress
```

---

## Remove Inbound Rule

```bash
aws ec2 revoke-security-group-ingress
```

---

# Elastic IP Commands

## Allocate Elastic IP

```bash
aws ec2 allocate-address
```

---

## Associate Elastic IP

```bash
aws ec2 associate-address
```

---

## Release Elastic IP

```bash
aws ec2 release-address
```

---

# Key Pair Commands

## List Key Pairs

```bash
aws ec2 describe-key-pairs
```

---

## Create Key Pair

```bash
aws ec2 create-key-pair
```

---

## Delete Key Pair

```bash
aws ec2 delete-key-pair
```

---

# CloudWatch Commands

## List Metrics

```bash
aws cloudwatch list-metrics \
--namespace AWS/EC2
```

---

## View CPU Metrics

```bash
aws cloudwatch get-metric-statistics
```

---

## List Alarms

```bash
aws cloudwatch describe-alarms
```

---

# Auto Scaling Commands

## List Auto Scaling Groups

```bash
aws autoscaling describe-auto-scaling-groups
```

---

## View Scaling Activities

```bash
aws autoscaling describe-scaling-activities
```

---

## List Launch Templates

```bash
aws ec2 describe-launch-templates
```

---

# Useful Queries

## Instance IDs

```bash
aws ec2 describe-instances \
--query "Reservations[].Instances[].InstanceId"
```

---

## Public IPs

```bash
aws ec2 describe-instances \
--query "Reservations[].Instances[].PublicIpAddress"
```

---

## Private IPs

```bash
aws ec2 describe-instances \
--query "Reservations[].Instances[].PrivateIpAddress"
```

---

## Instance Names

```bash
aws ec2 describe-instances \
--query "Reservations[].Instances[].Tags[?Key=='Name'].Value"
```

---

## Running Instance Count

```bash
aws ec2 describe-instances \
--filters Name=instance-state-name,Values=running \
--query "length(Reservations[].Instances[])"
```

---

# Global CLI Options

| Option | Purpose |
|----------|----------|
| `--profile` | Use a named AWS profile |
| `--region` | Override default Region |
| `--output json` | JSON output |
| `--output table` | Table output |
| `--query` | Filter output |
| `--debug` | Enable debugging |
| `--no-cli-pager` | Disable pager |

---

# Common Errors

| Error | Cause | Resolution |
|--------|-------|------------|
| UnauthorizedOperation | Missing IAM permission | Review IAM policies |
| InvalidInstanceID.NotFound | Wrong instance ID or Region | Verify instance and Region |
| InvalidAMIID.NotFound | Invalid or unavailable AMI | Verify AMI ID |
| InstanceLimitExceeded | EC2 quota reached | Request quota increase or terminate unused instances |
| InsufficientInstanceCapacity | Capacity unavailable | Try another AZ or instance type |
| VolumeInUse | Volume already attached | Detach before reuse |
| InvalidGroup.NotFound | Security Group missing | Verify Security Group ID |
| Connection Timed Out | Network issue | Check Security Group, Route Table, Internet Gateway |
| Permission denied (publickey) | SSH authentication failed | Verify key pair and username |

---

# Production Workflow

```text
Verify AWS Account
        │
        ▼
Verify Region
        │
        ▼
Launch Instance
        │
        ▼
Wait Until Running
        │
        ▼
Assign Tags
        │
        ▼
Verify Connectivity
        │
        ▼
Deploy Application
        │
        ▼
Enable Monitoring
```

---

# Daily EC2 Checklist

Before working with EC2:

- Verify AWS account.
- Verify Region.
- Check instance state.
- Verify Security Groups.
- Confirm IAM Role.
- Review attached EBS volumes.
- Check CloudWatch alarms.
- Review Auto Scaling configuration (if applicable).

---

# Interview Questions

## 1. What is an AMI?

**Answer**

An Amazon Machine Image (AMI) is a template used to launch EC2 instances. It includes the operating system, software configuration, block device mappings, and references to snapshots used for the root volume.

---

## 2. What is the difference between stopping and terminating an EC2 instance?

**Answer**

Stopping an instance shuts it down while preserving its EBS-backed storage and configuration, allowing it to be started again later. Terminating an instance permanently deletes it, and depending on the delete-on-termination setting, associated EBS volumes may also be deleted.

---

## 3. What is the difference between an AMI and an EBS Snapshot?

**Answer**

An AMI is used to launch EC2 instances and includes operating system and launch configuration information. An EBS Snapshot is an incremental backup of an EBS volume that can be used to restore or create new volumes.

---

## 4. What is a Security Group?

**Answer**

A Security Group is a stateful virtual firewall attached to an EC2 instance's network interface. It controls inbound and outbound traffic using allow rules.

---

## 5. What is the difference between a Security Group and a Network ACL?

**Answer**

Security Groups are stateful and operate at the instance level, while Network ACLs are stateless and operate at the subnet level, supporting both allow and deny rules.

---

## 6. What is an Elastic IP?

**Answer**

An Elastic IP is a static public IPv4 address that can be associated with an EC2 instance and reassigned if necessary, making it suitable for production workloads requiring a consistent public IP.

---

## 7. What is Auto Scaling?

**Answer**

Auto Scaling automatically adjusts the number of EC2 instances based on demand, helping maintain application availability while optimizing infrastructure costs.

---

## 8. How would you troubleshoot an EC2 instance that is unreachable?

**Answer**

I would verify the instance state, confirm the correct AWS account and Region, check the Security Group rules, Network ACLs, Route Table, Internet Gateway, public IP, key pair, IAM role, and review CloudWatch metrics and system logs if necessary.

---

## 9. What is the purpose of a Launch Template?

**Answer**

A Launch Template stores the configuration required to launch EC2 instances, including the AMI, instance type, Security Groups, IAM role, storage configuration, and user data. It is commonly used with Auto Scaling Groups.

---

## 10. Why should EC2 instances use IAM Roles instead of Access Keys?

**Answer**

IAM Roles provide temporary credentials through AWS STS, eliminating the need to store long-lived access keys on instances. This improves security and simplifies credential management.

---

# Senior Engineer Tips

Experienced engineers typically:

- Use IAM Roles instead of Access Keys.
- Enable detailed CloudWatch monitoring.
- Tag every EC2 resource consistently.
- Automate backups with EBS snapshots.
- Use Launch Templates for standardization.
- Restrict SSH access and prefer AWS Systems Manager Session Manager where possible.
- Review CloudWatch metrics before resizing instances.
- Test Auto Scaling policies in non-production environments.
- Verify the AWS account and Region before performing any destructive operation.
- Create AMIs before major deployments or operating system upgrades.

---

# Quick Reference

| Task | Command |
|------|---------|
| List Instances | `aws ec2 describe-instances` |
| Launch Instance | `aws ec2 run-instances` |
| Stop Instance | `aws ec2 stop-instances` |
| Start Instance | `aws ec2 start-instances` |
| Reboot Instance | `aws ec2 reboot-instances` |
| Terminate Instance | `aws ec2 terminate-instances` |
| Create AMI | `aws ec2 create-image` |
| Create Snapshot | `aws ec2 create-snapshot` |
| Create Security Group | `aws ec2 create-security-group` |
| Allocate Elastic IP | `aws ec2 allocate-address` |
| List Auto Scaling Groups | `aws autoscaling describe-auto-scaling-groups` |

---

# Final Thoughts

Amazon EC2 is the foundation of Infrastructure as a Service (IaaS) on AWS.

Mastering the EC2 CLI allows you to automate server provisioning, storage management, networking, monitoring, and scaling. Combined with IAM, CloudWatch, Auto Scaling, and EBS, the EC2 CLI becomes an essential tool for building reliable, scalable, and production-ready cloud infrastructure.

---

