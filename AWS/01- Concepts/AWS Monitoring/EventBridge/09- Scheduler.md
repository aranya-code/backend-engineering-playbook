# EventBridge Scheduler

Amazon EventBridge Scheduler is a fully managed scheduling service that allows you to invoke AWS services and APIs at specific times or on recurring schedules.

Unlike traditional cron servers, EventBridge Scheduler is serverless, highly available, and scalable.

------------------------------------------------------------------------

# What is EventBridge Scheduler?

EventBridge Scheduler allows you to execute tasks:

- Once
- Recurringly
- On a cron schedule
- On a rate schedule

without managing infrastructure.

------------------------------------------------------------------------

# Why Use Scheduler?

Scheduler helps you:

- Automate repetitive tasks
- Replace cron servers
- Schedule Lambda functions
- Trigger ECS Tasks
- Invoke Step Functions
- Call external APIs

------------------------------------------------------------------------

# Scheduler Workflow

```text
Schedule

↓

EventBridge Scheduler

↓

Target

↓

Execute Task
```

------------------------------------------------------------------------

# Schedule Types

EventBridge Scheduler supports:

- One-Time Schedule
- Recurring Schedule

------------------------------------------------------------------------

# One-Time Schedule

Executes only once.

Example:

```text
31 Dec 2026

11:59 PM

↓

Send Notification
```

------------------------------------------------------------------------

# Recurring Schedule

Executes repeatedly.

Example:

```text
Every Day

8:00 AM

↓

Run Backup
```

------------------------------------------------------------------------

# Rate Expressions

Examples:

```text
rate(5 minutes)

rate(1 hour)

rate(7 days)
```

Useful for fixed intervals.

------------------------------------------------------------------------

# Cron Expressions

Example:

```text
cron(0 8 * * ? *)
```

Runs every day at 8 AM UTC.

Cron expressions provide greater scheduling flexibility.

------------------------------------------------------------------------

# Flexible Time Window

Scheduler supports flexible execution windows.

Benefits:

- Reduced throttling
- Better scalability
- Load balancing

------------------------------------------------------------------------

# Retry Policy

Scheduler supports:

- Retry Attempts
- Maximum Event Age

Failed invocations can automatically retry.

------------------------------------------------------------------------

# Dead-Letter Queue

Scheduler can send failed invocations to Amazon SQS.

Benefits:

- Prevent data loss
- Easier troubleshooting
- Replay failed requests

------------------------------------------------------------------------

# Supported Targets

Scheduler supports:

- Lambda
- ECS
- Batch
- Step Functions
- SQS
- SNS
- EventBridge
- API Destinations

------------------------------------------------------------------------

# Real-World Example

Every night at midnight:

```text
Scheduler

↓

Lambda

↓

Backup Database

↓

SNS Notification
```

The entire workflow runs automatically.

------------------------------------------------------------------------

# Best Practices

- Prefer Scheduler over legacy scheduled rules.
- Use cron for complex schedules.
- Configure retries.
- Configure DLQs.
- Monitor schedules using CloudWatch.

------------------------------------------------------------------------

# Key Takeaways

- EventBridge Scheduler replaces traditional cron servers.
- Supports one-time and recurring schedules.
- Supports retries and DLQs.
- Can invoke numerous AWS services.