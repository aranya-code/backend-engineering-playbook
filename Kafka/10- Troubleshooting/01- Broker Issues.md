# Broker Issues

## Overview

Kafka brokers are the core servers responsible for storing partitions, replicating data, handling producer requests, and serving consumer fetch requests. If one or more brokers become unhealthy, the entire Kafka cluster can experience degraded performance, increased latency, unavailable partitions, or complete outages.

Understanding common broker issues and knowing how to diagnose and resolve them is an essential skill for operating Kafka in production.

This chapter covers the most common broker-related problems, their symptoms, causes, troubleshooting techniques, and recommended solutions.

---

# What is a Broker?

A Kafka broker is a server that:

- Stores partitions
- Accepts producer requests
- Serves consumer requests
- Replicates partition data
- Participates in leader elections
- Maintains cluster metadata

Example:

```text
               Kafka Cluster

      Broker 1    Broker 2    Broker 3

         │            │            │

      Partitions   Partitions   Partitions
```

---

# Common Broker Issues

Production Kafka clusters commonly experience:

- Broker unavailable
- Broker startup failure
- Broker crashes
- High CPU usage
- High memory usage
- Disk full
- Slow disk I/O
- Network failures
- Under replicated partitions
- Leader election failures
- Controller instability

---

# Broker Not Starting

### Symptoms

- Broker process exits immediately
- Service fails to start
- Clients cannot connect

---

### Possible Causes

- Invalid configuration
- Incorrect listeners
- Port already in use
- Corrupted log directories
- Missing SSL certificates
- Permission issues

---

### Diagnosis

Check broker logs.

```bash
journalctl -u kafka
```

Or:

```bash
docker logs kafka
```

Look for startup exceptions.

---

### Solution

Verify:

- server.properties
- Log directory
- File permissions
- Port availability
- SSL configuration

---

# Broker Keeps Restarting

### Symptoms

```text
Start

↓

Crash

↓

Restart

↓

Crash
```

---

### Common Causes

- Out of memory
- Invalid configuration
- Corrupted log segments
- Disk failure

---

### Solution

Inspect:

- JVM logs
- Kafka logs
- System logs

Correct the root cause before restarting repeatedly.

---

# Broker Offline

### Symptoms

```text
Broker Down
```

Effects:

- Leader elections
- Replica synchronization
- Increased latency

---

### Diagnosis

Verify:

```bash
kafka-broker-api-versions.sh \
--bootstrap-server localhost:9092
```

Or inspect monitoring dashboards.

---

### Solution

- Restart broker
- Verify hardware
- Verify networking
- Verify storage

---

# High CPU Usage

### Symptoms

```text
CPU > 90%
```

---

### Possible Causes

- Heavy producer traffic
- Heavy consumer traffic
- Compression
- Large batch processing
- Too many partitions

---

### Diagnosis

Linux:

```bash
top
```

or

```bash
htop
```

Monitor:

- Request rate
- Network throughput
- JVM activity

---

### Solution

- Add brokers
- Increase partitions
- Optimize producers
- Tune compression
- Reduce excessive traffic

---

# High Memory Usage

### Symptoms

```text
Memory Usage

↓

Increasing
```

---

### Possible Causes

- JVM heap too large
- Memory leak
- Excessive partitions
- Large requests

---

### Diagnosis

Monitor:

- Heap usage
- Garbage Collection
- Page cache

---

### Solution

- Tune JVM
- Reduce heap if necessary
- Increase RAM
- Reduce partition count

---

# Disk Full

### Symptoms

```text
Disk Usage

100%
```

Effects:

- Producers fail
- Replication stops
- Broker instability

---

### Diagnosis

Linux:

```bash
df -h
```

---

### Solution

- Increase storage
- Delete expired segments
- Reduce retention
- Add brokers

---

Never allow Kafka disks to become completely full.

---

# Slow Disk Performance

### Symptoms

- High request latency
- Slow replication
- Consumer lag

---

### Possible Causes

- HDD storage
- Shared disks
- Hardware degradation

---

### Diagnosis

Linux:

```bash
iostat
```

Monitor:

- Disk latency
- IOPS
- Queue length

---

### Solution

- Use SSD/NVMe
- Replace failing disks
- Balance partitions

---

# Network Problems

### Symptoms

- Connection timeouts
- Replica lag
- Producer retries

---

### Diagnosis

Linux:

```bash
ping
```

```bash
traceroute
```

```bash
netstat
```

---

### Solution

Verify:

- Firewall
- DNS
- Load balancer
- Routing
- Network bandwidth

---

# Under Replicated Partitions

### Symptoms

