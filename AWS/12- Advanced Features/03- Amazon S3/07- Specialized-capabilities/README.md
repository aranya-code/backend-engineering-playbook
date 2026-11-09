# README

## Overview

This section covers specialized S3 capabilities that extend object access beyond basic bucket operations. It includes S3 Object Lambda, Multi-Region Access Points, and advanced object access patterns for applications that need transformation, regional routing, or more sophisticated access architectures.

Use these documents when standard S3 endpoints and direct object reads do not fully meet application requirements. Evaluate the additional policies, supported operations, network paths, latency, availability, and cost introduced by each capability before adopting it.

## Navigation

| # | Document | Description |
|---|---|---|
| 01 | [S3 Object Lambda](./01-%20S3%20Object%20Lambda.md) | Transform or filter object data during retrieval through an Object Lambda access point and supporting compute |
| 02 | [S3 Multi-Region Access Points](./02-%20S3%20Multi-Region%20Access%20Points.md) | Provide a global access endpoint that routes requests across configured regional buckets |
| 03 | [Advanced Object Access Patterns](./03-%20Advanced%20Object%20Access%20Patterns.md) | Explore advanced object access designs and the trade-offs involved in application integration |

## Suggested Reading Order

1. Review advanced access patterns to identify the application requirement.
2. Study Object Lambda when responses need request-time transformation or filtering.
3. Study Multi-Region Access Points when applications need a global endpoint across Regions.
4. Validate authorization, routing, failure behavior, and cost with an end-to-end test.

## Design Considerations

- Prefer native S3 operations when they satisfy the requirement; specialized capabilities add architecture and operational complexity.
- Define the exact read or write path and identify which bucket, access point, or supporting compute component handles each request.
- Test IAM and resource policies independently, including cross-account and cross-Region boundaries where applicable.
- Measure latency and cost under realistic request patterns and test regional failure behavior where relevant.

## Key Takeaways

- Specialized S3 capabilities solve distinct access and routing problems; select them based on a concrete application requirement.
- Object Lambda introduces a transformation path and supporting compute that must be secured and operated.
- Multi-Region Access Points provide a global access layer but do not remove the need to design replication and regional data consistency.
- Validate policies, routing, failure handling, latency, and cost before production adoption.
