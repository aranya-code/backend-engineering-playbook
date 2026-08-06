# Producer Errors

## Overview

Kafka producers are responsible for publishing messages to Kafka topics. Although the Producer API is designed to be reliable, various failures can occur while sending messages. These failures may originate from the producer itself, the network, Kafka brokers, authentication, serialization, or cluster configuration.

Understanding common producer errors and knowing how to diagnose and resolve them is essential for building reliable, fault-tolerant Kafka applications.

This chapter covers the most common producer-side issues, their symptoms, causes, troubleshooting techniques, and recommended solutions.

---

# Producer Workflow

```text
Application

↓

Producer

↓

Serialize

↓

Partition

↓

Broker

↓

Acknowledgement
```

Failures can occur at any stage of this workflow.

---

# Common Producer Errors

Production environments commonly encounter:

- Broker unavailable
- Timeout errors
- Serialization errors
- Record too large
- Authentication failures
- Authorization failures
- Unknown topic
- Leader not available
- Network failures
- Buffer exhaustion
- Delivery timeout
- Retries exhausted

---

# Broker Unavailable

### Symptoms

```text
TimeoutException

OR

NetworkException
```

Producer cannot reach the broker.

---

### Possible Causes

- Broker stopped
- Network outage
- Wrong bootstrap server
- Firewall

---

### Diagnosis

Verify:

```bash
kafka-broker-api-versions.sh \
--bootstrap-server localhost:9092
```

Or:

```bash
telnet localhost 9092
```

---

### Solution

- Verify broker status
- Check bootstrap servers
- Verify networking
- Restart broker if necessary

---

# Unknown Topic

### Symptoms

```text
UnknownTopicOrPartitionException
```

---

### Causes

- Topic does not exist
- Incorrect topic name
- Auto topic creation disabled

---

### Solution

Verify:

```bash
kafka-topics.sh \
--bootstrap-server localhost:9092 \
--list
```

Create the topic if required.

---

# Leader Not Available

### Symptoms

```text
LeaderNotAvailableException
```

---

### Causes

- Leader election
- Broker startup
- Broker failure

---

### Solution

Wait for leader election to complete.

If persistent:

- Check broker health
- Check ISR
- Check controller

---

# Timeout Exception

### Symptoms

```text
TimeoutException
```

Producer waited too long.

---

### Causes

- Slow broker
- Network latency
- Large batches
- Busy cluster

---

### Solution

Investigate:

- Broker performance
- Network
- Batch configuration

---

# Delivery Timeout

Producer configuration:

```properties
delivery.timeout.ms
```

Exceeded:

```text
Send Failed
```

---

### Solution

- Increase timeout if appropriate
- Investigate slow brokers
- Check retries

---

# Serialization Error

### Symptoms

```text
SerializationException
```

---

### Causes

- Wrong serializer
- Invalid object
- Schema mismatch

---

### Example

Expected:

```text
JSON
```

Received:

```text
Java Object
```

Serialization fails.

---

### Solution

Verify:

- Serializer configuration
- Object type
- Schema

---

# Record Too Large

### Symptoms

```text
RecordTooLargeException
```

---

### Causes

Message exceeds broker limits.

---

### Solution

Reduce message size.

Or adjust:

```properties
max.request.size
```

and broker limits if appropriate.

Avoid sending large files through Kafka.

---

# Buffer Exhausted

### Symptoms

```text
BufferExhaustedException
```

Producer buffer becomes full.

---

### Causes

- Broker slow
- Network slow
- Buffer too small

---

### Solution

Increase:

```properties
buffer.memory
```

Or improve broker performance.

---

# Authentication Failure

### Symptoms

```text
SaslAuthenticationException
```

---

### Causes

- Wrong username
- Wrong password
- Invalid token

---

### Solution

Verify:

- Credentials
- JAAS configuration
- SASL mechanism

---

# Authorization Failure

### Symptoms

```text
TopicAuthorizationException
```

---

### Causes

Producer lacks:

```text
WRITE Permission
```

---

### Solution

Grant appropriate ACLs.

---

# SSL Errors

### Symptoms

```text
SSLHandshakeException
```

---

### Causes

