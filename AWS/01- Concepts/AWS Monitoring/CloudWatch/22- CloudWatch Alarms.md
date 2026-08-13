# CloudWatch Alarms

CloudWatch Alarms continuously monitor CloudWatch metrics and automatically perform actions when predefined thresholds are reached. They help detect operational issues, notify administrators, and automate responses to maintain application availability and reliability.

CloudWatch Alarms are one of the most important monitoring features in AWS because they enable proactive infrastructure management.

---

# What are CloudWatch Alarms?

A CloudWatch Alarm watches a single CloudWatch metric over a specified time period.

It compares the metric against a configured threshold and changes its state when the threshold is crossed.

Unlike dashboards, which provide visualization, alarms actively monitor resources and can automatically trigger actions.

---

# Why Use CloudWatch Alarms?

CloudWatch Alarms help you:

- Detect infrastructure failures
- Monitor application health
- Receive notifications
- Trigger Auto Scaling
- Recover EC2 instances automatically
- Reduce Mean Time to Recovery (MTTR)
- Improve system availability

---

# How CloudWatch Alarms Work

```text
CloudWatch Metric
        |
        v
CloudWatch Alarm
        |
Threshold Evaluation
        |
        +--------------------------+
        |                          |
        v                          v
Threshold Met             Threshold Not Met
        |                          |
        v                          v
Alarm State               OK State
        |
        v
SNS / Lambda / Auto Scaling / EC2 Actions
```

CloudWatch continuously evaluates incoming metric data against the configured threshold.

---

# Alarm Components

Every CloudWatch Alarm consists of the following components:

## Metric

The metric being monitored.

Examples:

- CPUUtilization
- NetworkIn
- Lambda Errors
- RequestCount

---

## Threshold

The value that determines when the alarm changes state.

Example:

```text
CPUUtilization > 80%
```

---

## Period

The amount of time over which CloudWatch evaluates the metric.

Examples:

- 10 seconds (High Resolution)
- 30 seconds
- 1 minute
- 5 minutes

---

## Evaluation Periods

The number of consecutive periods CloudWatch evaluates.

Example:

```text
Evaluation Periods = 5
```

CloudWatch checks the last five periods before making a decision.

---

## Datapoints to Alarm

Specifies how many evaluation periods must breach the threshold before the alarm enters the **ALARM** state.

Example:

```text
Evaluation Periods = 5

Datapoints to Alarm = 3
```

This means at least **3 out of the last 5** periods must exceed the threshold.

---

# Alarm States

CloudWatch Alarms have three possible states.

## OK

The metric is operating within the configured threshold.

Example:

```text
CPU = 35%
Threshold = 80%
State = OK
```

---

## ALARM

The metric has breached the configured threshold.

Example:

```text
CPU = 92%
Threshold = 80%
State = ALARM
```

---

## INSUFFICIENT_DATA

CloudWatch does not have enough data to determine the alarm state.

This commonly occurs:

- Immediately after creating an alarm
- When a resource stops publishing metrics
- During temporary communication failures

---

# Alarm Actions

When an alarm enters the **ALARM** state, CloudWatch can automatically perform one or more actions.

Supported actions include:

- Send an Amazon SNS notification
- Invoke an AWS Lambda function
- Trigger an Auto Scaling policy
- Stop an EC2 instance
- Reboot an EC2 instance
- Recover an EC2 instance
- Terminate an EC2 instance

These actions help automate operational responses.

---

# Example Alarm

Monitor CPU utilization.

```text
Metric

CPUUtilization

Threshold

> 80%

Period

1 Minute

Evaluation Periods

5

Datapoints to Alarm

3
```

If CPU utilization exceeds **80%** during **3 of the last 5 minutes**, the alarm changes to the **ALARM** state.

---

# Alarm Evaluation Flow

```text
Metric
   |
   v
Threshold Check
   |
   v
CloudWatch Alarm
   |
   +---------------------------+
   |                           |
   v                           v
      OK                  ALARM
                               |
                               v
         SNS / Lambda / Auto Scaling
```

---

# Common Use Cases

CloudWatch Alarms are commonly used to monitor:

- High CPU utilization
- Low available memory
- High disk utilization
- Application errors
- HTTP 5xx responses
- Database connections
- Queue length
- Lambda failures
- API latency

---

# Real-World Example

A production web application runs on Amazon EC2 behind an Application Load Balancer.

CloudWatch monitors:

- CPU Utilization
- Memory Utilization
- HTTP 5xx Errors

When CPU utilization remains above **80%** for **3 out of 5 minutes**:

1. The alarm enters the **ALARM** state.
2. Amazon SNS sends a notification to the operations team.
3. An Auto Scaling policy launches an additional EC2 instance.
4. The application continues serving requests without interruption.

---

# Best Practices

- Create alarms only for important metrics.
- Use meaningful alarm names.
- Avoid overly sensitive thresholds that generate false alarms.
- Combine alarms with Auto Scaling for production workloads.
- Monitor both infrastructure and application metrics.
- Review alarm thresholds periodically.
- Test alarm actions before deploying to production.

---

# Common Mistakes

- Monitoring too many low-value metrics.
- Using thresholds that are too aggressive.
- Ignoring the **INSUFFICIENT_DATA** state.
- Creating alarms without notifications.
- Not testing alarm actions.

---

# Key Takeaways

- CloudWatch Alarms continuously monitor CloudWatch metrics.
- Every alarm consists of a metric, threshold, period, evaluation periods, and datapoints to alarm.
- Alarm states include **OK**, **ALARM**, and **INSUFFICIENT_DATA**.
- Alarms can automatically invoke SNS, Lambda, Auto Scaling, and EC2 recovery actions.
- Well-designed alarms enable proactive monitoring and reduce downtime in production environments.