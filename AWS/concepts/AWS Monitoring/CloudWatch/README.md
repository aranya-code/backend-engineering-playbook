# Amazon CloudWatch

A deep-dive study guide into **Amazon CloudWatch** — AWS's fully managed monitoring and observability service for collecting metrics, aggregating logs, setting alarms, and visualizing operational data across your entire AWS infrastructure.

---

## 📚 Table of Contents

- [What is CloudWatch?](#what-is-cloudwatch)
- [Topics Covered](#topics-covered)
- [Module Structure](#module-structure)
- [Key Concepts at a Glance](#key-concepts-at-a-glance)
- [Architecture Overview](#architecture-overview)
- [Supported AWS Services](#supported-aws-services)
- [Navigation](#navigation)

---

## What is CloudWatch?

Amazon CloudWatch is a **fully managed monitoring and observability service** that collects, monitors, analyzes, and visualizes operational data from AWS resources, on-premises servers, applications, and custom workloads.

It collects data in the form of **metrics**, **logs**, **events**, and **traces**, enabling teams to quickly identify issues, automate responses, and maintain highly available systems.

---

## Topics Covered

| # | Topic | Focus Area |
|---|-------|------------|
| 01 | [Introduction](./01-%20Introduction.md) | What CloudWatch is, why it's needed, core capabilities |
| 02 | [CloudWatch Architecture](./02-%20CloudWatch%20Architecture.md) | Internal architecture and data flow |
| 03 | [Core Components](./03-%20Core%20Components.md) | Metrics, Logs, Alarms, Dashboards, Events |
| 04 | [CloudWatch Metrics](./04-%20CloudWatch%20Metrics.md) | Metric fundamentals and data points |
| 05 | [AWS Service Metrics](./05-%20AWS%20Service%20Metrics.md) | Built-in metrics from AWS services |
| 06 | [Custom Metrics](./06-%20Custom%20Metrics.md) | Publishing your own application metrics |
| 07 | [Namespaces](./07-%20Namespaces.md) | Metric grouping and organization |
| 08 | [Dimensions](./08-%20Dimensions.md) | Metric filtering with key-value pairs |
| 09 | [Metric Statistics](./09-%20Metric%20Statistics.md) | Average, Sum, Min, Max, SampleCount, Percentiles |
| 10 | [Metric Resolution](./10-%20Metric%20Resolution.md) | Standard (60s) vs High-Resolution (1s) metrics |
| 11 | [Basic vs Detailed Monitoring](./11-%20Basic%20vs%20Detailed%20Monitoring.md) | 5-minute vs 1-minute monitoring intervals |
| 12 | [CloudWatch Logs](./12-%20CloudWatch%20Logs.md) | Centralized log collection and storage |
| 14 | [Log Streams](./14-%20Log%20Streams.md) | Individual log event sequences |
| 15 | [Log Retention Policies](./15-%20Log%20Retention%20Policies.md) | Configuring log expiration |
| 16 | [Metric Filters](./16-%20Metric%20Filters.md) | Extracting metrics from log data |
| 17 | [Subscription Filters](./17-%20Subscription%20Filters.md) | Streaming logs to other destinations |
| 18 | [CloudWatch Logs Insights](./18-%20CloudWatch%20Logs%20Insights.md) | Interactive log query and analysis |
| 19 | [Export Logs to Amazon S3](./19-%20Export%20Logs%20to%20Amazon%20S3.md) | Archiving logs for long-term storage |
| 20 | [CloudWatch Agent & Unified Agent](./20-%20CloudWatch%20Agent%20%26%20Unified%20CloudWatch%20Agent.md) | Collecting OS-level metrics and custom logs |
| 21 | [CloudWatch Dashboards](./21-%20CloudWatch%20Dashboards.md) | Building visual operational dashboards |
| 22 | [CloudWatch Alarms](./22-%20CloudWatch%20Alarms.md) | Threshold-based alerting and automated actions |
| 23 | [Composite Alarms](./23-%20Composite%20Alarms.md) | Combining multiple alarms with AND/OR logic |
| 24 | [Contributor Insights](./24-%20Contributor%20Insights.md) | Identifying top contributors to operational issues |
| 25 | [Container Insights](./25-%20Container%20Insights.md) | ECS and EKS container monitoring |
| 26 | [CloudWatch Synthetics](./26-%20CloudWatch%20Synthetics.md) | Canary scripts for API and website monitoring |
| 27 | [ServiceLens](./27-%20ServiceLens.md) | Unified observability with metrics, logs, and traces |
| 28 | [Cross-Account Observability](./28-%20Cross-Account%20Observability.md) | Monitoring across multiple AWS accounts |
| 29 | [Best Practices & Cost Optimization](./29-%20Best%20Practices%20%26%20Cost%20Optimization.md) | Production guidelines and cost management |
| 30 | [Interview Questions & Summary](./30-%20Interview%20Questions%20%26%20Summary.md) | Common interview questions and key takeaways |

---

## Module Structure

This module is organized into progressive learning sections:

```
CloudWatch/
│
├── Fundamentals (01–03)
│   └── Introduction, Architecture, Core Components
│
├── Metrics Deep-Dive (04–11)
│   └── Metrics, Namespaces, Dimensions, Statistics, Resolution
│
├── Logs Deep-Dive (12–19)
│   └── Log Groups, Streams, Retention, Filters, Insights, S3 Export
│
├── Agent & Dashboards (20–21)
│   └── CloudWatch Agent, Dashboard creation
│
├── Alarms & Advanced Features (22–28)
│   └── Alarms, Composite Alarms, Contributor Insights,
│       Container Insights, Synthetics, ServiceLens,
│       Cross-Account Observability
│
└── Production & Interview Prep (29–30)
    └── Best Practices, Cost Optimization, Interview Questions
```

---

## Key Concepts at a Glance

| Concept | Description |
|---------|-------------|
| **Metrics** | Time-ordered numerical data (CPU, memory, latency, errors) |
| **Logs** | Centralized storage for application and system logs |
| **Alarms** | Evaluate metrics and trigger actions (SNS, Auto Scaling, Lambda) |
| **Dashboards** | Customizable visual views of metrics and alarms |
| **Namespaces** | Containers that isolate metrics from different sources |
| **Dimensions** | Key-value pairs that further identify a metric |
| **Metric Filters** | Extract custom metrics from log data |
| **Subscription Filters** | Stream logs to Lambda, Elasticsearch, Kinesis, or S3 |
| **Logs Insights** | SQL-like query language for log analysis |
| **CloudWatch Agent** | Collects OS-level metrics (memory, disk) and custom logs |
| **Composite Alarms** | Combine alarms with AND/OR logic to reduce noise |
| **Synthetics Canaries** | Scripted monitors that simulate user behavior |
| **ServiceLens** | Combines CloudWatch, X-Ray, and health data in one view |

---

## Architecture Overview

```
  Applications / AWS Services / On-Premises Servers
                        │
              ┌─────────┴─────────┐
              │   CloudWatch      │
              │   Agent / SDK     │
              └─────────┬─────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ Metrics  │  │  Logs    │  │ Events   │
   └────┬─────┘  └────┬─────┘  └────┬─────┘
        │              │              │
   ┌────▼─────┐  ┌─────▼────┐  ┌─────▼──────┐
   │ Alarms   │  │ Insights │  │ EventBridge│
   │Dashboards│  │ Filters  │  │ Automation │
   └──────────┘  └──────────┘  └────────────┘
```

---

## Supported AWS Services

CloudWatch automatically collects metrics from:

EC2 · S3 · Lambda · RDS · DynamoDB · ECS · EKS · ELB · API Gateway · Step Functions · CloudFront · SNS · SQS · and many more.

It can also monitor **on-premises servers** and **hybrid environments** using the CloudWatch Agent.

---

## Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [AWS Monitoring](../README.md) |
| ➡️ Next | [AWS CloudTrail](../Cloud%20Trail/README.md) |

---

> **Part of the [AWS Monitoring](../README.md) section in the Backend Engineering Playbook.**
