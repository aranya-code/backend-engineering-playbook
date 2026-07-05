# Subscription Filters

A **Subscription Filter** allows Amazon CloudWatch Logs to stream log events in near real time to other AWS services for processing, analytics, security monitoring, or long-term storage.

Unlike Metric Filters, which convert logs into metrics, Subscription Filters forward matching log events to downstream services.

---

# What are Subscription Filters?

A Subscription Filter continuously monitors a CloudWatch Log Group.

When a log event matches the configured filter pattern, CloudWatch forwards the event to a supported destination.

---

# Why Use Subscription Filters?

Subscription Filters help you:

- Stream logs in near real time
- Process logs automatically
- Build security monitoring solutions
- Archive logs
- Feed analytics platforms
- Integrate with custom applications

---

# How Subscription Filters Work

```text
Application
      |
      v
CloudWatch Logs
      |
      v
Subscription Filter
      |
      +-----------------------------+
      |        |         |          |
      v        v         v          v
 Lambda   Kinesis   Firehose   OpenSearch
```

---

# Supported Destinations

- AWS Lambda
- Amazon Kinesis Data Streams
- Amazon Kinesis Data Firehose
- Amazon OpenSearch Service

---

# Filter Patterns

Subscription Filters support the same filter patterns as Metric Filters.

## Text Pattern

```text
ERROR
```

## JSON Pattern

```text
{ $.status = 500 }
```

## Space-Delimited Pattern

```text
[ip, method, path, status = 500]
```

---

# Subscription Filters vs Metric Filters

| Metric Filters | Subscription Filters |
|----------------|----------------------|
| Convert logs into metrics | Stream matching logs |
| Used for dashboards and alarms | Used for real-time processing |
| Output is a CloudWatch Metric | Output is another AWS service |

---

# Common Use Cases

- Stream logs to Lambda
- Send logs to OpenSearch
- Archive logs with Kinesis Firehose
- Security monitoring
- Centralized logging pipelines

---

# Real-World Example

An e-commerce application writes logs to CloudWatch.

A Subscription Filter matches **ERROR** log events and sends them to AWS Lambda, which enriches the data before forwarding it to Amazon OpenSearch for indexing and visualization.

---

# Best Practices

- Forward only required logs.
- Use structured JSON logs.
- Keep filter patterns simple.
- Monitor downstream services.
- Use Firehose for archival and Lambda for processing.

---

# Key Takeaways

- Subscription Filters stream matching CloudWatch log events.
- Supported destinations include Lambda, Kinesis Data Streams, Firehose, and OpenSearch.
- They enable real-time log analytics, automation, and centralized logging.
- Unlike Metric Filters, they forward logs instead of creating metrics.
