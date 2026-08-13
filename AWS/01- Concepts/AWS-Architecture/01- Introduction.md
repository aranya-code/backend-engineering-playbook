# AWS Architecture — Introduction

This folder is different from the single-service deep dives elsewhere in this repo (EC2, S3, IAM, Route 53). Those answer "how does this AWS service work?" This folder answers a different question: **"how do you design a system that survives real-world failure, scales under load, and stays maintainable, using AWS as the substrate?"**

## Why This Is a Distinct Skill From Knowing Services

Knowing that DynamoDB has single-digit-millisecond latency, or that SQS guarantees at-least-once delivery, is service knowledge. Knowing *when* to reach for a queue instead of a direct synchronous call, or *why* a circuit breaker matters even though your load balancer already does health checks, is architecture judgment. Senior-level interviews and real production incidents both live in this second category far more than the first.

## What This Folder Covers

- **Resilience** — designing for failure as the default assumption, not the exception
- **Scalability** — patterns for handling growth in traffic and data without a rewrite
- **Decoupling** — breaking synchronous dependency chains that turn one slow service into a full outage
- **Availability** — multi-AZ and multi-region design, and honest disaster recovery trade-offs
- **System style** — microservices vs. serverless as architectural choices, not just deployment targets
- **Judgment** — anti-patterns to recognize, and how to document architecture decisions defensibly

## What This Folder Deliberately Does Not Cover

- Security architecture specifically — see `AWS-Security`
- Deep API/console mechanics of any single service — see that service's own folder (EC2, S3, IAM, etc.)

## How to Use This Folder

Most of these patterns are not AWS-specific in origin — circuit breakers, CQRS, and the Saga pattern all predate AWS. What matters here is how each pattern maps onto specific AWS services, and the trade-offs that are specific to operating them at AWS's scale and pricing model.
