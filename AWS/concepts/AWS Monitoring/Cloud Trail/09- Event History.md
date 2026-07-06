# AWS CloudTrail Event History

Event History is a built-in CloudTrail feature that automatically records **Management Events** for the last **90 days**.

Unlike Trails, Event History requires **no additional configuration** and is available immediately after creating an AWS account.

------------------------------------------------------------------------

# What is Event History?

Event History is the quickest way to view recent AWS API activity.

It allows administrators to search and investigate Management Events without creating a Trail.

------------------------------------------------------------------------

# Key Characteristics

- Automatically enabled
- Stores Management Events
- Retains events for 90 days
- No additional cost
- No Trail required
- Searchable from the AWS Console

------------------------------------------------------------------------

# What Events are Stored?

Event History includes:

- EC2 Management Events
- IAM Events
- VPC Changes
- Lambda Configuration Changes
- RDS Management Events
- S3 Bucket Management Events

It does **not** include:

- Data Events
- Network Activity Events

------------------------------------------------------------------------

# Searching Event History

You can search using:

- Event Name
- Resource Name
- IAM User
- AWS Region
- Event Source
- Time Range

Example:

```text
Event Name

↓

RunInstances
```

------------------------------------------------------------------------

# Event History Workflow

```text
AWS API Call

↓

CloudTrail

↓

Event History

↓

AWS Console Search
```

------------------------------------------------------------------------

# Event Retention

CloudTrail Event History stores Management Events for **90 days**.

To retain logs beyond 90 days:

```text
CloudTrail Trail

↓

Amazon S3

↓

Long-Term Storage
```

------------------------------------------------------------------------

# Real-World Example

An administrator notices that an EC2 instance has disappeared.

Using Event History, they search for:

```text
TerminateInstances
```

CloudTrail displays:

- IAM User
- Timestamp
- AWS Region
- Source IP
- Request Parameters

This helps determine who terminated the instance and when.

------------------------------------------------------------------------

# Event History vs Trail

| Event History | Trail |
|---------------|-------|
| 90-day retention | Long-term retention |
| Management Events only | All selected event types |
| No setup required | Requires configuration |
| Search in Console | Logs stored in Amazon S3 |

------------------------------------------------------------------------

# Best Practices

- Use Event History for quick investigations.
- Create Trails for compliance and long-term retention.
- Enable Multi-Region Trails.
- Archive logs in Amazon S3.
- Monitor sensitive API activity using CloudWatch.

------------------------------------------------------------------------

# Key Takeaways

- Event History is automatically available in every AWS account.
- It stores Management Events for the last 90 days.
- Trails are required for long-term retention and advanced integrations.
- Event History is ideal for quick troubleshooting and auditing.