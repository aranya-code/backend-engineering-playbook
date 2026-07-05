# CloudWatch Interview Questions & Summary

Amazon CloudWatch is one of the most frequently discussed AWS services in interviews for **Cloud Engineer**, **DevOps Engineer**, **Backend Engineer**, **Site Reliability Engineer (SRE)**, and **Solutions Architect** roles.

This chapter summarizes the key CloudWatch concepts and includes commonly asked interview questions ranging from beginner to advanced levels.

---

# Quick Revision

Remember the core components of CloudWatch:

- Metrics
- Custom Metrics
- Namespaces
- Dimensions
- Statistics
- Metric Resolution
- Basic vs Detailed Monitoring
- Logs
- Log Groups
- Log Streams
- Log Retention
- Metric Filters
- Subscription Filters
- Logs Insights
- CloudWatch Agent
- Dashboards
- Alarms
- Composite Alarms
- Contributor Insights
- Container Insights
- CloudWatch Synthetics
- ServiceLens
- Cross-Account Observability

---

# Beginner Interview Questions

## 1. What is Amazon CloudWatch?

**Answer**

Amazon CloudWatch is a fully managed monitoring and observability service that collects metrics, logs, events, and traces from AWS resources and applications.

---

## 2. What can CloudWatch monitor?

**Answer**

CloudWatch monitors:

- EC2
- Lambda
- RDS
- ECS
- EKS
- DynamoDB
- S3
- API Gateway
- Custom applications
- On-premises servers

---

## 3. What are Metrics?

**Answer**

Metrics are numerical values collected over time that represent the performance or health of a resource.

Example:

- CPU Utilization
- Request Count
- Network In

---

## 4. What are Custom Metrics?

**Answer**

Custom Metrics are application-specific metrics published by users using the **PutMetricData** API.

Example:

- Orders Processed
- Active Users
- Payment Success Rate

---

## 5. What is a Namespace?

**Answer**

A Namespace is a logical container that groups related CloudWatch metrics.

Example:

```text
AWS/EC2
AWS/Lambda
MyApplication
```

---

## 6. What are Dimensions?

**Answer**

Dimensions are key-value pairs that identify a specific resource.

Example:

```text
InstanceId = i-0123456789abcdef0
```

---

## 7. What are CloudWatch Logs?

**Answer**

CloudWatch Logs centralize application and system logs for monitoring and troubleshooting.

---

## 8. What is a Log Group?

**Answer**

A Log Group is a logical container that stores one or more Log Streams.

---

## 9. What is a Log Stream?

**Answer**

A Log Stream is a sequence of log events from a single resource.

---

## 10. What is a CloudWatch Dashboard?

**Answer**

A Dashboard displays metrics, alarms, logs, and widgets in a centralized view.

---

# Intermediate Interview Questions

## 11. What is the difference between Metrics and Logs?

| Metrics | Logs |
|---------|------|
| Numerical values | Text records |
| Performance monitoring | Troubleshooting |
| Lightweight | Detailed information |

---

## 12. What is the difference between Basic and Detailed Monitoring?

| Basic | Detailed |
|--------|----------|
| 5-minute metrics | 1-minute metrics |
| Default | Additional cost |
| Lower granularity | Higher granularity |

---

## 13. Why doesn't EC2 provide Memory Utilization by default?

**Answer**

Memory usage is an operating system metric.

AWS cannot access the operating system directly, so you must install the **Unified CloudWatch Agent**.

---

## 14. What is the CloudWatch Agent?

**Answer**

The CloudWatch Agent collects operating system metrics and log files from EC2 instances and on-premises servers.

---

## 15. What is the Unified CloudWatch Agent?

**Answer**

The Unified CloudWatch Agent collects both metrics and logs using a single configuration.

---

## 16. What is a Metric Filter?

**Answer**

A Metric Filter converts matching log events into CloudWatch Metrics.

---

## 17. What is a Subscription Filter?

**Answer**

A Subscription Filter streams matching log events to:

- AWS Lambda
- Kinesis Data Streams
- Kinesis Firehose
- Amazon OpenSearch Service

---

## 18. What is Logs Insights?

**Answer**

Logs Insights is an interactive query service for searching and analyzing CloudWatch Logs.

---

## 19. What is a CloudWatch Alarm?

**Answer**

An Alarm continuously evaluates metrics and changes state when thresholds are exceeded.

---

