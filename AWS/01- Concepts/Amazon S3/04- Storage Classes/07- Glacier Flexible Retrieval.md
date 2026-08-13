# Amazon S3 Glacier Flexible Retrieval

---

# Introduction

Many organizations are required to retain data for months or years even though it is accessed only occasionally. Examples include compliance records, historical backups, audit logs, scientific datasets, and long-term business documents.

Keeping this data in high-performance storage unnecessarily increases costs. At the same time, retrieving the data within milliseconds is often not a business requirement.

**Amazon S3 Glacier Flexible Retrieval** is designed for these workloads. It provides significantly lower storage costs than frequently accessed storage classes while allowing data to be restored whenever needed.

Formerly known as **Amazon S3 Glacier**, this storage class is one of the most widely used archival solutions on AWS.

---

# Why Glacier Flexible Retrieval Exists

Imagine a financial institution that stores transaction records for seven years.

Most records are never accessed again.

However, regulators or auditors may occasionally request historical data.

Waiting a few minutes or even a few hours is acceptable.

Paying for high-performance storage throughout the entire retention period is not.

Glacier Flexible Retrieval provides a better balance between storage cost and retrieval time.

> 💡 **Engineering Insight**
>
> Glacier Flexible Retrieval is optimized for **rarely accessed archival data** where lower storage cost is more important than immediate retrieval.

---

# Characteristics

| Feature | Amazon S3 Glacier Flexible Retrieval |
|---------|--------------------------------------|
| Access Pattern | Rare |
| Retrieval Time | Minutes to Hours |
| Availability | 99.9% |
| Durability | 99.999999999% (11 nines) |
| Availability Zones | Multiple |
| Retrieval Charges | Yes |
| Minimum Storage Duration | 90 Days |

Unlike Glacier Instant Retrieval, objects must first be restored before they can be downloaded.

---

# Restore Workflow

Objects stored in Glacier Flexible Retrieval cannot be read immediately.

A restore request must first be initiated.

```text
Client
   │
Request Restore
   │
   ▼
Amazon S3
   │
Restore Object
   │
   ▼
Temporary Accessible Copy
   │
   ▼
Download Object
```

The restored copy remains available for a configurable number of days.

The archived object itself is never modified.

---

# Retrieval Options

Amazon S3 offers multiple retrieval speeds.

### Expedited Retrieval

- Fastest option
- Typically available within minutes
- Higher retrieval cost

---

### Standard Retrieval

- Most commonly used
- Typically completes within a few hours
- Balanced cost and performance

---

### Bulk Retrieval

- Lowest retrieval cost
- Suitable for large datasets
- Longest retrieval time

Organizations select the retrieval option based on business urgency.

---

# Typical Workloads

Glacier Flexible Retrieval is ideal for:

- Long-term database backups
- Compliance archives
- Financial records
- Audit logs
- Historical project files
- Digital preservation
- Scientific research data

These datasets are retained for extended periods but accessed infrequently.

> 🏗️ **Production Pattern**
>
> Automatically transition inactive objects from S3 Standard-IA or Glacier Instant Retrieval into Glacier Flexible Retrieval using Lifecycle Rules.

---

# Cost Considerations

Advantages:

- Very low storage cost
- Multiple retrieval options
- Excellent durability

Trade-offs:

- Restore operation required
- Retrieval charges apply
- 90-day minimum storage duration

Applications requiring immediate access should generally avoid this storage class.

---

# When Not to Use Glacier Flexible Retrieval

Avoid this storage class for:

- Frequently accessed content
- Website assets
- User profile images
- Production application data
- Interactive workloads

Waiting for restore operations would negatively impact user experience.

---

# Best Practices

- Archive only inactive data.
- Automate transitions using Lifecycle Rules.
- Choose retrieval speed based on business requirements.
- Monitor archive storage costs.
- Test restore procedures periodically.

---

# Common Mistakes

- Expecting immediate downloads.
- Archiving active production data.
- Forgetting retrieval charges.
- Ignoring the 90-day minimum storage duration.
- Never testing restore workflows.

> ⚠️ **Common Mistake**
>
> Uploading data to Glacier Flexible Retrieval does not automatically make it available for download. A restore request is required before the object can be accessed.

---

# Real-World Example

A healthcare organization stores diagnostic reports for regulatory compliance.

Recent reports remain in Amazon S3 Standard.

After one year, Lifecycle Rules automatically transition them to Glacier Flexible Retrieval.

When auditors request historical records, administrators restore only the required objects, reducing long-term storage costs while maintaining compliance.

---

# Key Takeaways

Amazon S3 Glacier Flexible Retrieval is designed for archival workloads where storage cost is more important than immediate accessibility. By accepting restore delays in exchange for lower storage pricing, organizations can archive large volumes of infrequently accessed data economically.

In the next chapter, we'll explore **Amazon S3 Glacier Deep Archive**, the lowest-cost Amazon S3 storage class for long-term data retention and regulatory compliance.
