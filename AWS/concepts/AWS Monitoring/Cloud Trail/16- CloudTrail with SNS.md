# AWS CloudTrail with Amazon SNS

AWS CloudTrail integrates with Amazon Simple Notification Service (SNS) to provide immediate notifications when important AWS API events occur.

Instead of manually reviewing CloudTrail logs, administrators can receive real-time alerts whenever sensitive operations are performed within their AWS environment.

------------------------------------------------------------------------

# Why Integrate CloudTrail with SNS?

CloudTrail records API activity, but notifications allow teams to respond immediately.

Common notification scenarios include:

- Root account login
- IAM policy changes
- Security Group modifications
- S3 bucket deletion
- EC2 termination
- Unauthorized API activity

------------------------------------------------------------------------

# Architecture

```text
AWS API Call

↓

CloudTrail

↓

CloudWatch Logs

↓

Metric Filter

↓

CloudWatch Alarm

↓

Amazon SNS

↓

Email / SMS / Lambda / HTTPS
```

------------------------------------------------------------------------

# How Integration Works

1. A user performs an AWS API action.
2. CloudTrail records the event.
3. CloudWatch Logs receives the event.
4. A Metric Filter matches the event.
5. A CloudWatch Alarm enters the ALARM state.
6. Amazon SNS sends notifications to subscribers.

------------------------------------------------------------------------

# Notification Targets

Amazon SNS supports multiple delivery methods:

- Email
- SMS
- AWS Lambda
- HTTPS Endpoint
- Amazon SQS
- Mobile Push Notifications

------------------------------------------------------------------------

# Common Notification Scenarios

Examples include:

- IAM User Created
- IAM Policy Changed
- Root User Login
- DeleteBucket
- TerminateInstances
- ConsoleLogin Failure
- Security Group Changes

------------------------------------------------------------------------

# Example Workflow

```text
Administrator

↓

Delete S3 Bucket

↓

CloudTrail

↓

CloudWatch Alarm

↓

SNS Topic

↓

Email Sent to Security Team
```

------------------------------------------------------------------------

# Benefits

- Real-time notifications
- Faster incident response
- Improved operational awareness
- Compliance support
- Automated security alerts

------------------------------------------------------------------------

# Real-World Example

A production IAM policy is modified.

CloudTrail records the **PutRolePolicy** API call.

CloudWatch detects the event and triggers an SNS topic.

The security team immediately receives an email notification and begins investigating the change.

------------------------------------------------------------------------

# Best Practices

- Create separate SNS topics for security and operations.
- Subscribe multiple administrators.
- Use encrypted SNS topics.
- Test notifications regularly.
- Monitor failed deliveries.

------------------------------------------------------------------------

# Key Takeaways

- SNS provides real-time notifications for CloudTrail events.
- CloudWatch Alarms typically trigger SNS notifications.
- SNS improves operational awareness and security response.
- Email, SMS, Lambda, HTTPS, and SQS are common notification targets.