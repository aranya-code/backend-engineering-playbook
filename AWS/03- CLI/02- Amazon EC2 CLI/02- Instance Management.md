# Instance Management

> Learn how to launch, start, stop, reboot, terminate, and manage Amazon EC2 instances using the AWS CLI. This chapter covers the most common day-to-day operations performed by Cloud Engineers, Backend Engineers, and DevOps Engineers.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Launch EC2 instances
- Start and stop instances
- Reboot instances
- Terminate instances
- Describe instance state
- Tag EC2 instances
- Filter instances
- Wait for state changes
- Follow production best practices

---

# Understanding the EC2 Instance Lifecycle

Every EC2 instance moves through a defined lifecycle.

```text
Pending
    │
    ▼
Running
    │
    ├────────────┐
    ▼            │
Stopping         │
    │            │
    ▼            │
Stopped          │
    │            │
    ▼            │
Pending          │
    │            │
    ▼            │
Running ◄────────┘
    │
    ▼
Shutting Down
    │
    ▼
Terminated
```

Understanding these states is essential before managing instances.

---

# Launching an EC2 Instance

Basic syntax:

```bash
aws ec2 run-instances
```

Example:

```bash
aws ec2 run-instances \
--image-id ami-0123456789abcdef0 \
--instance-type t2.micro \
--key-name backend-key \
--security-group-ids sg-0123456789abcdef0 \
--subnet-id subnet-0123456789abcdef0
```

This launches one EC2 instance.

---

# Launch Multiple Instances

```bash
aws ec2 run-instances \
--image-id ami-0123456789abcdef0 \
--instance-type t3.micro \
--count 3
```

AWS launches three identical instances.

---

# Understanding Required Parameters

The most common parameters are:

| Parameter | Purpose |
|-----------|----------|
| `--image-id` | AMI to launch |
| `--instance-type` | Instance size |
| `--count` | Number of instances |
| `--key-name` | SSH key pair |
| `--security-group-ids` | Firewall rules |
| `--subnet-id` | Target subnet |

---

# Viewing Instance Status

```bash
aws ec2 describe-instance-status
```

Returns:

- Health checks
- System status
- Instance status
- Scheduled events

Useful when troubleshooting.

---

# Starting an Instance

```bash
aws ec2 start-instances \
--instance-ids i-0123456789abcdef0
```

Example response:

```json
{
    "StartingInstances":[
        {
            "CurrentState":{
                "Name":"pending"
            }
        }
    ]
}
```

---

# Stopping an Instance

```bash
aws ec2 stop-instances \
--instance-ids i-0123456789abcdef0
```

Stopping preserves:

- EBS volumes
- Instance configuration
- Private IP (in most cases)

Stopping does **not** delete the instance.

---

# Rebooting an Instance

```bash
aws ec2 reboot-instances \
--instance-ids i-0123456789abcdef0
```

A reboot is similar to restarting a physical server.

The instance ID remains unchanged.

---

# Terminating an Instance

```bash
aws ec2 terminate-instances \
--instance-ids i-0123456789abcdef0
```

Once terminated:

- The instance cannot be restarted.
- Instance Store data is lost.
- Root EBS volume may also be deleted depending on its configuration.

Always verify before terminating production instances.

---

# Describing a Specific Instance

```bash
aws ec2 describe-instances \
--instance-ids i-0123456789abcdef0
```

Useful when investigating a specific server.

---

# Filtering Running Instances

```bash
aws ec2 describe-instances \
--filters Name=instance-state-name,Values=running
```

Other states include:

- pending
- running
- stopping
- stopped
- shutting-down
- terminated

---

# Filter by Instance Type

```bash
aws ec2 describe-instances \
--filters Name=instance-type,Values=t3.micro
```

Useful for inventory reporting.

---

# Filter by Tag

Example:

```bash
aws ec2 describe-instances \
--filters Name=tag:Environment,Values=Production
```

Filtering by tags is common in production automation.

---

# Adding Tags

Example:

```bash
aws ec2 create-tags \
--resources i-0123456789abcdef0 \
--tags Key=Name,Value=BackendServer
```

---

# Multiple Tags

```bash
aws ec2 create-tags \
--resources i-0123456789abcdef0 \
--tags \
Key=Environment,Value=Production \
Key=Application,Value=Payments
```

Tags simplify resource management and cost allocation.

---

# Removing Tags

```bash
aws ec2 delete-tags \
--resources i-0123456789abcdef0 \
--tags Key=Environment
```

---

# Waiting for State Changes

Instead of writing custom loops, AWS CLI provides waiters.

Wait until an instance is running:

```bash
aws ec2 wait instance-running \
--instance-ids i-0123456789abcdef0
```

Wait until stopped:

```bash
aws ec2 wait instance-stopped \
--instance-ids i-0123456789abcdef0
```

Wait until terminated:

```bash
aws ec2 wait instance-terminated \
--instance-ids i-0123456789abcdef0
```

These commands are widely used in deployment scripts.

---

# Viewing Public IP

Retrieve the public IP address:

```bash
aws ec2 describe-instances \
--instance-ids i-0123456789abcdef0 \
--query "Reservations[].Instances[].PublicIpAddress"
```

---

# Viewing Private IP

```bash
aws ec2 describe-instances \
--instance-ids i-0123456789abcdef0 \
--query "Reservations[].Instances[].PrivateIpAddress"
```

---

# Production Tips

Before modifying an instance:

- Verify AWS account.
- Verify Region.
- Confirm the correct instance ID.
- Review attached EBS volumes.
- Check Auto Scaling membership.
- Verify application impact.

Never terminate production instances without confirmation.

---

# Real-World Workflow

Deploying a new backend server:

```text
Choose AMI
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
Verify Health
      │
      ▼
Deploy Application
```

---

# Architecture Note

```text
AWS CLI
      │
      ▼
Amazon EC2 API
      │
      ▼
Instance Lifecycle
      │
      ├── Launch
      ├── Start
      ├── Stop
      ├── Reboot
      └── Terminate
```

Every lifecycle operation is performed through the EC2 API.

---

# Interview Note

### Question

**What is the difference between stopping and terminating an EC2 instance?**

### Answer

Stopping an EC2 instance shuts down the virtual machine while preserving its configuration and attached EBS volumes. The instance can be started again later. Terminating an instance permanently deletes it. Once terminated, it cannot be restarted, and resources such as the root EBS volume may also be deleted depending on the instance configuration.

---

# Key Takeaways

- Use `run-instances` to launch EC2 instances.
- Use `start-instances`, `stop-instances`, and `reboot-instances` to manage the instance lifecycle.
- Use `terminate-instances` carefully, as it is irreversible.
- Apply meaningful tags to every production instance.
- Use filters and JMESPath queries to retrieve only the required information.
- Use AWS CLI waiters to automate state transitions reliably.
- Always verify the AWS account, Region, and instance ID before making changes.

---

