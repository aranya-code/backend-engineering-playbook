# Amazon S3 Standard-IA

---

# Introduction

Not every object stored in Amazon S3 is accessed frequently. Many production workloads contain data that must remain immediately available but is only retrieved occasionally.

Examples include completed project documents, monthly reports, database backups, historical invoices, and compliance records.

Storing these objects in Amazon S3 Standard provides excellent performance but often results in unnecessary storage costs.

Amazon **S3 Standard-Infrequent Access (S3 Standard-IA)** is designed specifically for this scenario. It offers lower storage costs while maintaining high durability, immediate retrieval, and multi-Availability Zone resilience.

---

# Why S3 Standard-IA Exists

Imagine an online banking system.

Customer statements are generated every month.

During the first few weeks, customers frequently download them.

After several months, access becomes much less common.

However, customers still expect statements to be available immediately whenever they need them.

This workload doesn't require S3 Standard, but archive storage would introduce retrieval delays.

S3 Standard-IA provides the ideal balance.

> 💡 **Engineering Insight**
>
> Standard-IA is optimized for data that is **rarely accessed but must be available immediately** when requested.

---

# Characteristics

| Feature | Amazon S3 Standard-IA |
|---------|------------------------|
| Access Pattern | Infrequent |
| Retrieval Time | Milliseconds |
| Availability | 99.9% |
| Durability | 99.999999999% (11 nines) |
| Availability Zones | Multiple |
| Retrieval Charges | Yes |
| Minimum Storage Duration | 30 Days |

Unlike Glacier storage classes, objects do **not** require a restore operation before they can be accessed.

---

# Architecture

```text
            Client
               │
               ▼
      Amazon S3 Standard-IA
               │
      ┌────────┼────────┐
      │        │        │
    AZ-A     AZ-B     AZ-C
```

Objects remain redundantly stored across multiple Availability Zones, providing protection against hardware and Availability Zone failures.

---

# Cost Model

Compared to Amazon S3 Standard:

Advantages:

- Lower storage cost

Trade-offs:

- Retrieval charges
- 30-day minimum storage duration
- Slightly lower availability target

Because retrieval incurs an additional charge, Standard-IA is not suitable for frequently accessed data.

---

# Typical Workloads

S3 Standard-IA is commonly used for:

- Database backups
- Disaster recovery copies
- Historical reports
- Archived project documents
- Medical records
- Financial statements
- Long-term application logs

These objects remain available immediately but are accessed only occasionally.

> 🏗️ **Production Pattern**
>
> Use Lifecycle Rules to automatically transition inactive objects from S3 Standard to S3 Standard-IA after 30 or 60 days of inactivity.

---

# When Not to Use Standard-IA

Avoid Standard-IA for:

- Frequently accessed images
- Website assets
- Application configuration files
- Active user content
- Temporary files

In these scenarios, retrieval charges can outweigh storage savings.

---

# Best Practices

- Transition objects automatically using Lifecycle Rules.
- Monitor retrieval frequency.
- Estimate retrieval costs before migrating workloads.
- Keep active production data in S3 Standard.

---

# Common Mistakes

- Moving active workloads into Standard-IA.
- Ignoring retrieval charges.
- Deleting objects before the 30-day minimum storage duration.
- Assuming lower storage cost always means lower overall cost.

> ⚠️ **Common Mistake**
>
> Standard-IA reduces storage costs but introduces retrieval charges. Applications that access objects frequently often cost less when using S3 Standard.

---

# Real-World Example

A hospital stores patient discharge summaries.

Recent summaries are accessed frequently by healthcare staff and remain in Amazon S3 Standard.

After 60 days, Lifecycle Rules automatically transition them to S3 Standard-IA.

Doctors can still retrieve records instantly whenever required, while the hospital significantly reduces long-term storage costs.

---

# Key Takeaways

Amazon S3 Standard-IA is designed for data that is accessed infrequently but must remain immediately available. It reduces storage costs while maintaining high durability and multi-Availability Zone resilience, making it an excellent choice for backups, historical records, and other infrequently accessed production data.

In the next chapter, we'll explore **Amazon S3 One Zone-IA** and understand when storing infrequently accessed data in a single Availability Zone can provide additional cost savings.
