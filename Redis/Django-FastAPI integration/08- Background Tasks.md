# Background Tasks

## Overview

Not every operation in a web application should be completed during the request-response cycle.

Operations such as:

- Sending emails
- Uploading files
- AI inference
- Video processing
- PDF generation
- Image compression
- Data synchronization
- Report generation
- Analytics processing

can take seconds or even minutes.

Making users wait for these operations results in poor user experience.

Background tasks solve this problem by moving long-running operations outside the HTTP request lifecycle.

Redis is commonly used as the communication layer for background task processing.

---

# Synchronous Processing

```
Client

↓

API

↓

Long Running Task

↓

Database

↓

Response
```

Response Time

```
12 Seconds
```

Poor user experience.

---

# Background Processing

```
Client

↓

API

↓

Redis Queue

↓

Immediate Response

↓

Worker

↓

Background Processing
```

Response Time

```
150 ms
```

User doesn't wait.

---

# Why Background Tasks?

Advantages

- Faster APIs
- Better scalability
- Improved reliability
- Better resource utilization
- Higher throughput
- Retry capability
- Independent scaling

---

# Common Architecture

```
                Client

                   │

                   ▼

             Django/FastAPI

                   │

                   ▼

             Redis Queue

        ┌──────────┼──────────┐

        ▼          ▼          ▼

    Worker 1    Worker 2    Worker 3

        │          │          │

        └──────────┼──────────┘

                   ▼

             PostgreSQL
```

---

# Request Lifecycle

```
Client

↓

HTTP Request

↓

Validate Input

↓

Save Database

↓

Push Job

↓

Redis

↓

Return Response
```

Worker executes later.

---

# Worker Lifecycle

```
Worker

↓

Read Queue

↓

Process Task

↓

Update Database

↓

Finish
```

---

# Typical Background Jobs

Most production systems move these tasks to workers.

| Task | Background? |
|--------|-------------|
| Send Email | ✅ |
| Resize Image | ✅ |
| Generate PDF | ✅ |
| AI Inference | ✅ |
| Push Notification | ✅ |
| SMS | ✅ |
| Data Import | ✅ |
| Excel Export | ✅ |
| Thumbnail Creation | ✅ |
| Video Encoding | ✅ |

---

# Example

Instead of

```python
def register():

    create_user()

    send_email()

    generate_pdf()

    upload_files()

    return response
```

Use

```python
def register():

    create_user()

    send_email.delay()

    generate_pdf.delay()

    upload_files.delay()

    return response
```

---

# Background Email

Without queue

```
User

↓

SMTP

↓

Wait

↓

Response
```

---

With Redis

```
User

↓

Redis Queue

↓

Response

↓

SMTP
```

---

# Background Image Processing

```
Upload

↓

Store Original

↓

Redis

↓

Resize

↓

Compress

↓

Thumbnail

↓

Store
```

---

# AI Processing

```
Prompt

↓

Redis

↓

GPU Worker

↓

LLM

↓

Store Result
```

The API remains responsive.

---

# Report Generation

```
User

↓

Request Report

↓

Redis

↓

Worker

↓

Generate PDF

↓

Store

↓

Email Link
```

---

# Video Processing

```
Upload

↓

Redis

↓

Worker

↓

Convert

↓

Compress

↓

Upload

↓

Notify User
```

---

# Data Synchronization

```
CRM

↓

Redis

↓

Worker

↓

ERP

↓

Database
```

Background synchronization avoids blocking users.

---

# Retry Workflow

Suppose email fails.

```
Worker

↓

SMTP Failure

↓

Retry

↓

Success
```

Automatic retries improve reliability.

---

# Delayed Jobs

```
Register User

↓

Delay

↓

Send Welcome Email

↓

5 Minutes Later
```

Useful for

- Reminders
- Notifications
- Delayed processing

---

# Scheduled Jobs

```
Midnight

↓

Redis Queue

↓

Workers

↓

Cleanup

↓

Archive
```

Examples

- Cleanup logs
- Backup database
- Generate reports
- Sync data

---

# Multiple Workers

```
Redis

│

├── Worker A

├── Worker B

├── Worker C

├── Worker D

└── Worker E
```

Jobs are distributed automatically.

---

# Queue Separation

Different workloads should use different queues.

```
Redis

├── emails

├── reports

├── payments

├── notifications

└── ai
```

Benefits

- Isolation
- Better prioritization
- Easier scaling

---

# Priority Queues

```
High

↓

Payments

↓

Emails

↓

Reports

↓

Analytics

↓

Low
```

Critical jobs execute first.

---

# Worker Scaling

```
Traffic

↓

More Requests

↓

More Jobs

↓

Increase Workers
```

Scaling workers is independent of API servers.

---

# Database Interaction

Recommended workflow

```
Worker

↓

Read Database

↓

Process

↓

Update Database
```

Avoid sending entire objects through Redis.

Instead

```
Task

↓

User ID

↓

Worker

↓

Load Data
```

---

# Task Idempotency

Tasks should be safe to execute multiple times.

Good

```
Generate Report

↓

Overwrite Existing File
```

Bad