```text
ISR Shrinking
```

---

### Causes

- Slow broker
- Network issue
- Disk bottleneck

---

### Diagnosis

Monitor:

```text
Under Replicated Partitions
```

---

### Solution

Restore broker health before replicas fall too far behind.

---

# Leader Election Problems

### Symptoms

- Frequent leader changes
- Increased latency
- Temporary unavailability

---

### Causes

- Broker crashes
- Network failures
- Controller instability

---

### Solution

Stabilize:

- Brokers
- Network
- Storage

Frequent leader elections often indicate a deeper infrastructure issue.

---

# Controller Changes

### Symptoms

```text
Controller

↓

Broker 2

↓

Broker 1

↓

Broker 3
```

Frequent controller changes are abnormal.

---

### Causes

- Broker instability
- Network partitions
- Resource exhaustion

---

### Solution

Investigate:

- Broker logs
- Network
- JVM
- Storage

---

# Large Number of Partitions

### Symptoms

- Slow startup
- High memory usage
- Controller overload

---

### Diagnosis

Count:

- Topics
- Partitions
- Replicas

---

### Solution

Reduce unnecessary partitions.

Plan partition counts carefully.

---

# Port Conflicts

### Symptoms

```text
Address already in use
```

---

### Diagnosis

Linux:

```bash
netstat -tulpn
```

or

```bash
ss -lntp
```

---

### Solution

Stop conflicting process or change Kafka listener ports.

---

# SSL Configuration Errors

### Symptoms

```text
SSL Handshake Failed
```

---

### Causes

- Invalid certificate
- Expired certificate
- Wrong truststore

---

### Solution

Verify:

- Certificates
- Keystore
- Truststore
- Passwords

---

# Broker Log Analysis

Important log messages include:

```text
ERROR

WARN

FATAL

Exception
```

Always start troubleshooting by examining broker logs.

---

# Monitoring Broker Health

Monitor:

- CPU
- Memory
- Disk
- Network
- JVM
- Request latency
- Replication
- ISR
- Consumer lag

Healthy brokers rarely fail without showing warning signs first.

---

# Troubleshooting Workflow

```text
Identify Symptoms

↓

Collect Logs

↓

Check CPU

↓

Check Memory

↓

Check Disk

↓

Check Network

↓

Check Replication

↓

Identify Root Cause

↓

Fix Issue

↓

Validate Recovery
```

---

# Quick Diagnosis Table

| Problem | Possible Cause | Recommended Action |
|----------|----------------|--------------------|
| Broker won't start | Configuration error | Check `server.properties` |
| High CPU | Heavy traffic | Scale brokers, tune producers |
| High Memory | Large heap, many partitions | Tune JVM |
| Disk Full | Retention too long | Increase storage or reduce retention |
| Slow Broker | Disk bottleneck | Check disk performance |
| SSL Errors | Invalid certificates | Verify keystore/truststore |
| Frequent Leader Elections | Broker instability | Investigate hardware/network |
| Under Replicated Partitions | Slow broker | Restore replica synchronization |

---

# Best Practices

- Monitor broker health continuously.
- Use SSD or NVMe storage.
- Keep disk usage below 80%.
- Monitor JVM metrics.
- Review broker logs regularly.
- Enable comprehensive monitoring and alerting.
- Distribute partitions evenly across brokers.
- Keep brokers on reliable hardware.
- Test broker recovery procedures.
- Perform regular maintenance during planned windows.

---

# Common Mistakes

- Ignoring broker warnings in logs.
- Running brokers on slow disks.
- Allowing disks to become full.
- Creating excessive partitions.
- Restarting brokers repeatedly without identifying the root cause.
- Ignoring network latency.
- Running outdated Kafka versions.
- Disabling monitoring in production.

---

# Summary

Broker issues are among the most common causes of Kafka production incidents. Problems such as startup failures, resource exhaustion, storage bottlenecks, replication failures, and network instability can affect the entire cluster if left unresolved. A structured troubleshooting approach—combined with proactive monitoring, healthy infrastructure, and careful capacity planning—allows operators to identify problems quickly and restore normal cluster operation with minimal downtime.

---

# Key Takeaways

- Brokers are the foundation of every Kafka cluster.
- Monitor CPU, memory, disk, network, and replication continuously.
- Broker logs are the primary source of troubleshooting information.
- Storage and network issues are common causes of broker instability.
- Frequent leader elections and shrinking ISR often indicate broker health problems.
- Preventive monitoring is more effective than reactive troubleshooting.
- Always identify the root cause before restarting brokers.
- Healthy brokers are essential for maintaining a reliable Kafka cluster.