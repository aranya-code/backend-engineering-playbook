# Rolling Updates and Rollbacks

## Overview

One of the biggest challenges in production environments is deploying new application versions without causing downtime.

Docker Swarm solves this problem using:

- Rolling Updates
- Rollbacks

These features allow services to be updated gradually while keeping the application available to users.

---

# What is a Rolling Update?

## Definition

A Rolling Update is the process of replacing old containers with new containers incrementally rather than all at once.

Instead of:

```text
Stop Everything
     ↓
Deploy New Version
     ↓
Start Everything
```

Swarm updates containers one by one or in batches.

---

# Why Rolling Updates?

Without rolling updates:

```text
Version 1 Running

Stop All Containers ❌

Deploy Version 2

Application Down
```

Result:

```text
Downtime
```

---

# With Rolling Updates

```text
Version 1

Replica 1
Replica 2
Replica 3

       ↓

Update Replica 1

       ↓

Update Replica 2

       ↓

Update Replica 3
```

Application remains available during the update.

---

# Rolling Update Architecture

Before Update:

```text
Web Service

V1
V1
V1
```

During Update:

```text
V2
V1
V1
```

Then:

```text
V2
V2
V1
```

Finally:

```text
V2
V2
V2
```

---

# Creating a Service

Example:

```bash
docker service create \
--name web \
--replicas 3 \
nginx:1.25
```

Verify:

```bash
docker service ls
```

---

# Updating a Service

Update image:

```bash
docker service update \
--image nginx:1.26 \
web
```

Swarm begins a rolling update automatically.

---

# Rolling Update Process

```text
Manager

     │

     ▼

Stop Old Task

     │

     ▼

Create New Task

     │

     ▼

Verify Health

     │

     ▼

Continue Update
```

---

# Viewing Update Progress

```bash
docker service ps web
```

Example:

```text
NAME       IMAGE

web.1      nginx:1.26

web.2      nginx:1.25

web.3      nginx:1.25
```

Update is in progress.

---

# Update Configuration

Docker Swarm allows control over update behavior.

---

## Update One Container at a Time

```bash
docker service update \
--update-parallelism 1 \
--image nginx:1.26 \
web
```

Meaning:

```text
Update 1 Task

Wait

Update Next Task
```

---

# Update Multiple Containers at Once

```bash
docker service update \
--update-parallelism 2 \
--image nginx:1.26 \
web
```

Swarm updates:

```text
2 Tasks Simultaneously
```

---

# Update Delay

Control waiting period between updates.

Example:

```bash
docker service update \
--update-delay 30s \
--image nginx:1.26 \
web
```

Result:

```text
Update Task

Wait 30 Seconds

Update Next Task
```

---

# Parallelism + Delay

Example:

```bash
docker service update \
--update-parallelism 2 \
--update-delay 15s \
--image nginx:1.26 \
web
```

Workflow:

```text
Update 2 Tasks

Wait 15 Seconds

Update Next 2 Tasks
```

---

# Update Failure Handling

Suppose:

```text
Version 1 → Stable

Version 2 → Broken
```

Update starts:

```text
Replica 1 Updated
```

Application crashes.

Swarm detects failure.

---

# Update Failure Actions

Swarm supports:

```text
Pause
Continue
Rollback
```

---

# Pause on Failure

```bash
docker service update \
--update-failure-action pause \
--image nginx:1.26 \
web
```

Result:

```text
Failure Detected

Stop Update Process
```

Administrator investigates.

---

# Continue on Failure

```bash
docker service update \
--update-failure-action continue \
--image nginx:1.26 \
web
```

Result:

```text
Failure Detected

Continue Updating
```

Generally not recommended.

---

# Automatic Rollback

```bash
docker service update \
--update-failure-action rollback \
--image nginx:1.26 \
web
```

Result:

```text
Failure Detected

Automatically Return to Previous Version
```

---

# What is a Rollback?

## Definition

A Rollback restores a service to its previous working configuration.

This is one of the most valuable production features of Docker Swarm.

