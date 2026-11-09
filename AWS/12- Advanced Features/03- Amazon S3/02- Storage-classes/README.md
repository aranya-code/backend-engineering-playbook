# README

## Overview

This section explains Amazon S3 storage classes and how to select them according to access frequency, retrieval latency, availability requirements, resilience, and cost. It covers the primary S3 storage classes from frequently accessed object storage through archival tiers, along with a comparison framework for workload-level decisions.

Use these documents when defining storage policies, estimating lifecycle costs, or deciding where application data should reside over its lifecycle. Storage-class selection should account for retrieval charges, minimum storage duration, minimum billable object size, monitoring charges, and restore requirements—not storage price alone.

## Navigation

| # | Document | Description |
|---|---|---|
| 01 | [Storage Classes Overview](./01-%20Storage%20Classes%20Overview.md) | Storage-class concepts, selection dimensions, and the role of access patterns in storage design |
| 02 | [S3 Standard](./02-%20S3%20Standard.md) | General-purpose storage for frequently accessed data requiring low-latency access |
| 03 | [S3 Intelligent-Tiering](./03-%20S3%20Intelligent-Tiering.md) | Automatic tiering for changing or uncertain access patterns and its monitoring considerations |
| 04 | [S3 Standard-Infrequent Access](./04-%20S3%20Standard-Infrequent%20Access.md) | Lower storage cost for infrequently accessed data that still needs rapid access |
| 05 | [S3 One Zone-Infrequent Access](./05-%20S3%20One%20Zone-Infrequent%20Access.md) | Lower-cost infrequent-access storage for data that can tolerate single-Availability-Zone resilience |
| 06 | [S3 Glacier Instant Retrieval](./06-%20S3%20Glacier%20Instant%20Retrieval.md) | Archive-oriented storage for rarely accessed data that still requires millisecond retrieval |
| 07 | [S3 Glacier Flexible Retrieval](./07-%20S3%20Glacier%20Flexible%20Retrieval.md) | Archive storage with configurable restore times and retrieval options |
| 08 | [S3 Glacier Deep Archive](./08-%20S3%20Glacier%20Deep%20Archive.md) | Lowest-cost long-term archive tier for data with infrequent access and extended restore times |
| 09 | [Storage Class Comparison and Selection](./09-%20Storage%20Class%20Comparison%20and%20Selection.md) | Side-by-side decision criteria, cost drivers, and workload-based selection guidance |

## Suggested Reading Order

1. Read the overview to understand the decision dimensions.
2. Review individual classes based on the workload's access and recovery requirements.
3. Use the comparison document to validate the final choice against total cost and operational constraints.

## Key Takeaways

- Choose a storage class from measured access patterns, availability needs, recovery objectives, and total cost.
- Include retrieval fees, minimum storage duration, minimum billable object size, and monitoring charges in cost estimates.
- Glacier restore workflows must be reflected in application behavior and recovery objectives.
- Reassess storage-class choices as access patterns and business requirements change.
