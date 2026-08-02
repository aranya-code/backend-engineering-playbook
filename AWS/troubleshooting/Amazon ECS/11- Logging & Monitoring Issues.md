# Logging & Monitoring Issues

Logging and monitoring are essential for operating Amazon ECS workloads in production. Without proper observability, diagnosing application failures, deployment issues, performance bottlenecks, or security incidents becomes extremely difficult.

This guide explains how to troubleshoot common logging and monitoring problems in Amazon ECS, including CloudWatch Logs, Container Insights, CloudWatch Metrics, and CloudWatch Alarms.

---

# Typical Symptoms

You may observe one or more of the following:

- No logs in CloudWatch
- Missing application logs
- Missing metrics
- CloudWatch alarms never trigger
- Container Insights not showing data
- Dashboards display no information
- Unable to troubleshoot production issues

Example

```
Application

↓

No Logs

↓

No Root Cause
```

---

# ECS Logging Architecture

A typical logging pipeline looks like this.

```
Application

↓

stdout / stderr

↓

Docker Log Driver

↓

CloudWatch Logs

↓

CloudWatch Dashboard

↓

CloudWatch Alarm

↓

Amazon SNS
```

---

# Troubleshooting Workflow

```
Logs Missing

      │

      ▼

Task Definition

      │

      ▼

Log Driver

      │

      ▼

Execution Role

      │

      ▼

CloudWatch Log Group

      │

      ▼

Application Logging

      │

      ▼

Root Cause
```

---

# Step 1: Verify the Log Driver

Open the Task Definition and verify the logging configuration.

Recommended configuration:

```
awslogs
```

Example

```
Log Driver

awslogs
```

Without a configured log driver, ECS cannot send logs to CloudWatch.

---

# Step 2: Verify CloudWatch Log Group

Ensure the configured Log Group exists.

Example

```
/ecs/backend-api
```

Verify:

- Log Group name
- AWS Region
- Log retention
- Correct account

---

# Step 3: Verify the Task Execution Role

The Task Execution Role sends logs to CloudWatch.

Required permissions include:

```
logs:CreateLogStream
```

```
logs:PutLogEvents
```

```
logs:CreateLogGroup
```

(if automatic creation is enabled)

---

### Interview Tip

The **Execution Role**, not the **Task Role**, is responsible for writing logs to CloudWatch.

---

# Step 4: Verify Application Logging

Applications should write logs to:

```
stdout
```

and

```
stderr
```

Avoid writing logs only to local files.

Incorrect

```
logs/app.log
```

Preferred

```
print()

logging.StreamHandler()

stdout
```

---

# Step 5: Verify Container Insights

Container Insights provides cluster-level monitoring.

Verify it is enabled.

Example metrics include:

- CPU Utilization
- Memory Utilization
- Network Throughput
- Running Tasks
- Pending Tasks
- Disk Usage

---

# Step 6: Verify CloudWatch Metrics

Common ECS metrics include:

- CPU Utilization
- Memory Utilization
- RunningTaskCount
- PendingTaskCount

Application metrics may include:

- Request Count
- Response Time
- Error Rate

---

# Step 7: Verify CloudWatch Alarms

Check whether alarms are configured correctly.

Review:

- Metric
- Threshold
- Evaluation Period
- Alarm State

Example

```
CPU > 80%

↓

Alarm
```

---

# Step 8: Review ECS Service Events

Sometimes monitoring issues are caused by ECS itself.

Review events such as:

```
Task failed health checks.
```

```
Service unable to place task.
```

```
Deployment completed.
```

These provide valuable operational context.

---

# Step 9: Verify Log Retention

CloudWatch may automatically delete logs after the retention period.

Example

```
Retention

30 Days
```

Verify:

- Retention period
- Compliance requirements
- Storage costs

---

# Step 10: Review CloudWatch Dashboards

Verify dashboards display the expected metrics.

Check:

- Correct Region
- Correct Cluster
- Correct ECS Service
- Time range
- Metric namespace

