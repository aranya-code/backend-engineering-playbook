# Introduction to CloudWatch CLI

> Learn how to monitor AWS resources using Amazon CloudWatch and the AWS Command Line Interface (AWS CLI). This chapter introduces CloudWatch architecture, metrics, logs, alarms, dashboards, and observability concepts used in production AWS environments.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Amazon CloudWatch
- Understand observability in AWS
- Navigate CloudWatch CLI commands
- Work with metrics and namespaces
- Understand logs and alarms
- Monitor AWS infrastructure
- Build a foundation for production monitoring

---

# Why Learn CloudWatch CLI?

Amazon CloudWatch is AWS's native monitoring and observability service.

CloudWatch collects:

- Metrics
- Logs
- Events
- Alarms
- Dashboards

Backend Engineers, DevOps Engineers, Platform Engineers, Site Reliability Engineers (SREs), and Cloud Engineers rely on CloudWatch to monitor production workloads.

Typical use cases include:

- Infrastructure monitoring
- Application monitoring
- Centralized logging
- Performance analysis
- Alerting
- Auto Scaling
- Incident response
- Cost optimization

The AWS CLI is commonly used to automate CloudWatch operations in production.

---

# What is Observability?

Monitoring answers:

> **Is my system healthy?**

Observability answers:

> **Why is my system unhealthy?**

CloudWatch provides the data needed to understand system behavior.

---

# Three Pillars of Observability

```text
Observability
│
├── Metrics
├── Logs
└── Traces
```

CloudWatch primarily focuses on:

- Metrics
- Logs
- Events

Distributed tracing is provided through **AWS X-Ray** and **AWS CloudWatch Application Signals**.

---

# How AWS CLI Communicates with CloudWatch

CloudWatch commands follow this pattern:

```bash
aws cloudwatch <operation>
```

Examples:

```bash
aws cloudwatch list-metrics
```

```bash
aws cloudwatch get-metric-statistics
```

```bash
aws cloudwatch put-metric-alarm
```

CloudWatch Logs uses a separate namespace:

```bash
aws logs <operation>
```

Examples:

```bash
aws logs describe-log-groups
```

```bash
aws logs describe-log-streams
```

```bash
aws logs tail
```

---

# CloudWatch Architecture

```text
AWS Resources
      │
      ▼
CloudWatch
      │
      ├── Metrics
      ├── Logs
      ├── Alarms
      ├── Dashboards
      └── Events
      │
      ▼
Notifications / Automation
```

CloudWatch acts as the central monitoring service for AWS resources.

---

# AWS Services Integrated with CloudWatch

Nearly every AWS service publishes metrics.

Common examples:

- EC2
- Lambda
- ECS
- EKS
- RDS
- DynamoDB
- S3
- API Gateway
- ELB
- CloudFront

Custom applications can also publish metrics.

---

# Understanding Metrics

A metric is a numerical measurement collected over time.

Examples:

- CPU Utilization
- Memory Usage
- Request Count
- Error Rate
- Latency
- Disk Read Operations

Metrics help identify trends and performance issues.

---

# Understanding Logs

Logs record events that occur within systems.

Examples:

- Lambda execution logs
- EC2 application logs
- ECS container logs
- VPC Flow Logs
- CloudTrail logs

Logs provide detailed diagnostic information.

---

# Understanding Alarms

CloudWatch Alarms monitor metrics and trigger actions when thresholds are exceeded.

Example:

```text
CPU > 80%

↓

Alarm

↓

SNS Notification

↓

Engineer Notified
```

---

# Understanding Dashboards

CloudWatch Dashboards provide visual representations of metrics.

Typical dashboard widgets include:

- Line charts
- Bar charts
- Number widgets
- Text widgets
- Alarm summaries

Dashboards help teams monitor application health at a glance.

---

# List Available Metrics

```bash
aws cloudwatch list-metrics
```

Returns available metrics across AWS services.

---

# View Metric Data

```bash
aws cloudwatch get-metric-statistics
```

Used to retrieve historical metric values.

---

# List Log Groups

```bash
aws logs describe-log-groups
```

Returns all CloudWatch Log Groups.

---

# View Current Identity

Before modifying monitoring resources:

```bash
aws sts get-caller-identity
```

Always verify the active AWS account.

---

# Global CLI Options

Examples:

```bash
aws cloudwatch list-metrics \
--profile production
```

```bash
aws cloudwatch list-metrics \
--region ap-south-1
```

```bash
aws cloudwatch list-metrics \
--output table
```

---

# Production Tip

Monitoring should be treated as part of the application—not an afterthought.

Every production workload should include:

- Metrics
- Logs
- Alarms
- Dashboards
- Notifications

Good observability significantly reduces Mean Time to Detection (MTTD) and Mean Time to Recovery (MTTR).

---

# Architecture Note

```text
Application
      │
      ▼
CloudWatch
      │
      ├── Metrics
      ├── Logs
      ├── Alarms
      ├── Dashboards
      └── EventBridge
      │
      ▼
Operations Team
```

CloudWatch serves as the operational visibility layer for AWS environments.

---

# Interview Note

### Question

**What is the difference between CloudWatch and CloudTrail?**

### Answer

CloudWatch is used for monitoring and observability. It collects metrics, logs, and alarms to help monitor the health and performance of applications and AWS resources. CloudTrail, on the other hand, records API activity and account events for auditing, governance, compliance, and security investigations. In production, CloudWatch answers **"How is my system performing?"**, while CloudTrail answers **"Who did what and when?"**

---

# Key Takeaways

- CloudWatch is AWS's monitoring and observability service.
- CloudWatch collects metrics, logs, alarms, and dashboards.
- The AWS CLI uses both `aws cloudwatch` and `aws logs` namespaces.
- CloudWatch integrates with nearly every AWS service.
- Effective monitoring is essential for reliable production systems.
- Observability helps reduce downtime and accelerate troubleshooting.