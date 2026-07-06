# CloudTrail Log Files

CloudTrail stores recorded events as **JSON log files**.

These log files contain detailed information about every recorded AWS API call and are delivered to an Amazon S3 bucket when a Trail is configured.

They provide the foundation for auditing, troubleshooting, compliance, and security investigations.

------------------------------------------------------------------------

# What is a CloudTrail Log File?

A CloudTrail log file is a JSON document containing one or more recorded events.

Each event represents a single AWS API request.

Example:

```text
Log File

↓

Event 1

↓

Event 2

↓

Event 3
```

------------------------------------------------------------------------

# Log Delivery

CloudTrail delivers log files to:

```text
CloudTrail

↓

Trail

↓

Amazon S3

↓

JSON Log Files
```

Logs are typically delivered within a few minutes after API activity occurs.

------------------------------------------------------------------------

# JSON Structure

Each log file contains:

- Records
- Event Metadata
- API Information
- Resource Details

Example:

```json
{
  "Records": [
    {
      "eventVersion": "1.09",
      "eventSource": "ec2.amazonaws.com",
      "eventName": "RunInstances",
      "awsRegion": "us-east-1"
    }
  ]
}
```

------------------------------------------------------------------------

# Common Event Fields

Every event may include:

- Event Version
- Event Time
- Event Source
- Event Name
- AWS Region
- User Identity
- Source IP Address
- User Agent
- Request Parameters
- Response Elements
- Resources
- Event ID

------------------------------------------------------------------------

# Example Event

Suppose a user launches an EC2 instance.

CloudTrail records:

```text
Event Name

RunInstances

↓

IAM User

↓

Timestamp

↓

Source IP

↓

AWS Region

↓

Request Parameters
```

This provides complete visibility into the operation.

------------------------------------------------------------------------

# Log File Naming

CloudTrail automatically organizes logs in Amazon S3.

A typical structure is:

```text
Bucket

↓

AWSLogs

↓

Account ID

↓

CloudTrail

↓

Region

↓

Year

↓

Month

↓

Day
```

This hierarchy makes it easy to locate historical log files.

------------------------------------------------------------------------

# Log Analysis

CloudTrail logs can be analyzed using:

- Amazon Athena
- Amazon CloudWatch Logs Insights
- Amazon OpenSearch Service
- AWS Glue
- Third-party SIEM platforms

------------------------------------------------------------------------

# Security Considerations

Protect CloudTrail logs by:

- Enabling S3 encryption
- Using AWS KMS
- Restricting bucket access
- Enabling S3 Versioning
- Enabling Log File Integrity Validation

------------------------------------------------------------------------

# Real-World Example

A security team investigates an unauthorized IAM policy change.

They locate the CloudTrail log in Amazon S3 and identify:

- User Identity
- Source IP
- Event Name
- Request Parameters
- Timestamp

This information is used to determine the cause of the incident.

------------------------------------------------------------------------

# Best Practices

- Store logs in a dedicated S3 bucket.
- Enable server-side encryption.
- Enable S3 Versioning.
- Analyze logs using Amazon Athena.
- Archive older logs with S3 Lifecycle policies.
- Enable Log File Integrity Validation.

------------------------------------------------------------------------

# Key Takeaways

- CloudTrail stores events as JSON log files.
- Log files are delivered to Amazon S3 through a Trail.
- Each event contains detailed information about an AWS API call.
- CloudTrail logs support auditing, troubleshooting, compliance, and security investigations.
- Secure log files using encryption, versioning, and integrity validation.