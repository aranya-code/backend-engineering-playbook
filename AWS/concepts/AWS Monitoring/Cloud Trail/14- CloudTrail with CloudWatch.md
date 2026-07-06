# AWS CloudTrail with Amazon CloudWatch

AWS CloudTrail integrates with Amazon CloudWatch Logs, allowing organizations to monitor AWS API activity in near real time.

By sending CloudTrail events to CloudWatch Logs, administrators can create metric filters, dashboards, alarms, and automated notifications.

------------------------------------------------------------------------

# Why Integrate CloudTrail with CloudWatch?

CloudWatch enables:

- Real-time monitoring
- Metric Filters
- CloudWatch Alarms
- Dashboards
- Log Insights queries
- Operational visibility

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

SNS Notification
```

------------------------------------------------------------------------

# How Integration Works

1. CloudTrail records an API event.
2. The Trail sends the log to CloudWatch Logs.
3. CloudWatch analyzes the log.
4. Metric Filters evaluate the event.
5. Alarms trigger when conditions are met.

------------------------------------------------------------------------

# CloudWatch Metric Filters

Metric Filters search CloudTrail logs for specific API calls.

Examples:

- ConsoleLogin
- DeleteBucket
- TerminateInstances
- CreateUser
- PutBucketPolicy

------------------------------------------------------------------------

# CloudWatch Alarms

Common alarms include:

- Root account login
- IAM policy changes
- Security Group modifications
- Unauthorized API calls
- EC2 termination

Example:

```text
DeleteBucket Detected

↓

CloudWatch Alarm

↓

SNS Email

↓

Security Team
```

------------------------------------------------------------------------

# CloudWatch Logs Insights

Logs Insights allows you to query CloudTrail logs.

Example use cases:

- Find all DeleteBucket events.
- Search IAM activity.
- Identify failed ConsoleLogins.
- Analyze EC2 launches.

------------------------------------------------------------------------

# Benefits

- Near real-time monitoring
- Automated alerting
- Improved security
- Operational dashboards
- Faster incident response

------------------------------------------------------------------------

# Real-World Example

An IAM administrator accidentally deletes a production IAM role.

CloudTrail records the event.

CloudWatch detects the **DeleteRole** API call.

A CloudWatch Alarm sends an SNS notification to the operations team, allowing immediate investigation.

------------------------------------------------------------------------

# Best Practices

- Send CloudTrail logs to CloudWatch Logs.
- Create Metric Filters for sensitive API calls.
- Configure CloudWatch Alarms.
- Review dashboards regularly.
- Combine with EventBridge automation.

------------------------------------------------------------------------

# Key Takeaways

- CloudTrail integrates with CloudWatch for real-time monitoring.
- Metric Filters detect important API activity.
- CloudWatch Alarms notify administrators immediately.
- This integration significantly improves operational visibility.