- Expired certificate
- Wrong truststore
- Invalid keystore

---

### Solution

Verify:

- Certificates
- Truststore
- Keystore
- Passwords

---

# Network Errors

### Symptoms

```text
NetworkException
```

---

### Causes

- Packet loss
- Firewall
- DNS issues
- Broker unavailable

---

### Solution

Check:

- Network connectivity
- DNS
- Routing
- Firewalls

---

# Retries Exhausted

Producer retries:

```properties
retries=5
```

After all retries fail:

```text
Message Send Failed
```

---

### Solution

Investigate the root cause instead of increasing retries indefinitely.

---

# Idempotence Disabled

Suppose:

```text
Retry

↓

Duplicate Message
```

---

### Solution

Enable:

```properties
enable.idempotence=true
```

Duplicates are significantly reduced.

---

# Acknowledgement Problems

Configuration:

```properties
acks=0
```

Producer never confirms delivery.

Possible result:

```text
Message Lost
```

Recommended:

```properties
acks=all
```

---

# Metadata Fetch Failure

### Symptoms

```text
Timeout Fetching Metadata
```

---

### Causes

- Wrong bootstrap server
- Cluster unavailable
- Network failure

---

### Solution

Verify broker connectivity.

---

# High Producer Latency

Symptoms:

```text
Send()

↓

Slow Response
```

Possible causes:

- Slow brokers
- Large batches
- Compression
- Network latency

---

### Solution

Monitor:

- Request latency
- Broker CPU
- Network throughput

---

# Monitoring Producer Health

Monitor:

- Error rate
- Retry rate
- Request latency
- Batch size
- Compression ratio
- Delivery timeout
- Requests/sec

These metrics help identify producer issues early.

---

# Troubleshooting Workflow

```text
Producer Error

↓

Check Logs

↓

Check Broker

↓

Check Topic

↓

Check Network

↓

Check Security

↓

Check Serialization

↓

Identify Root Cause

↓

Resolve

↓

Retry
```

---

# Quick Diagnosis Table

| Problem | Possible Cause | Recommended Action |
|----------|----------------|--------------------|
| TimeoutException | Slow broker | Check broker health |
| UnknownTopicOrPartition | Missing topic | Create or verify topic |
| SerializationException | Wrong serializer | Verify serializer configuration |
| RecordTooLargeException | Large message | Reduce message size |
| TopicAuthorizationException | Missing ACL | Grant WRITE permission |
| SSLHandshakeException | Certificate issue | Verify SSL configuration |
| BufferExhaustedException | Producer buffer full | Increase buffer or fix broker bottleneck |
| NetworkException | Connectivity issue | Verify network and broker availability |

---

# Best Practices

- Enable idempotent producers.
- Use `acks=all` for critical data.
- Configure sensible retry limits.
- Monitor producer latency and retries.
- Keep messages reasonably small.
- Validate serializers during development.
- Secure producers using SSL/TLS and SASL.
- Monitor broker health alongside producer metrics.
- Log failed sends for troubleshooting.
- Test producer recovery scenarios before production deployment.

---

# Common Mistakes

- Using `acks=0` in production.
- Sending oversized messages.
- Ignoring retry failures.
- Hardcoding broker addresses.
- Misconfiguring serializers.
- Ignoring authentication failures.
- Disabling idempotence.
- Treating retries as a permanent solution instead of fixing the underlying issue.

---

# Summary

Producer errors can arise from broker failures, networking issues, security configuration, serialization problems, or improper producer settings. Understanding these failures and following a structured troubleshooting process enables engineers to identify root causes quickly and build resilient producer applications. Proper configuration, monitoring, retries, idempotence, and security are key to ensuring reliable message delivery in production Kafka environments.

---

# Key Takeaways

- Producer errors may originate from brokers, networks, security, serialization, or configuration.
- Monitor producer retries, latency, and error rates continuously.
- Enable idempotence and use `acks=all` for reliable delivery.
- Keep message sizes within configured limits.
- Verify authentication, authorization, and SSL configuration.
- Use structured troubleshooting to isolate root causes.
- Avoid masking persistent problems by simply increasing retries.
- Reliable producers are a critical component of production-grade Kafka systems.