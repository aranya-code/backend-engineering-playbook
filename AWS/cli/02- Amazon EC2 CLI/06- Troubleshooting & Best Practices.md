# Troubleshooting & Best Practices

> Learn how to troubleshoot common Amazon EC2 issues using the AWS CLI and follow production-ready operational practices for managing EC2 instances at scale.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Troubleshoot common EC2 CLI errors
- Diagnose instance launch failures
- Resolve SSH connectivity issues
- Troubleshoot EBS attachment problems
- Investigate networking issues
- Debug Security Group misconfigurations
- Improve EC2 performance
- Apply production-ready operational practices

---

# Why Troubleshooting Matters

Most EC2 problems are **not caused by AWS**.

Instead, they are usually caused by:

- Wrong Region
- Wrong AWS Account
- Security Groups
- IAM Permissions
- Missing Key Pair
- Incorrect AMI
- Networking
- Route Tables
- EBS configuration
- User mistakes

A structured troubleshooting approach saves hours of debugging.

---

# EC2 Troubleshooting Workflow

Whenever an EC2 operation fails:

```text
AWS CLI Installed?
        │
        ▼
Correct AWS Account?
        │
        ▼
Correct Region?
        │
        ▼
Instance Exists?
        │
        ▼
Instance State?
        │
        ▼
IAM Permissions?
        │
        ▼
Networking?
        │
        ▼
Storage?
        │
        ▼
Retry with --debug
```

Always troubleshoot from the top down.

---

# Verify Your Environment

Before troubleshooting:

```bash
aws --version

aws sts get-caller-identity

aws configure list

aws configure get region
```

Verify:

- CLI installation
- Active AWS account
- Credentials
- Default Region

---

# Error: UnauthorizedOperation

Example:

```text
UnauthorizedOperation
```

Cause:

Missing IAM permission.

Verify:

```bash
aws sts get-caller-identity
```

Then review:

- IAM Policy
- IAM Role
- SCP (AWS Organizations)

---

# Error: InvalidInstanceID.NotFound

Example:

```text
InvalidInstanceID.NotFound
```

Possible causes:

- Wrong Region
- Incorrect Instance ID
- Instance already terminated

Verify:

```bash
aws ec2 describe-instances
```

---

# Error: InstanceLimitExceeded

Example:

```text
InstanceLimitExceeded
```

Cause:

You've reached your EC2 quota.

Solutions:

- Request a quota increase.
- Terminate unused instances.
- Use a different instance family.

---

# Error: InsufficientInstanceCapacity

Example:

```text
InsufficientInstanceCapacity
```

Cause:

AWS temporarily lacks capacity for the requested instance type.

Possible solutions:

- Try another Availability Zone.
- Choose another instance type.
- Retry later.

---

# Error: InvalidAMIID.NotFound

Example:

```text
InvalidAMIID.NotFound
```

Cause:

The specified AMI:

- Doesn't exist
- Is in another Region
- Was deregistered

Verify:

```bash
aws ec2 describe-images
```

---

# Instance Launch Failure

Checklist:

- AMI exists
- Subnet exists
- Security Group exists
- Key Pair exists
- IAM Role exists
- Quota available

Most launch failures occur before the instance is created.

---

# SSH Connection Timeout

Example:

```text
Connection timed out
```

Verify:

- Instance running
- Public IP assigned
- Internet Gateway
- Route Table
- Security Group
- Network ACL

---

# Permission Denied (Public Key)

Example:

```text
Permission denied (publickey)
```

Possible causes:

- Wrong private key
- Wrong EC2 username
- Incorrect file permissions

Common usernames:

| Operating System | Username |
|------------------|----------|
| Amazon Linux | ec2-user |
| Ubuntu | ubuntu |
| RHEL | ec2-user |
| CentOS | centos |
| Debian | admin |

---

# Security Group Issues

Unable to connect?

Verify:

```bash
aws ec2 describe-security-groups
```

Ensure required ports are open.

Examples:

SSH

```
22
```

HTTP

```
80
```

HTTPS

```
443
```

---

# Elastic IP Problems

Incorrect public IP?

Verify:

```bash
aws ec2 describe-addresses
```

Check:

- Allocation ID
- Association
- Instance ID

---

# Volume Attachment Issues

Example:

```text
IncorrectState
```

