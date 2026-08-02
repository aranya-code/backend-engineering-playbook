# Celery with Redis

## Overview

As applications grow, not every task should be executed during the HTTP request lifecycle. Some operations take several seconds—or even minutes—to complete.

Examples include:

- Sending emails
- Processing images
- Generating PDF reports
- Uploading files
- AI inference
- Video processing
- Sending notifications
- Data synchronization

Executing these tasks inside an API request increases response time and degrades user experience.

**Celery** solves this problem by executing tasks asynchronously, while **Redis** acts as the message broker that queues tasks for background workers.

Redis + Celery is one of the most widely used architectures in Django and FastAPI production systems.

---

# What is Celery?

Celery is a distributed task queue that executes background jobs asynchronously.

Instead of

```
Request

↓

Long Running Task

↓

Response
```

Use

```
Request

↓

Redis Queue

↓

Immediate Response

↓

Celery Worker

↓

Task Execution
```

The user receives a response immediately.

---

# Why Redis?

Celery requires a message broker.

Popular options

| Broker | Popularity | Recommended |
|----------|------------|-------------|
| Redis | ⭐⭐⭐⭐⭐ | ✅ Yes |
| RabbitMQ | ⭐⭐⭐⭐⭐ | Enterprise |
| Amazon SQS | ⭐⭐⭐ | Cloud Native |
| Kafka | ⭐⭐ | Event Streaming |

Redis is simple, fast, and easy to configure.

---

# High-Level Architecture

```
               Client

                  │

                  ▼

          Django / FastAPI

                  │

                  ▼

          Celery Producer

                  │

                  ▼

              Redis Queue

                  │

                  ▼

           Celery Worker

                  │

                  ▼

          Background Task
```

---

# Production Architecture

```
                    Users

                      │

                      ▼

               Load Balancer

                      │

        ┌─────────────┴─────────────┐

        ▼                           ▼

     Django                     FastAPI

        │                           │

        └─────────────┬─────────────┘

                      ▼

                Redis Broker

        ┌─────────────┼─────────────┐

        ▼             ▼             ▼

   Worker 1      Worker 2      Worker 3

        │             │             │

        └─────────────┼─────────────┘

                      ▼

               PostgreSQL
```

Workers process jobs independently.

---

# Installing Packages

```bash
pip install celery
```

Redis support

```bash
pip install redis
```

or

```bash
pip install celery[redis]
```

---

# Django Project Structure

```
project/

├── config/

│   ├── settings.py

│   ├── celery.py

│   └── __init__.py

├── app/

│   ├── tasks.py

│   ├── views.py

│   └── models.py

└── manage.py
```

---

# Creating Celery App

Create

```
config/celery.py
```

```python
from celery import Celery

app = Celery("project")

app.conf.broker_url = "redis://localhost:6379/0"

app.conf.result_backend = "redis://localhost:6379/1"

app.autodiscover_tasks()
```

---

# Initialize Celery

```
config/__init__.py
```

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

---

# Django Settings

```python
CELERY_BROKER_URL =

"redis://localhost:6379/0"

CELERY_RESULT_BACKEND =

"redis://localhost:6379/1"
```

Better

```python
CELERY_BROKER_URL =

os.getenv("REDIS_BROKER")
```

---

# Creating a Task

```
tasks.py
```

```python
from celery import shared_task

@shared_task

def send_email(email):

    print(

        f"Sending email to {email}"

    )
```

---

# Calling a Task

Instead of

```python
send_email(email)
```

Use

```python
send_email.delay(email)
```

Workflow

```
Request

↓

Redis

↓

Worker

↓

Task
```

---

# Running Worker

```bash
celery -A config worker --loglevel=info
```

Worker output

```
Ready.
```

Now Celery processes tasks.

---

# Running Beat Scheduler

Periodic jobs

```bash
celery -A config beat
```

Architecture

```
Celery Beat

↓

Redis

↓

Workers

↓

Execute Task
```

---

# Example: Sending Email

Without Celery

```
User Registers

↓

SMTP

↓

Wait

↓

Response
```

---

With Celery

```
User Registers

↓

Redis Queue

↓

Response

↓

Email Sent
```

Much better user experience.

---

# Example: PDF Generation

```
User

↓

Generate PDF

↓

Redis

↓

Worker

↓

PDF Created

↓

Download Link
```

---

# Example: AI Processing

```
Prompt

↓

Redis Queue

↓

GPU Worker

↓

LLM

↓

Database
```

API remains responsive.

---

# Example: Image Processing

```
Upload Image

↓

Redis

↓

Worker

↓

Resize

↓

Compress

↓

Store
```

---

# Task States

A task transitions through several states.

```
PENDING

↓

RECEIVED

↓

STARTED

↓

SUCCESS

↓

FAILURE
```

Result backend stores task status.

---

# Getting Task Status

```python
result = send_email.delay(email)

print(result.id)
```

Later

```python
from celery.result import AsyncResult

task = AsyncResult(task_id)

print(task.status)
```

Possible output

```
SUCCESS
```

---

# Retrying Tasks

Sometimes external services fail.