```
Send Money

↓

Execute Again

↓

Double Payment
```

---

# Dead Letter Queue

Sometimes tasks permanently fail.

```
Redis Queue

↓

Retry

↓

Retry

↓

Retry

↓

Dead Letter Queue

↓

Manual Review
```

Useful for

- Banking
- Healthcare
- Critical systems

---

# Monitoring

Monitor

- Queue length
- Worker utilization
- Failed tasks
- Retry count
- Average execution time
- Queue wait time

Useful Redis command

```
LLEN celery
```

---

# High Availability

```
             API Servers

                   │

                   ▼

          Redis Sentinel

                   ▼

      Primary + Replicas

                   │

        ┌──────────┼──────────┐

        ▼          ▼          ▼

    Worker1    Worker2    Worker3
```

Workers reconnect after failover.

---

# Failure Scenario

Suppose

```
Worker Crash
```

```
Redis

↓

Task Still Queued

↓

New Worker

↓

Continue Processing
```

Jobs are not lost.

---

# Common Production Use Cases

Background processing is commonly used for:

- Email delivery
- Invoice generation
- PDF reports
- AI inference
- Video transcoding
- Image optimization
- Search indexing
- Notification delivery
- Data synchronization
- Scheduled cleanup
- Billing workflows
- Audit logging

---

# Common Mistakes

## Performing Heavy Work Inside APIs

Bad

```python
@app.post("/upload")

def upload():

    resize()

    compress()

    ai_scan()

    notify()

    return {}
```

Move heavy work to workers.

---

## Passing Large Objects

Bad

```
Entire DataFrame
```

Good

```
Report ID
```

Worker loads data itself.

---

## No Retry Strategy

External APIs fail.

Always configure retries with backoff.

---

## Single Queue for Everything

Avoid

```
emails

payments

reports

analytics

↓

One Queue
```

Separate workloads.

---

## No Monitoring

Without monitoring

```
Queue Growing

↓

Nobody Notices
```

Monitor queue depth continuously.

---

# Best Practices

- Keep HTTP requests fast by offloading expensive work.
- Pass lightweight identifiers instead of large payloads.
- Design tasks to be idempotent.
- Configure retries with exponential backoff.
- Separate workloads into dedicated queues.
- Scale workers independently from API servers.
- Monitor queue depth, execution time, and worker health.
- Use Redis with high availability for production.

---

# Performance Considerations

| Feature | Benefit |
|----------|----------|
| Background Workers | Faster API responses |
| Multiple Queues | Better isolation |
| Worker Scaling | Higher throughput |
| Retries | Better reliability |
| Delayed Tasks | Flexible scheduling |
| Distributed Workers | Horizontal scalability |

---

# Production Considerations

For production deployments:

- Run multiple worker instances across different servers or Kubernetes pods.
- Separate queues by workload and priority.
- Configure retries, time limits, and visibility timeouts.
- Ensure tasks are idempotent to safely handle retries.
- Store only task identifiers in Redis, not large payloads.
- Monitor queue depth, processing latency, worker utilization, and failure rates.
- Deploy Redis with Sentinel or Cluster to avoid a single point of failure.
- Implement dead-letter queues or equivalent mechanisms for permanently failed tasks.

---

# BackgroundTasks (FastAPI) vs Celery

| Feature | FastAPI BackgroundTasks | Celery + Redis |
|----------|-------------------------|----------------|
| Runs After Response | ✅ | ✅ |
| Separate Process | ❌ No | ✅ Yes |
| Distributed Workers | ❌ | ✅ |
| Retries | ❌ | ✅ |
| Scheduling | ❌ | ✅ |
| Queue Management | ❌ | ✅ |
| Horizontal Scaling | Limited | Excellent |
| Enterprise Ready | Small Tasks | Production Systems |

> **Recommendation:** Use FastAPI's built-in `BackgroundTasks` only for lightweight operations that complete quickly (e.g., logging or sending a webhook). For long-running, distributed, or mission-critical workloads, use **Celery with Redis**.

---

# Django vs FastAPI Background Processing

| Framework | Recommended Approach |
|------------|----------------------|
| Django | Celery + Redis |
| FastAPI (Small Apps) | BackgroundTasks |
| FastAPI (Production) | Celery + Redis |
| Microservices | Celery + Redis |
| Enterprise Systems | Celery + Redis |

---

# Summary

Background task processing is a fundamental architecture pattern for scalable backend systems. By moving long-running operations out of the request-response cycle and into Redis-backed worker queues, applications can deliver fast API responses while processing expensive operations asynchronously. Combined with retries, queue separation, worker scaling, monitoring, and high availability, Redis enables reliable background processing suitable for enterprise-grade Django and FastAPI applications.

---

# Key Takeaways

- Long-running operations should not execute during HTTP requests.
- Redis acts as a fast and reliable queue for background workers.
- Celery is the de facto standard for background processing in Django and production FastAPI applications.
- Keep task payloads small and pass only identifiers.
- Design tasks to be idempotent and retry-safe.
- Separate workloads into dedicated queues based on priority.
- Scale workers independently of API servers.
- Continuously monitor queue depth, worker health, retries, and execution times in production.