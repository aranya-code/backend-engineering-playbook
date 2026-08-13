# CloudWatch Agent & Unified CloudWatch Agent

Amazon CloudWatch automatically collects many infrastructure metrics from AWS services. However, some operating system metrics—such as **memory utilization**, **disk usage**, and **swap usage**—are **not collected by default**.

The **CloudWatch Agent** fills this gap by collecting additional system metrics and application logs from Amazon EC2 instances, on-premises servers, and hybrid environments.

---

# Why Do We Need the CloudWatch Agent?

By default, Amazon EC2 publishes only a limited set of metrics to CloudWatch.

Examples include:

- CPU Utilization
- Network In
- Network Out
- Disk Read Bytes
- Disk Write Bytes
- Status Checks

Important operating system metrics such as:

- Memory utilization
- Disk usage
- Swap usage
- Running processes

are **not available** unless the CloudWatch Agent is installed.

---

# What is the CloudWatch Agent?

The CloudWatch Agent is software that runs on an operating system and sends metrics and logs to Amazon CloudWatch.

It can be installed on:

- Amazon EC2
- On-premises servers
- Virtual machines
- Hybrid cloud environments

It enables centralized monitoring regardless of where the workload is running.

---

# Unified CloudWatch Agent

AWS originally provided separate agents for:

- CloudWatch Metrics
- CloudWatch Logs

These were later replaced by the **Unified CloudWatch Agent**.

The Unified CloudWatch Agent can collect both **metrics** and **logs** using a single configuration.

AWS recommends using the Unified CloudWatch Agent for all new deployments.

---

# CloudWatch Agent vs Unified CloudWatch Agent

| CloudWatch Logs Agent | Unified CloudWatch Agent |
|------------------------|--------------------------|
| Collects logs only | Collects metrics and logs |
| Older agent | Recommended by AWS |
| Separate configuration | Single configuration |
| Limited functionality | Full monitoring capabilities |

---

# Metrics Collected

The Unified CloudWatch Agent can collect:

## CPU Metrics

- CPU Utilization
- CPU Idle Time
- CPU User Time
- CPU System Time

---

## Memory Metrics

- Memory Used
- Memory Available
- Memory Utilization

---

## Disk Metrics

- Disk Used
- Disk Free
- Disk Utilization
- Disk I/O

---

## Network Metrics

- Bytes Sent
- Bytes Received
- Packets Sent
- Packets Received

---

## Swap Metrics

- Swap Usage
- Swap Free

---

## Process Metrics

- Running Processes
- Zombie Processes
- Process Count

---

# Log Collection

The Unified CloudWatch Agent can also collect:

- Application Logs
- System Logs
- Nginx Logs
- Apache Logs
- Docker Logs
- Custom Log Files

Example:

```text
/var/log/messages
/var/log/syslog
/var/log/nginx/access.log
/var/log/nginx/error.log
```

---

# How the Agent Works

```text
EC2 Instance
      |
      v
CloudWatch Agent
      |
      +----------------+
      |                |
      v                v
 Metrics           Log Files
      |                |
      +--------+-------+
               |
               v
      Amazon CloudWatch
```

---

# Installation Overview

Typical installation steps:

1. Install the CloudWatch Agent package.
2. Attach an IAM role with CloudWatch permissions.
3. Create an agent configuration file.
4. Start the CloudWatch Agent service.
5. Verify metrics and logs in CloudWatch.

---

# IAM Permissions

The EC2 instance requires an IAM role.

Typical managed policy:

```text
CloudWatchAgentServerPolicy
```

This policy allows the agent to publish metrics and logs to CloudWatch.

---

# Real-World Example

A production web server hosts a Django application.

By default, CloudWatch monitors:

- CPU Utilization
- Network Traffic

After installing the Unified CloudWatch Agent, the operations team also monitors:

- Memory Utilization
- Disk Usage
- Nginx Access Logs
- Django Application Logs

When disk usage exceeds **90%**, CloudWatch triggers an alarm and sends an Amazon SNS notification, allowing engineers to resolve the issue before the server runs out of storage.

---

# Best Practices

- Always use the Unified CloudWatch Agent for new deployments.
- Attach the `CloudWatchAgentServerPolicy` IAM policy.
- Collect only the metrics you actually need.
- Monitor memory and disk usage for production EC2 instances.
- Centralize application logs in CloudWatch Logs.
- Store the agent configuration in AWS Systems Manager Parameter Store for easier management.
- Review collected metrics periodically to avoid unnecessary costs.

---

# Key Takeaways

- The CloudWatch Agent collects operating system metrics that AWS does not publish by default.
- The Unified CloudWatch Agent is the recommended solution because it collects both metrics and logs.
- The agent works with Amazon EC2, on-premises servers, and hybrid environments.
- It provides visibility into memory, disk, swap, processes, and application logs.
- Installing the Unified CloudWatch Agent is a production best practice for comprehensive infrastructure monitoring.