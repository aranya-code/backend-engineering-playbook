# VPC Flow Logs

VPC Flow Logs capture information about IP traffic going to and from network interfaces in your VPC. They are an essential tool for network monitoring, security analysis, troubleshooting connectivity issues, and meeting compliance requirements for network traffic auditing.

Flow Logs do not capture actual packet content — they capture metadata about each network flow (source, destination, ports, protocol, action, bytes).

---

# What Flow Logs Capture

Each flow log record contains:

```text
version account-id interface-id srcaddr dstaddr srcport dstport protocol packets bytes start end action log-status
```

## Example Record

```text
2 123456789012 eni-abc123 10.0.1.5 52.94.76.5 49152 443 6 15 7500 1688000000 1688000060 ACCEPT OK
```

| Field | Value | Meaning |
|-------|-------|---------|
| version | 2 | Log format version |
| account-id | 123456789012 | AWS account |
| interface-id | eni-abc123 | Network interface |
| srcaddr | 10.0.1.5 | Source IP |
| dstaddr | 52.94.76.5 | Destination IP |
| srcport | 49152 | Source port |
| dstport | 443 | Destination port (HTTPS) |
| protocol | 6 | TCP |
| packets | 15 | Packet count |
| bytes | 7500 | Byte count |
| start | 1688000000 | Start timestamp |
| end | 1688000060 | End timestamp |
| action | ACCEPT | Traffic was allowed |
| log-status | OK | Logging successful |

---

# Capture Levels

| Level | Scope | Use Case |
|-------|-------|----------|
| **VPC** | All ENIs in the entire VPC | Broad network visibility |
| **Subnet** | All ENIs in a specific subnet | Subnet-level monitoring |
| **ENI** | A specific network interface | Targeted troubleshooting |

Multiple flow logs can be active simultaneously at different levels.

---

# Log Destinations

| Destination | Best For |
|-------------|----------|
| **CloudWatch Logs** | Real-time analysis, metric filters, alarms |
| **Amazon S3** | Long-term storage, batch analysis, cost-effective |
| **Kinesis Data Firehose** | Streaming to Splunk, Datadog, OpenSearch |

```text
VPC Flow Logs
      │
      ├──► CloudWatch Logs ──► Metric Filters ──► Alarms
      │
      ├──► S3 Bucket ──► Athena Queries ──► Analysis
      │
      └──► Kinesis Firehose ──► OpenSearch ──► Dashboards
```

---

# What Flow Logs Do NOT Capture

- Actual packet content (payload)
- DNS queries to Route 53 Resolver
- DHCP traffic
- Traffic to the instance metadata service (169.254.169.254)
- Traffic to the VPC DNS server (x.x.x.2)
- Traffic to/from Windows license activation
- NTP traffic

---

# Security Use Cases

## Detect Rejected Traffic

Filter for `REJECT` actions to find unauthorized access attempts:

```text
# Rejected SSH attempts
Filter: [action = "REJECT", dstport = 22]
```

## Detect Data Exfiltration

Monitor for unusual outbound data volumes:

```text
# Large outbound transfers from private instances
Filter: [srcaddr starts with "10.0.3", bytes > 1000000]
```

## Identify Port Scanning

Look for patterns of connection attempts across many ports:

```text
# Multiple rejected ports from same source
Filter: [action = "REJECT", srcaddr = "x.x.x.x", multiple dstports]
```

## Compliance Auditing

Prove that only authorized traffic flows through the network.

---

# Analyzing Flow Logs with Athena

For S3-stored flow logs, use Athena for SQL-based analysis:

```sql
-- Top 10 rejected source IPs
SELECT srcaddr, COUNT(*) as reject_count
FROM vpc_flow_logs
WHERE action = 'REJECT'
GROUP BY srcaddr
ORDER BY reject_count DESC
LIMIT 10;

-- Traffic volume by destination port
SELECT dstport, SUM(bytes) as total_bytes
FROM vpc_flow_logs
WHERE action = 'ACCEPT'
GROUP BY dstport
ORDER BY total_bytes DESC
LIMIT 20;
```

---

# Best Practices

| Practice | Detail |
|----------|--------|
| Enable at VPC level | Captures all traffic in one configuration |
| Send to S3 for long-term | More cost-effective than CloudWatch for storage |
| Use CloudWatch for real-time | Create metric filters and alarms for security events |
| Use custom log format | Include only needed fields to reduce storage costs |
| Integrate with GuardDuty | GuardDuty analyzes flow logs for threat detection |
| Set S3 lifecycle policies | Transition old logs to Glacier, expire after retention period |

---

# Key Takeaways

- Flow Logs capture network flow metadata (not packet content).
- Capture at VPC, Subnet, or ENI level — VPC level provides broadest visibility.
- Send to CloudWatch for real-time monitoring, S3 for batch analysis, Firehose for streaming.
- Use Athena for SQL analysis of S3-stored flow logs.
- Flow Logs are essential for security monitoring, troubleshooting, and compliance.
- GuardDuty analyzes Flow Logs automatically for threat detection.

---
