# AWS CloudTrail Architecture

AWS CloudTrail records API activity across your AWS account and delivers the event logs to a secure storage location, typically an Amazon S3 bucket.

The architecture is designed to capture every supported API call made by users, applications, AWS services, and the AWS Management Console.

------------------------------------------------------------------------

# CloudTrail Architecture Components

A typical CloudTrail architecture consists of:

- AWS Resources
- Users and Applications
- CloudTrail
- Event History
- Trails
- Amazon S3
- Amazon CloudWatch Logs
- Amazon EventBridge
- Amazon SNS
- AWS Lambda

------------------------------------------------------------------------

# Architecture Diagram

```text
Users / Applications

↓

AWS API Calls

↓

AWS CloudTrail

├── Event History (90 Days)

├── Trail

│     ↓

│   Amazon S3

│

├── CloudWatch Logs

│

├── EventBridge

│

└── AWS Lambda / SNS
```

------------------------------------------------------------------------

# How CloudTrail Fits into AWS

CloudTrail sits between AWS services and administrators.

Every supported API request is captured before being stored or forwarded to other AWS services.

Example:

```text
User

↓

Launch EC2 Instance

↓

EC2 API

↓

CloudTrail Records Event

↓

Amazon S3
```

------------------------------------------------------------------------

# Main Components

## Users

Users generate API calls using:

- AWS Console
- AWS CLI
- AWS SDKs
- Applications

------------------------------------------------------------------------

## AWS Services

CloudTrail records actions performed on services such as:

- Amazon EC2
- Amazon S3
- AWS Lambda
- Amazon RDS
- IAM
- Amazon VPC

------------------------------------------------------------------------

## Event History

CloudTrail automatically stores management events for the last **90 days** without creating a trail.

------------------------------------------------------------------------

## Trail

A Trail continuously records events and delivers them to:

- Amazon S3
- CloudWatch Logs

------------------------------------------------------------------------

## Amazon S3

S3 stores CloudTrail log files.

Benefits:

- Long-term retention
- Backup
- Compliance
- Auditing

------------------------------------------------------------------------

## CloudWatch Logs

CloudTrail can send logs to CloudWatch Logs for:

- Monitoring
- Metric Filters
- Alarms

------------------------------------------------------------------------

## Amazon EventBridge

CloudTrail events can trigger:

- Lambda
- Step Functions
- SNS
- SQS

for automated workflows.

------------------------------------------------------------------------

# Benefits of the Architecture

- Centralized logging
- Secure storage
- Automation
- Compliance
- Monitoring
- Auditing

------------------------------------------------------------------------

# Best Practices

- Use Multi-Region Trails.
- Store logs in encrypted S3 buckets.
- Enable CloudWatch integration.
- Configure EventBridge rules.
- Enable log file integrity validation.

------------------------------------------------------------------------

# Key Takeaways

- CloudTrail captures AWS API activity.
- Trails deliver logs to Amazon S3.
- Event History stores management events for 90 days.
- CloudWatch and EventBridge extend monitoring and automation capabilities.