---

# Common Logging Problems

## No Logs in CloudWatch

Possible causes

- Missing awslogs driver
- Execution Role permissions
- Wrong Log Group
- Wrong Region
- Application logs written to file

---

## Logs Suddenly Stop

Possible causes

- Container crash
- IAM permission changes
- Log stream creation failure
- CloudWatch service issue

---

## Logs Are Delayed

Possible causes

- High traffic
- Network latency
- Large log volume

Usually this resolves automatically.

---

# Common Monitoring Problems

## No CPU Metrics

Possible causes

- Container Insights disabled
- Wrong Cluster selected
- Metrics delayed

---

## CloudWatch Alarm Never Fires

Possible causes

- Wrong metric
- Incorrect threshold
- Wrong namespace
- Insufficient evaluation periods

---

## Dashboard Shows No Data

Verify

- Cluster
- Region
- Time range
- Namespace

---

# Recommended Production Metrics

## Infrastructure Metrics

- CPU Utilization
- Memory Utilization
- Network In
- Network Out
- Running Tasks
- Pending Tasks

---

## Application Metrics

- HTTP Requests
- Error Rate
- Response Time
- Active Connections
- Queue Length

---

## Business Metrics

Examples

- Orders processed
- Payments completed
- Login success rate
- Active users

Business metrics often provide more meaningful scaling and alerting than infrastructure metrics alone.

---

# Common Root Causes

| Problem | Solution |
|----------|----------|
| Missing log driver | Configure `awslogs` |
| Missing CloudWatch permissions | Update Execution Role |
| Wrong Log Group | Correct Task Definition |
| Logs written to files | Write to stdout/stderr |
| Container Insights disabled | Enable Container Insights |
| Alarm never triggers | Review metric and threshold |
| Wrong dashboard | Select correct cluster and region |
| Log retention expired | Increase retention period |

---

# Diagnostic Checklist

Before making changes, verify:

- awslogs driver configured.
- CloudWatch Log Group exists.
- Execution Role configured.
- Application writes to stdout.
- Container Insights enabled.
- CloudWatch metrics available.
- Alarm configuration reviewed.
- Dashboard configured correctly.
- Correct AWS Region selected.
- ECS Service Events reviewed.

---

# Best Practices

- Always use the `awslogs` log driver.
- Send logs to stdout and stderr.
- Enable Container Insights for production clusters.
- Configure CloudWatch alarms for critical metrics.
- Create dashboards for operational visibility.
- Use structured logging (JSON) when possible.
- Configure appropriate log retention periods.
- Monitor both infrastructure and business metrics.

---

# Interview Questions

### Which IAM role sends logs to CloudWatch?

The **Task Execution Role**.

---

### Why are no logs appearing in CloudWatch?

Possible reasons include:

- Missing awslogs driver
- Incorrect Log Group
- Missing IAM permissions
- Wrong AWS Region
- Application writes logs only to local files

---

### What is Container Insights?

Container Insights is a CloudWatch feature that provides detailed monitoring for ECS clusters, services, tasks, and containers, including CPU, memory, network, and storage metrics.

---

### What should you monitor in production?

Monitor three categories:

Infrastructure

- CPU
- Memory
- Network
- Running Tasks

Application

- Latency
- Error Rate
- Request Count

Business

- Orders
- Transactions
- Active Users

---

### Why is logging to stdout preferred?

Because ECS automatically captures stdout and stderr through the configured log driver, making logs available in CloudWatch without additional agents or file management.

---

# Key Takeaways

- Logging and monitoring are fundamental to operating ECS workloads in production.
- Configure the `awslogs` log driver and ensure the Task Execution Role has the required CloudWatch permissions.
- Applications should write logs to stdout and stderr rather than local files.
- Enable Container Insights to gain visibility into cluster, service, and task health.
- Effective observability combines logs, metrics, dashboards, and alarms to reduce troubleshooting time and improve system reliability.