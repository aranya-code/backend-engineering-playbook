# Production Incident Playbook

## Overview

Production incidents involving Redis can quickly impact entire applications because Redis is often a **critical dependency** for:

- Application caching
- Session storage
- Distributed locking
- Message queues
- Rate limiting
- Leaderboards
- Pub/Sub
- Background job processing

Unlike development environments, production incidents require a **structured, repeatable response** rather than trial-and-error debugging.

This playbook provides a practical incident response workflow that senior backend engineers, SREs, and DevOps teams can follow during Redis outages and performance incidents.

---

# Incident Response Lifecycle

```
          Incident Detected

                 │

                 ▼

           Assess Severity

                 │

                 ▼

      Identify Business Impact

                 │

                 ▼

         Gather Diagnostics

                 │

                 ▼

        Identify Root Cause

                 │

                 ▼

      Mitigate Immediate Impact

                 │

                 ▼

         Permanent Resolution

                 │

                 ▼

          Postmortem Review
```

---

# Incident Severity Levels

| Severity | Description | Example |
|-----------|-------------|----------|
| SEV-1 | Complete outage | Redis unavailable, application down |
| SEV-2 | Major degradation | High latency affecting most users |
| SEV-3 | Partial degradation | Replica lag, increased cache misses |
| SEV-4 | Minor issue | Monitoring alert without customer impact |

---

# Initial Response Checklist

Immediately verify:

```
✓ Is Redis reachable?

✓ Is the application reachable?

✓ Are all nodes healthy?

✓ Is failover in progress?

✓ Are replicas synchronized?

✓ Is memory exhausted?

✓ Is CPU saturated?

✓ Are clients reconnecting?

✓ Are alerts still firing?
```

---

# Step 1 — Assess Business Impact

Determine:

- Which services are affected?
- Are all users impacted?
- Is data at risk?
- Is revenue affected?
- Is failover occurring?
- Are downstream systems overloaded?

Business impact determines incident priority.

---

# Step 2 — Verify Redis Availability

Test connectivity

```bash
redis-cli ping
```

Expected

```
PONG
```

If unavailable

```
Network

↓

Authentication

↓

Redis Process

↓

Infrastructure
```

---

# Step 3 — Verify Server Health

```bash
redis-cli INFO
```

Review

- Uptime
- Memory
- CPU
- Clients
- Persistence
- Replication

---

# Step 4 — Check Memory

```bash
INFO memory
```

Review

```
used_memory

maxmemory

mem_fragmentation_ratio
```

Look for

- Memory exhaustion
- Evictions
- Fragmentation

---

# Step 5 — Check CPU

```bash
INFO cpu
```

Linux

```bash
top
```

or

```bash
htop
```

High CPU usually indicates

- Slow commands
- Hot keys
- Lua scripts
- Excessive requests

---

# Step 6 — Review Slow Log

```bash
SLOWLOG GET
```

Investigate

- KEYS
- HGETALL
- SORT
- Large scans
- Long-running Lua scripts

---

# Step 7 — Check Replication

```bash
INFO replication
```

Verify

- Primary status
- Replica status
- Replication lag

Architecture

```
Primary

      │

      ▼

Replica

      │

      ▼

Application
```

---

# Step 8 — Verify Persistence

```bash
INFO persistence
```

Check

- RDB status
- AOF status
- Background saves
- Rewrite status

---

# Step 9 — Check Connected Clients

```bash
CLIENT LIST
```

Monitor

- Number of clients
- Blocked clients
- Output buffer size

Connection spikes often indicate application issues.

---

# Step 10 — Review Infrastructure

Linux

```bash
df -h
```

```bash
iostat
```

```bash
vmstat
```

Review

- Disk usage
- Disk latency
- Memory pressure
- CPU utilization

---

# Step 11 — Review Monitoring

Correlate metrics

```
CPU

↓

Memory

↓

Latency

↓

Throughput

↓

Errors
```

Use dashboards to identify the first abnormal metric.

---

# Common Incident Scenarios

---

## Scenario 1 — Redis Down

Symptoms

```
Connection Refused

↓

Application Errors
```

Actions

1. Verify process status
2. Review logs
3. Check infrastructure
4. Restore service
5. Validate application recovery

---

## Scenario 2 — High Latency

Symptoms

```
Slow API

↓

Redis Response Time ↑
```

Investigate

- Slow Log
- CPU
- Network
- Large keys

---

## Scenario 3 — Memory Exhaustion

Workflow

```
Memory Full

↓

Evictions

↓

Cache Misses

↓

Database Overload
```

Actions

- Identify large keys
- Increase capacity
- Optimize TTLs

---

## Scenario 4 — Replica Lag

Symptoms

```
Stale Reads

↓

Inconsistent Data
```

Check

```bash
INFO replication
```

Investigate

- Network
- CPU
- Write volume

---

## Scenario 5 — Authentication Failure

Symptoms

```
NOAUTH

↓

Application Failure
```

Verify

- Password
- ACL
- Secrets
- Configuration

---