## 20. What are the three Alarm states?

**Answer**

- OK
- ALARM
- INSUFFICIENT_DATA

---

# Advanced Interview Questions

## 21. What is a Composite Alarm?

**Answer**

A Composite Alarm evaluates multiple CloudWatch Alarms using logical operators such as **AND**, **OR**, and **NOT**.

---

## 22. What is Contributor Insights?

**Answer**

Contributor Insights identifies the top contributors in logs or metrics, such as IP addresses, API endpoints, or DynamoDB partition keys.

---

## 23. What is Container Insights?

**Answer**

Container Insights provides detailed monitoring for Amazon ECS, Amazon EKS, AWS Fargate, and Kubernetes workloads.

---

## 24. What is CloudWatch Synthetics?

**Answer**

CloudWatch Synthetics uses Canaries to simulate user interactions with applications and APIs.

---

## 25. What is ServiceLens?

**Answer**

ServiceLens combines Metrics, Logs, Alarms, and AWS X-Ray traces into a unified observability console.

---

## 26. What is Cross-Account Observability?

**Answer**

Cross-Account Observability allows a central monitoring account to view metrics, logs, dashboards, and traces from multiple AWS accounts.

---

## 27. How can CloudWatch trigger automatic actions?

**Answer**

CloudWatch Alarms can:

- Send SNS notifications
- Invoke Lambda functions
- Trigger Auto Scaling
- Recover EC2 instances

---

## 28. How do you reduce CloudWatch costs?

**Answer**

- Configure log retention
- Remove unused custom metrics
- Avoid unnecessary high-resolution metrics
- Use standard monitoring when appropriate
- Query only required log data

---

## 29. What is the difference between Metric Filters and Subscription Filters?

| Metric Filters | Subscription Filters |
|----------------|----------------------|
| Convert logs into metrics | Stream log events |
| Used for alarms | Used for processing |
| Output is CloudWatch Metrics | Output is another AWS service |

---

## 30. What is the difference between CloudWatch and AWS X-Ray?

| CloudWatch | AWS X-Ray |
|-------------|------------|
| Infrastructure monitoring | Request tracing |
| Metrics and Logs | Distributed tracing |
| Dashboards and Alarms | Service dependency analysis |

---

# Scenario-Based Interview Questions

### Scenario 1

Your EC2 instance has high CPU utilization.

**How would you investigate?**

**Answer**

- Check CloudWatch Metrics
- Review CloudWatch Alarms
- Analyze CloudWatch Logs
- Review memory and disk metrics
- Investigate application logs
- Scale the application if required

---

### Scenario 2

Your API is slow, but CPU usage is low.

**What would you check?**

**Answer**

- API latency metrics
- CloudWatch Logs
- AWS X-Ray traces
- Database performance
- Network latency

---

### Scenario 3

Your Lambda function occasionally fails.

**How would you troubleshoot it?**

**Answer**

- Lambda Metrics
- Error Count
- Duration
- Throttles
- Lambda Logs
- CloudWatch Alarm history

---

### Scenario 4

Your production application sends hundreds of alerts every hour.

**How would you reduce alert fatigue?**

**Answer**

- Tune alarm thresholds
- Use Composite Alarms
- Remove low-value alarms
- Review evaluation periods

---

### Scenario 5

How would you monitor an application running on Amazon EKS?

**Answer**

- Enable Container Insights
- Install CloudWatch Agent
- Configure CloudWatch Logs
- Create dashboards
- Configure alarms
- Enable ServiceLens
- Enable AWS X-Ray

---

# Production Monitoring Checklist

Before deploying an application, ensure:

- ✅ Metrics configured
- ✅ Custom metrics reviewed
- ✅ Log Groups created
- ✅ Retention policies configured
- ✅ Dashboards created
- ✅ CloudWatch Agent installed
- ✅ Alarms tested
- ✅ Composite Alarms configured
- ✅ Logs Insights queries saved
- ✅ SNS notifications verified

---

# Final Summary

Amazon CloudWatch is the central monitoring and observability platform for AWS.

It enables you to:

- Collect metrics
- Store logs
- Query logs
- Create dashboards
- Configure alarms
- Automate responses
- Monitor containers
- Simulate user interactions
- Trace distributed applications
- Observe multiple AWS accounts from one place

Mastering CloudWatch is essential for designing, operating, and troubleshooting production-grade AWS workloads.

---
