# Amazon API Gateway — Operations & Observability

This section covers the essential observability and operations capabilities required to monitor, troubleshoot, and operate production-grade APIs on AWS. API Gateway integrates natively with **Amazon CloudWatch** and **AWS X-Ray** for deep visibility into request processing, latency, errors, and performance.

---

## Quick Navigation

| # | File | Topic |
|---|------|-------|
| 01 | [CloudWatch Metrics](./01-%20CloudWatch%20Metrics.md) | Request count, latency, error rates, throttling, and cache performance metrics |
| 02 | [CloudWatch Logs](./02-%20CloudWatch%20Logs.md) | Execution logs, logging levels, data tracing, log groups, and troubleshooting requests |
| 03 | [Access Logs](./03-%20Access%20Logs.md) | Customizable access logs, `$context` variables, JSON log formats, and production logging |
| 03 | [API Caching](./03-%20API%20Caching.md) | Configuring and tuning API Gateway response caching |
| 04 | [X-Ray Tracing](./04-%20X-Ray%20Tracing.md) | Distributed tracing, traces, segments, service maps, and end-to-end request visualization |
| 05 | [Monitoring & Alarms](./05-%20Monitoring%20%26%20Alarms.md) | CloudWatch Alarms, SNS notifications, dashboards, composite alarms, and monitoring strategies |
| 06 | [Common Performance Metrics](./06-%20Common%20Performance%20Metrics.md) | Key API Gateway performance metrics, how to interpret them, and diagnosing production issues |
| 07 | [Cache Invalidation](./07-%20Cache%20Invalidation.md) | Strategies and methods for invalidating cached responses |
| 08 | [Request & Response Compression](./08-%20Request%20%26%20Response%20Compression.md) | Enabling and configuring payload compression to reduce latency and data transfer costs |

---

## Recommended Study Order

1. [CloudWatch Metrics](./01-%20CloudWatch%20Metrics.md)
2. [CloudWatch Logs](./02-%20CloudWatch%20Logs.md)
3. [Access Logs](./03-%20Access%20Logs.md)
4. [API Caching](./03-%20API%20Caching.md)
5. [X-Ray Tracing](./04-%20X-Ray%20Tracing.md)
6. [Monitoring & Alarms](./05-%20Monitoring%20%26%20Alarms.md)
7. [Common Performance Metrics](./06-%20Common%20Performance%20Metrics.md)
8. [Cache Invalidation](./07-%20Cache%20Invalidation.md)
9. [Request & Response Compression](./08-%20Request%20%26%20Response%20Compression.md)

---

## Related Sections

- [01 - Concepts → Amazon API Gateway](../../01-%20Concepts/07-%20Amazon%20API%20Gateway/README.md)
- [02 - Architecture → Amazon API Gateway](../../02-%20Architecture/07-%20Amazon%20API%20Gateway/README.md)
- [05 - Security → Amazon API Gateway](../../05-%20Security/06-%20Amazon%20API%20Gateway/README.md)
- [06 - Deployment → Amazon API Gateway](../../06-%20Deployment/01-%20Amazon%20API%20Gateway/README.md)
- [07 - Troubleshooting → Amazon API Gateway](../../07-%20Troubleshooting/06-%20Amazon%20API%20Gateway/README.md)
- [08 - Interview Questions → Amazon API Gateway](../../08-%20Interview%20Questions/07-%20Amazon%20API%20Gateway/README.md)
- [09 - Integrations → Amazon API Gateway](../../09-%20Integrations/01-%20Amazon%20API%20Gateway/README.md)
- [10 - Hands On → Amazon API Gateway](../../10-%20Hands%20On/01-%20Amazon%20API%20Gateway/README.md)
- [11 - Best Practices → Amazon API Gateway](../../11-%20Best%20Practices/01-%20Amazon%20API%20Gateway/README.md)
