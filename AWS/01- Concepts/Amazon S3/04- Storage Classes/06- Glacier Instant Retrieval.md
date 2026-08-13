# Amazon S3 Glacier Instant Retrieval

---

# Introduction

Not all archived data is rarely needed. Some information is retained for long periods but must still be available within milliseconds whenever it is requested.

Examples include medical images, legal documents, media assets, and compliance records. These workloads benefit from lower archival storage costs without the delays associated with traditional archive retrieval.

**Amazon S3 Glacier Instant Retrieval** is designed for this exact use case. It provides archive-class pricing while delivering millisecond retrieval performance.

---

# Why Glacier Instant Retrieval Exists

Consider a hospital that stores patient X-ray images.

Most images are rarely accessed after the patient is discharged.

However, doctors may need immediate access during a follow-up consultation.

Traditional archive storage requiring hours to restore would not meet this requirement.

Glacier Instant Retrieval offers lower storage costs while preserving instant access.

> 💡 **Engineering Insight**
>
> Glacier Instant Retrieval is an archive storage class with **millisecond retrieval**, making it suitable for data that is cold but cannot tolerate restore delays.

---

# Characteristics

| Feature | Amazon S3 Glacier Instant Retrieval |
|---------|--------------------------------------|
| Access Pattern | Rare |
| Retrieval Time | Milliseconds |
| Availability | 99.9% |
| Durability | 99.999999999% (11 nines) |
| Availability Zones | Multiple |
| Retrieval Charges | Yes |
| Minimum Storage Duration | 90 Days |

Objects remain online and immediately accessible without initiating a restore operation.

---

# Architecture

```text
             Client
                │
                ▼
S3 Glacier Instant Retrieval
                │
      ┌─────────┼─────────┐
      │         │         │
    AZ-A      AZ-B      AZ-C
```

Data is redundantly stored across multiple Availability Zones while using infrastructure optimized for archival workloads.

---

# Typical Workloads

Glacier Instant Retrieval is well suited for:

- Medical imaging
- Legal documents
- Digital media archives
- Compliance records
- Long-term engineering documents
- Historical project files

These objects are rarely accessed but require immediate availability when requested.

> 🏗️ **Production Pattern**
>
> Use Lifecycle Rules to transition objects from S3 Standard-IA or Intelligent-Tiering into Glacier Instant Retrieval after they become inactive but still require immediate access.

---

# Cost Considerations

Advantages:

- Lower storage cost than Standard-IA
- Instant retrieval
- Archive-class pricing

Trade-offs:

- Retrieval charges apply
- 90-day minimum storage duration
- Not economical for frequently accessed objects

Always estimate both storage and retrieval costs before selecting this storage class.

---

# When Not to Use Glacier Instant Retrieval

Avoid this storage class for:

- Frequently accessed application assets
- Static website files
- Active user content
- Temporary processing data
- High-frequency analytics workloads

These workloads are generally better suited to S3 Standard or Intelligent-Tiering.

---

# Best Practices

- Use Lifecycle Rules for automatic transitions.
- Keep active data in S3 Standard.
- Monitor retrieval frequency.
- Review storage patterns periodically using S3 Storage Lens.

---

# Common Mistakes

- Assuming archive storage always requires restore operations.
- Moving frequently accessed data to reduce storage costs.
- Ignoring retrieval charges.
- Deleting objects before the 90-day minimum storage period.

> ⚠️ **Common Mistake**
>
> Glacier Instant Retrieval delivers millisecond access, but it is still an archive storage class. Frequent retrievals can eliminate the expected cost savings.

---

# Real-World Example

A media company stores completed video productions.

New productions remain in Amazon S3 Standard while actively edited.

After 120 days, Lifecycle Rules transition the videos to Glacier Instant Retrieval.

Editors can still access archived projects instantly whenever a client requests revisions, while the company significantly reduces long-term storage costs.

---

# Key Takeaways

Amazon S3 Glacier Instant Retrieval provides archive-class storage with millisecond retrieval performance. It is an excellent choice for long-lived data that is rarely accessed but must remain immediately available without restoration delays.

In the next chapter, we'll explore **Amazon S3 Glacier Flexible Retrieval** and learn how longer retrieval times can further reduce storage costs for archival workloads.
