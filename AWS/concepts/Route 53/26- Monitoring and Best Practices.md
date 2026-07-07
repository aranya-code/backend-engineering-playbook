# Monitoring and Best Practices

## Why Monitor Route 53?

DNS failures are often silent until a customer reports "your site is down" — proactive monitoring catches issues before they become incidents.

## What to Monitor

| Signal | Why It Matters |
|---|---|
| Health check status changes | Direct signal of failover-triggering events |
| Query volume (via CloudWatch metrics) | Sudden spikes can indicate a DDoS attempt, DNS amplification abuse, or a runaway client retry loop |
| Query logging (Resolver / hosted zone) | Deep visibility into what's actually being queried, from where |
| DNSSEC validation failures | Signals a signing/chain-of-trust misconfiguration |

## CloudWatch Integration

Route 53 health checks automatically publish metrics to CloudWatch (`HealthCheckStatus`, `HealthCheckPercentageHealthy`), which can drive CloudWatch Alarms — including alarms that page an on-call engineer the moment a health check flips unhealthy, independent of whatever failover routing does automatically.

## Best Practices

| Practice | Reason |
|---|---|
| Use Alias records for all AWS resource targets | Correctness (tracks IP changes) and avoids extra query charges |
| Attach health checks to every failover/weighted record that matters | Failover routing without a health check silently does nothing |
| Keep TTLs low on records involved in failover or migrations | Bounds propagation/recovery time |
| Use private hosted zones for internal-only names | Keeps internal topology out of public DNS entirely |
| Enable query logging on production zones | Gives you data during an incident instead of guessing |
| Set a Default record on every geolocation configuration | Prevents silent NXDOMAIN for unmapped countries |
| Enable DNSSEC on customer-facing production domains | Meaningful protection against DNS spoofing for relatively low ongoing effort |
| Regularly audit for orphaned records pointing at decommissioned resources | Prevents subdomain takeover |

## Alerting Philosophy

Treat a health check state change as an incident-worthy signal on its own — don't rely solely on "did failover routing handle it" as your monitoring strategy, since a silent, successful failover can still represent a real capacity or cost problem worth investigating.
