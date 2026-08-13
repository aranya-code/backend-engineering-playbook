# Choosing the Right Storage Class

---

# Introduction

Selecting the correct Amazon S3 storage class is one of the most important cost optimization decisions in AWS. Every storage class provides the same exceptional durability, but they differ in storage cost, retrieval charges, availability, retrieval latency, and minimum storage duration.

There is no universally "best" storage class. The right choice depends entirely on your workload's access pattern and business requirements.

---

# Decision Factors

Before selecting a storage class, answer the following questions:

- How often is the object accessed?
- How quickly must it be retrieved?
- How long will it be stored?
- Can the data be recreated?
- Are retrieval charges acceptable?
- Are regulatory retention requirements involved?

> 💡 **Engineering Insight**
>
> Storage class selection should be driven by access patterns—not by storage price alone.

---

# Storage Class Comparison

| Storage Class | Best For | Retrieval | Retrieval Fee | Multi-AZ |
|---------------|----------|-----------|---------------|----------|
| S3 Standard | Frequently accessed data | Milliseconds | No | Yes |
| Intelligent-Tiering | Unknown access patterns | Milliseconds | Depends on tier | Yes |
| Standard-IA | Infrequent access | Milliseconds | Yes | Yes |
| One Zone-IA | Re-creatable data | Milliseconds | Yes | No |
| Glacier Instant Retrieval | Cold data needing instant access | Milliseconds | Yes | Yes |
| Glacier Flexible Retrieval | Archive workloads | Minutes–Hours | Yes | Yes |
| Glacier Deep Archive | Long-term retention | Hours | Yes | Yes |

---

# Decision Tree

```text
Need immediate access?
        │
   ┌────┴─────┐
   │          │
 Yes         No
   │          │
Frequent?   Archive?
   │          │
 ┌─┴───┐      │
 │     │      │
Yes   No      ▼
 │     │   Glacier
 ▼     ▼
S3   Standard-IA
Standard
```

If access patterns are unpredictable, choose **S3 Intelligent-Tiering**.

---

# Example Workloads

| Workload | Recommended Storage Class |
|----------|---------------------------|
| Website assets | S3 Standard |
| User profile images | S3 Standard |
| Database backups | S3 Standard-IA |
| Temporary render outputs | S3 One Zone-IA |
| Medical images | Glacier Instant Retrieval |
| Audit logs | Glacier Flexible Retrieval |
| Regulatory archives | Glacier Deep Archive |

---

# Lifecycle Strategy

A common production lifecycle looks like this:

```text
Day 0
│
▼
S3 Standard
│
▼
30 Days
│
▼
S3 Standard-IA
│
▼
180 Days
│
▼
Glacier Flexible Retrieval
│
▼
7 Years
│
▼
Glacier Deep Archive
```

Lifecycle Rules automate these transitions without application changes.

> 🏗️ **Production Pattern**
>
> Combine Lifecycle Rules with Storage Lens reports to continuously optimize storage costs based on real usage.

---

# Best Practices

- Match storage classes to actual access patterns.
- Use Intelligent-Tiering when access is unpredictable.
- Automate transitions using Lifecycle Rules.
- Monitor retrieval costs as well as storage costs.
- Review storage strategy periodically as workloads evolve.

---

# Common Mistakes

- Keeping all objects in S3 Standard.
- Selecting archive storage for interactive applications.
- Ignoring retrieval charges.
- Forgetting minimum storage duration requirements.
- Optimizing only for storage price.

> ⚠️ **Common Mistake**
>
> The cheapest storage class is not always the lowest-cost solution. Retrieval frequency, restore delays, and minimum storage durations all affect the total cost of ownership.

---

# Key Takeaways

Amazon S3 offers multiple storage classes to balance cost, performance, and availability for different workloads. Understanding access patterns and automating lifecycle transitions allows organizations to significantly reduce storage costs without compromising application requirements.

This concludes the **Storage Classes** section. In the next section, we'll begin **Versioning**, starting with how Amazon S3 protects objects from accidental deletion and overwrites.


## Current platform note: latency-sensitive data

Include S3 Express One Zone in the decision when a workload needs consistent single-digit millisecond access and can tolerate a single-AZ storage model. For general production data requiring multi-AZ resilience, compare the general-purpose S3 storage classes instead.