```python
from celery import shared_task

@shared_task(

    autoretry_for=(Exception,),

    retry_backoff=True,

    max_retries=5

)

def sync_data():

    ...
```

Retries automatically.

---

# Delayed Execution

Run later

```python
send_email.apply_async(

    args=[email],

    countdown=60
)
```

Executes after

```
60 Seconds
```

---

# Scheduled Execution

```python
from datetime import datetime

send_email.apply_async(

    eta=datetime(...)

)
```

Runs at a specific time.

---

# Priority Queues

Separate workloads.

```
Redis

├── default

├── emails

├── reports

└── payments
```

Workers can listen to specific queues.

---

# Queue Routing

Example

```python
send_email.apply_async(

    queue="emails"
)
```

Worker

```bash
celery worker -Q emails
```

---

# Task Chaining

```
Resize Image

↓

Generate Thumbnail

↓

Upload

↓

Notify User
```

Celery supports chaining multiple tasks.

---

# Parallel Tasks

```
Report A

Report B

Report C

      │

      ▼

Merge Results
```

Celery Groups execute tasks concurrently.

---

# Distributed Workers

```
Redis

│

├── Worker 1

├── Worker 2

├── Worker 3

└── Worker 4
```

Tasks are distributed automatically.

---

# Monitoring

Install Flower

```bash
pip install flower
```

Run

```bash
celery -A config flower
```

Dashboard shows

- Active workers
- Queues
- Task status
- Retries
- Failures
- Runtime

---

# Redis Queues

Inspect

```
LLEN celery
```

Shows pending tasks.

---

# High Availability

```
              Django

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

Workers reconnect automatically.

---

# Common Production Use Cases

Celery with Redis is commonly used for:

- Email delivery
- SMS notifications
- Push notifications
- PDF generation
- Image resizing
- AI inference
- Machine learning pipelines
- Data imports
- Database synchronization
- Video transcoding
- Report generation
- Scheduled jobs

---

# Common Mistakes

## Executing Long Tasks Inside Views

Bad

```python
def register(request):

    send_email()
```

Response waits.

Instead

```python
send_email.delay()
```

---

## Large Task Payloads

Bad

```python
generate_report.delay(

    huge_dataframe
)
```

Pass IDs instead.

```python
generate_report.delay(

    report_id
)
```

Worker loads data.

---

## No Retry Logic

Network failures happen.

Always configure retries for external services.

---

## Single Worker

One worker limits throughput.

Production should have multiple workers.

---

## No Monitoring

Without monitoring

```
Failed Tasks

↓

Unknown
```

Use Flower and application metrics.

---

# Best Practices

- Keep tasks small and focused on a single responsibility.
- Pass identifiers (IDs) instead of large objects to tasks.
- Configure automatic retries with exponential backoff.
- Separate workloads into dedicated queues.
- Scale workers horizontally as traffic increases.
- Monitor queues, failures, retries, and worker health.
- Use environment variables for broker and backend configuration.
- Ensure tasks are idempotent so retries do not produce incorrect results.

---

# Performance Considerations

| Feature | Benefit |
|----------|----------|
| Redis Broker | Extremely fast queue operations |
| Multiple Workers | Horizontal scaling |
| Queue Routing | Better workload isolation |
| Retries | Improved reliability |
| Delayed Tasks | Flexible scheduling |
| Parallel Execution | Higher throughput |

---

# Production Considerations

For production deployments:

- Use Redis as the Celery broker and, where appropriate, as the result backend.
- Run multiple worker processes across multiple servers or Kubernetes pods.
- Separate high-priority and low-priority jobs into different queues.
- Configure retries, acknowledgments, and task time limits.
- Monitor queue depth, worker utilization, and task latency.
- Use Redis Sentinel or Cluster for broker high availability.
- Store only lightweight task payloads in Redis; fetch large data inside the worker.

---

# Django vs FastAPI Celery Integration

| Feature | Django | FastAPI |
|----------|---------|----------|
| Configuration | `celery.py` + `settings.py` | Standalone Celery app |
| Task Definition | `@shared_task` | `@shared_task` |
| Redis Broker | ✅ | ✅ |
| Result Backend | ✅ | ✅ |
| Background Processing | Excellent | Excellent |
| Production Usage | Very Common | Very Common |

---

# Summary

Celery and Redis together provide a robust solution for background task processing in Django and FastAPI applications. Redis acts as the message broker, while Celery workers execute tasks asynchronously, allowing APIs to remain responsive even when handling time-consuming operations. With features such as retries, scheduling, task routing, distributed workers, and monitoring, Celery enables scalable and resilient background processing suitable for enterprise production systems.

---

# Key Takeaways

- Celery executes long-running tasks asynchronously.
- Redis is the most commonly used broker for Celery due to its simplicity and performance.
- Use `.delay()` or `.apply_async()` instead of calling tasks directly.
- Keep task payloads small and pass IDs rather than large objects.
- Configure retries, scheduling, and queue routing for production workloads.
- Scale Celery workers horizontally to increase throughput.
- Monitor workers and queues using Flower and Redis metrics.
- Design tasks to be idempotent to safely support retries and failures.