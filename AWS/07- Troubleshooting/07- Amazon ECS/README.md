# Amazon ECS Troubleshooting

The **Troubleshooting** section is a practical guide to diagnosing and resolving real-world issues encountered while running applications on **Amazon Elastic Container Service (ECS)**. Rather than focusing on theory, these notes walk through common production failures, explain why they occur, and provide systematic troubleshooting workflows to identify and resolve them efficiently.

The topics cover the complete lifecycle of an ECS application—from task startup and deployments to networking, IAM, Auto Scaling, monitoring, and production incident response. The objective is to help you build the mindset required to troubleshoot production systems confidently.

---

## Quick Navigation

| # | Topic | Coverage |
|---|---|---|
| 01 | [Troubleshooting Methodology](01-%20Troubleshooting%20Methodology.md) | Systematic approach to ECS troubleshooting. |
| 02 | [Common ECS Errors](02-%20Common%20ECS%20Errors.md) | Common errors and resolutions. |
| 03 | [Task Failed to Start](03-%20Task%20Failed%20to%20Start.md) | Diagnosing task startup failures. |
| 04 | [Tasks Stuck in Pending](04-%20Tasks%20Stuck%20in%20Pending.md) | Troubleshooting pending tasks. |
| 05 | [Container CrashLoop & Restart Issues](05-%20Container%20CrashLoop%20%26%20Restart%20Issues.md) | Handling crashing containers. |
| 06 | [Health Check Failures](06-%20Health%20Check%20Failures.md) | Fixing ALB and container health checks. |
| 07 | [Load Balancer Issues](07-%20Load%20Balancer%20Issues.md) | Resolving routing and load balancing problems. |
| 08 | [Image Pull Failures](08-%20Image%20Pull%20Failures.md) | Diagnosing ECR and Docker registry pull errors. |
| 09 | [Networking Issues](09-%20Networking%20Issues.md) | VPC, subnet, and connectivity troubleshooting. |
| 10 | [IAM & Permission Errors](10-%20IAM%20%26%20Permission%20Errors.md) | Fixing role and policy access issues. |
| 11 | [Auto Scaling Issues](11-%20Auto%20Scaling%20Issues.md) | Troubleshooting scaling policies and constraints. |
| 12 | [Logging & Monitoring Issues](12-%20Logging%20%26%20Monitoring%20Issues.md) | Investigating missing logs and metrics. |
| 13 | [Deployment Failures](13-%20Deployment%20Failures.md) | Diagnosing failed service updates. |
| 14 | [Performance & Resource Bottlenecks](14-%20Performance%20%26%20Resource%20Bottlenecks.md) | CPU, memory, and application profiling. |
| 15 | [Production Incident Playbook](15-%20Production%20Incident%20Playbook.md) | Operational playbooks for severe ECS incidents. |

---

# Quick Navigation

| Topic | Description |
|--------|-------------|
| [01- Common ECS Errors](01-%20Common%20ECS%20Errors.md) | Learn the most common ECS errors, their causes, and a systematic troubleshooting approach. |
| [02- Task Failed to Start](02-%20Task%20Failed%20to%20Start.md) | Diagnose startup failures caused by application crashes, configuration errors, missing dependencies, or resource limitations. |
| [03- Tasks Stuck in Pending](03-%20Tasks%20Stuck%20in%20Pending.md) | Resolve scheduling failures caused by insufficient CPU, memory, networking, Capacity Providers, or placement constraints. |
| [04- Container CrashLoop & Restart Issues](04-%20Container%20CrashLoop%20%26%20Restart%20Issues.md) | Troubleshoot continuously restarting containers caused by runtime failures, memory exhaustion, or failed health checks. |
| [05- Health Check Failures](05-%20Health%20Check%20Failures.md) | Debug container and load balancer health checks that prevent tasks from becoming healthy. |
| [06- Load Balancer Issues](06-%20Load%20Balancer%20Issues.md) | Investigate ALB/NLB configuration, listeners, target groups, routing, and HTTP gateway errors. |
| [07- Image Pull Failures](07-%20Image%20Pull%20Failures.md) | Resolve container image download failures involving Amazon ECR, IAM permissions, image tags, and networking. |
| [08- Networking Issues](08-%20Networking%20Issues.md) | Diagnose networking problems related to VPCs, Security Groups, Route Tables, DNS, ENIs, and VPC Endpoints. |
| [09- IAM & Permission Errors](09-%20IAM%20%26%20Permission%20Errors.md) | Fix IAM role configuration, resource policies, KMS permissions, and AWS service access issues. |
| [10- Auto Scaling Issues](10-%20Auto%20Scaling%20Issues.md) | Troubleshoot scaling policies, CloudWatch alarms, Capacity Providers, and Cluster Auto Scaling. |
| [11- Logging & Monitoring Issues](11-%20Logging%20%26%20Monitoring%20Issues.md) | Resolve CloudWatch Logs, metrics, dashboards, Container Insights, and monitoring configuration issues. |
| [12- Deployment Failures](12-%20Deployment%20Failures.md) | Debug failed deployments, rollbacks, unhealthy tasks, and deployment configuration problems. |
| [13- Performance & Resource Bottlenecks](13-%20Performance%20%26%20Resource%20Bottlenecks.md) | Analyze performance degradation caused by CPU, memory, databases, caches, networking, or external dependencies. |
| [14- Production Incident Playbook](14-%20Production%20Incident%20Playbook.md) | Learn a structured approach for responding to, mitigating, and preventing production incidents in ECS environments. |

---

# Recommended Learning Order

```text
Common ECS Errors
        │
        ▼
Task Failed to Start
        │
        ▼
Tasks Stuck in Pending
        │
        ▼
Container CrashLoop & Restart Issues
        │
        ▼
Health Check Failures
        │
        ▼
Load Balancer Issues
        │
        ▼
Image Pull Failures
        │
        ▼
Networking Issues
        │
        ▼
IAM & Permission Errors
        │
        ▼
Auto Scaling Issues
        │
        ▼
Logging & Monitoring Issues
        │
        ▼
Deployment Failures
        │
        ▼
Performance & Resource Bottlenecks
        │
        ▼
Production Incident Playbook
```

---

# Prerequisites

Before studying this section, you should be familiar with:

- Amazon ECS Fundamentals
- ECS Services and Task Definitions
- ECS Networking
- Docker fundamentals
- Amazon ECR
- IAM Roles
- Elastic Load Balancing
- Amazon CloudWatch

---

# Skills You'll Gain

After completing this section, you will be able to:

- Troubleshoot ECS task startup failures.
- Diagnose scheduling and deployment problems.
- Resolve container crash loops and health check failures.
- Debug networking and load balancer issues.
- Identify and fix IAM permission problems.
- Configure and troubleshoot Auto Scaling.
- Monitor ECS workloads using CloudWatch and Container Insights.
- Analyze performance bottlenecks across application and infrastructure layers.
- Respond to production incidents using a structured troubleshooting methodology.
- Perform root cause analysis and implement preventive measures to improve production reliability.