Possible causes:

- Volume already attached
- Wrong Availability Zone

Verify:

```bash
aws ec2 describe-volumes
```

---

# Snapshot Problems

Cannot restore volume?

Verify:

```bash
aws ec2 describe-snapshots \
--owner-ids self
```

Check:

- Snapshot exists
- Correct Region
- Permissions

---

# High CPU Usage

Investigate:

```bash
aws cloudwatch get-metric-statistics
```

Possible causes:

- Application bug
- Memory pressure
- High traffic
- Infinite loop

Scaling isn't always the correct solution.

---

# High Network Traffic

Review:

- Network In
- Network Out

Possible causes:

- DDoS
- Unexpected traffic
- Large deployments
- Backup jobs

---

# Auto Scaling Problems

Instances not launching?

Verify:

- Launch Template
- Auto Scaling Group
- Desired Capacity
- Maximum Capacity
- Health Checks

View scaling events:

```bash
aws autoscaling describe-scaling-activities
```

---

# CloudWatch Alarm Issues

Alarm never triggers?

Verify:

- Metric Name
- Namespace
- Dimensions
- Threshold
- Evaluation Period

Incorrect metric dimensions are a common cause.

---

# Use --debug

AWS CLI debugging:

```bash
aws ec2 describe-instances \
--debug
```

Useful information includes:

- Request signing
- API endpoint
- HTTP request
- HTTP response
- Retry attempts

---

# Production Checklist

Before modifying production instances:

- □ Verify AWS Account
- □ Verify Region
- □ Verify Instance ID
- □ Review attached volumes
- □ Review Security Groups
- □ Confirm application impact
- □ Notify stakeholders if required
- □ Create backup if necessary

---

# Production Best Practices

## Use IAM Roles

Avoid storing Access Keys on EC2 instances.

Prefer:

- IAM Roles
- Instance Profiles

---

## Tag Every Resource

Recommended tags:

- Name
- Environment
- Owner
- CostCenter
- Application

Tags simplify automation and cost tracking.

---

## Enable Detailed Monitoring

CloudWatch provides:

- Better visibility
- Faster troubleshooting
- Improved scaling decisions

---

## Backup Before Changes

Before:

- OS upgrades
- Application deployments
- Major configuration changes

Create:

- AMI
- EBS Snapshot

Recovery becomes much easier.

---

## Use Launch Templates

Launch Templates replace legacy Launch Configurations.

Benefits:

- Versioning
- Reusability
- Easier Auto Scaling

---

## Restrict SSH

Instead of:

```text
0.0.0.0/0
```

Prefer:

```text
Corporate VPN

or

Trusted IP Range
```

---

# Real-World Troubleshooting Workflow

Application unreachable.

```text
Verify Instance Running
        │
        ▼
Check Public IP
        │
        ▼
Verify Security Group
        │
        ▼
Verify Route Table
        │
        ▼
Check Application
        │
        ▼
Review CloudWatch Metrics
        │
        ▼
Review Logs
```

Never assume the issue is with AWS.

---

# Architecture Note

```text
AWS CLI
      │
      ▼
EC2 API
      │
      ▼
Authentication
      │
      ▼
Authorization
      │
      ▼
Networking
      │
      ▼
Storage
      │
      ▼
EC2 Instance
```

Failures can occur at any stage of this workflow.

---

# Interview Note

### Question

**How would you troubleshoot an EC2 instance that is running but cannot be accessed via SSH?**

### Answer

First, verify that the instance is in the **Running** state and has a reachable public IP (or an appropriate private connectivity method). Check the Security Group to ensure port 22 is allowed from the correct source, verify the subnet's route table and Internet Gateway (if using a public subnet), confirm that the correct key pair and username are being used, and review Network ACLs. Finally, inspect the instance's system logs and CloudWatch metrics to identify any operating system or application-level issues.

---

# Key Takeaways

- Most EC2 issues are caused by configuration errors rather than AWS service failures.
- Always verify the AWS account, Region, and resource identifiers before troubleshooting.
- Security Groups, networking, and IAM permissions are the most common sources of connectivity issues.
- Use `--debug` for detailed AWS CLI diagnostics.
- Enable monitoring, tagging, and backups before making production changes.
- Follow a structured troubleshooting workflow to minimize downtime and reduce operational risk.

---