---

# Why Rollbacks Matter

Scenario:

```text
Version 1 → Stable

Version 2 → Buggy
```

Without rollback:

```text
Application Failure
```

With rollback:

```text
Restore Version 1
```

Application becomes healthy again.

---

# Manual Rollback

Rollback service:

```bash
docker service rollback web
```

Swarm restores:

```text
Previous Image

Previous Configuration

Previous State
```

---

# Rollback Workflow

```text
Version 1

      ↓

Update

      ↓

Version 2

      ↓

Issue Detected

      ↓

Rollback

      ↓

Version 1 Restored
```

---

# Viewing Rollback Status

```bash
docker service ps web
```

Example:

```text
web.1 nginx:1.25

web.2 nginx:1.25

web.3 nginx:1.25
```

Rollback completed.

---

# Rollback Configuration

Just like updates, rollbacks can be controlled.

---

## Rollback Parallelism

```bash
docker service update \
--rollback-parallelism 1 \
web
```

Meaning:

```text
Rollback One Task At A Time
```

---

## Rollback Delay

```bash
docker service update \
--rollback-delay 10s \
web
```

Meaning:

```text
Rollback Task

Wait 10 Seconds

Rollback Next Task
```

---

# Update vs Rollback

| Feature | Update | Rollback |
|----------|---------|----------|
| Purpose | Deploy New Version | Restore Previous Version |
| Direction | Forward | Backward |
| Risk | Can Introduce Bugs | Restores Stability |
| Command | docker service update | docker service rollback |

---

# Real-World Example

Current:

```text
Frontend

nginx:1.25
```

Deploy:

```bash
docker service update \
--image nginx:1.26 \
frontend
```

Users report:

```text
500 Errors
```

Rollback:

```bash
docker service rollback frontend
```

Result:

```text
nginx:1.25 Restored
```

Downtime avoided.

---

# Blue-Green vs Rolling Updates

## Rolling Update

```text
V1 → V2

Gradually
```

Benefits:

- Lower resource usage
- Simpler deployments

---

## Blue-Green Deployment

```text
V1 Running

V2 Running

Switch Traffic
```

Benefits:

- Instant rollback
- More resources required

Swarm primarily supports rolling updates natively.

---

# Monitoring Updates

View services:

```bash
docker service ls
```

Inspect service:

```bash
docker service inspect web
```

Pretty output:

```bash
docker service inspect web --pretty
```

Track tasks:

```bash
docker service ps web
```

---

# Common Commands

## Update Image

```bash
docker service update \
--image nginx:latest \
web
```

---

## Set Parallelism

```bash
--update-parallelism 1
```

---

## Set Delay

```bash
--update-delay 30s
```

---

## Automatic Rollback

```bash
--update-failure-action rollback
```

---

## Manual Rollback

```bash
docker service rollback web
```

---

# Best Practices

## Use Rolling Updates

Avoid replacing all containers simultaneously.

---

## Update Gradually

```bash
--update-parallelism 1
```

Reduces deployment risk.

---

## Configure Automatic Rollbacks

```bash
--update-failure-action rollback
```

Recommended for production.

---

## Test Before Deployment

Validate new images in non-production environments.

---

## Monitor During Updates

```bash
docker service ps
```

Watch for failures.

---

# Common Interview Questions

## What is a Rolling Update?

A rolling update replaces old containers with new containers incrementally while keeping the application available.

---

## What is a Rollback?

A rollback restores a service to its previous working version after a failed deployment.

---

## Which Command Performs a Rolling Update?

```bash
docker service update
```

---

## Which Command Performs a Rollback?

```bash
docker service rollback
```

---

## What is Update Parallelism?

It controls how many tasks are updated simultaneously during a rolling update.

---

## What is Update Delay?

It defines the waiting period between update batches.

---

# Interview One-Liner

Docker Swarm Rolling Updates enable zero-downtime deployments by updating service replicas gradually, while Rollbacks provide a fast recovery mechanism that restores the previous stable version when an update fails.