## Scenario 6 — Failover

Workflow

```
Primary Failure

↓

Replica Promotion

↓

DNS Update

↓

Reconnect
```

Applications should retry connections automatically.

---

# Diagnostic Decision Tree

```
Redis Incident

        │

        ▼

Reachable?

        │

 ┌──────┴────────┐

 │               │

No              Yes

 │               │

Infrastructure  Slow?

 │               │

 ▼               ▼

Restart      CPU High?

 │               │

 ▼               ▼

Recovered    Slow Log

 │               │

 ▼               ▼

Monitor      Memory

 │               │

 ▼               ▼

Resolved     Network

                │

                ▼

             Root Cause
```

---

# Communication During an Incident

Keep stakeholders informed.

Typical update format

```
Status

Current impact

Systems affected

Actions underway

Estimated recovery

Next update time
```

Frequent communication reduces uncertainty during outages.

---

# Recovery Validation Checklist

```
✓ Redis reachable

✓ Applications healthy

✓ Replication synchronized

✓ Memory stable

✓ CPU normal

✓ Latency acceptable

✓ Cache hit ratio restored

✓ Monitoring green

✓ Alerts resolved
```

Do not close an incident until all checks pass.

---

# Post-Incident Review

Every production incident should include a postmortem.

Recommended sections

- Timeline
- Detection
- Root cause
- Business impact
- Resolution
- Lessons learned
- Preventive actions
- Owners
- Target completion dates

---

# Example Timeline

| Time | Event |
|------|-------|
| 10:00 | Alert received |
| 10:02 | Incident acknowledged |
| 10:05 | Redis identified as bottleneck |
| 10:10 | Temporary mitigation applied |
| 10:20 | Root cause confirmed |
| 10:35 | Service fully restored |
| 11:00 | Monitoring stable |
| 14:00 | Postmortem initiated |

---

# Useful Commands

Server

```bash
INFO
```

Memory

```bash
INFO memory
```

CPU

```bash
INFO cpu
```

Replication

```bash
INFO replication
```

Persistence

```bash
INFO persistence
```

Slow Log

```bash
SLOWLOG GET
```

Latency

```bash
LATENCY LATEST
```

Large keys

```bash
redis-cli --bigkeys
```

Hot keys

```bash
redis-cli --hotkeys
```

---

# Production Runbook

```
Alert

    │

    ▼

Acknowledge

    │

    ▼

Assess Impact

    │

    ▼

Collect Evidence

    │

    ▼

Identify Root Cause

    │

    ▼

Mitigate

    │

    ▼

Verify Recovery

    │

    ▼

Communicate

    │

    ▼

Postmortem

    │

    ▼

Prevent Recurrence
```

---

# Common Mistakes

## Restarting Redis Immediately

Restarting before understanding the issue may destroy valuable diagnostic information or worsen the outage.

---

## Ignoring Business Impact

A technically small issue can have a large customer impact.

Prioritize based on business impact.

---

## Making Multiple Changes

Avoid changing several variables simultaneously.

Apply one change at a time and verify the result.

---

## Closing Incidents Too Early

Wait until monitoring confirms sustained stability.

---

## Skipping the Postmortem

Every incident is an opportunity to improve reliability.

---

# Best Practices

- Maintain documented Redis runbooks.
- Define severity levels before incidents occur.
- Automate alerting for critical metrics.
- Practice failover and disaster recovery regularly.
- Use centralized logging and monitoring.
- Record timelines during every incident.
- Conduct blameless postmortems.
- Track corrective actions to completion.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| Monitoring | Real-time dashboards and alerts |
| Recovery | Automate where possible |
| Communication | Provide regular status updates |
| Diagnostics | Preserve evidence before changes |
| Documentation | Keep runbooks up to date |
| Testing | Regularly simulate production failures |

---

# Production Considerations

For enterprise Redis deployments:

- Integrate Redis monitoring with systems such as Prometheus, Grafana, CloudWatch, or Datadog.
- Define clear incident ownership and escalation paths.
- Automate health checks and failover validation.
- Maintain tested backup and disaster recovery procedures.
- Conduct regular game days to validate operational readiness.
- Review incident trends quarterly to identify recurring reliability issues.
- Continuously refine runbooks based on lessons learned from real incidents.

---

# Summary

Effective Redis incident response is built on preparation, structured troubleshooting, and disciplined operational practices. By following a repeatable workflow—from impact assessment and diagnostics to mitigation, recovery validation, and postmortems—engineering teams can minimize downtime, reduce customer impact, and continuously improve the reliability of their Redis infrastructure.

---

# Key Takeaways

- Treat Redis incidents with a structured response rather than ad hoc debugging.
- Assess business impact before selecting mitigation strategies.
- Collect diagnostics before making significant changes.
- Validate recovery using objective health checks and monitoring.
- Communicate regularly with stakeholders during incidents.
- Conduct blameless postmortems after every production incident.
- Maintain and regularly test operational runbooks.
- Continuous operational improvement is the foundation of reliable Redis deployments.