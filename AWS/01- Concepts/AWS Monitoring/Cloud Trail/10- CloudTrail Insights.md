# AWS CloudTrail Insights

CloudTrail Insights is a feature of AWS CloudTrail that automatically detects unusual or abnormal API activity within your AWS account.

Instead of recording every event like standard CloudTrail logging, CloudTrail Insights analyzes historical API activity, establishes a normal baseline, and generates **Insight Events** whenever it detects significant deviations.

This helps security teams quickly identify operational issues, compromised credentials, or unexpected administrative activity.

------------------------------------------------------------------------

# Why Do We Need CloudTrail Insights?

In large AWS environments, thousands of API calls occur every minute.

It is difficult to manually identify abnormal behavior such as:

- Sudden increase in EC2 launches
- Unexpected IAM modifications
- Large number of failed API calls
- Unusual Delete operations
- Compromised AWS credentials

CloudTrail Insights automatically detects these anomalies.

------------------------------------------------------------------------

# How CloudTrail Insights Works

CloudTrail continuously analyzes **Write Management Events**.

```text
AWS API Activity

↓

CloudTrail

↓

Behavior Analysis

↓

Baseline Created

↓

Abnormal Activity?

↓

Insight Event Generated
```

------------------------------------------------------------------------

# What Activities are Monitored?

CloudTrail Insights monitors:

- API call rate
- API error rate

It compares current activity against historical behavior.

------------------------------------------------------------------------

# Examples of Insight Events

Examples include:

- Large number of `RunInstances` API calls
- Unusual number of `DeleteBucket` operations
- Sudden increase in `CreateUser`
- Multiple failed IAM operations
- Spike in `TerminateInstances`

------------------------------------------------------------------------

# Insight Event Lifecycle

```text
Normal API Activity

↓

Baseline Established

↓

Abnormal API Activity

↓

Insight Starts

↓

Activity Returns to Normal

↓

Insight Ends
```

------------------------------------------------------------------------

# Information Included

An Insight Event contains:

- Insight ID
- Event Time
- Event Source
- API Name
- Baseline Activity
- Current Activity
- Insight State
- Duration

------------------------------------------------------------------------

# Benefits

- Detects unusual AWS activity
- Reduces manual investigation
- Improves incident response
- Identifies compromised credentials
- Detects operational issues
- Supports compliance monitoring

------------------------------------------------------------------------

# Real-World Example

An attacker gains access to an IAM user's credentials.

Normally:

```text
CreateUser

↓

1 Request / Day
```

Suddenly:

```text
CreateUser

↓

75 Requests / Hour
```

CloudTrail Insights detects the abnormal spike and generates an Insight Event for investigation.

------------------------------------------------------------------------

# Best Practices

- Enable CloudTrail Insights for production environments.
- Monitor Insight Events using CloudWatch.
- Integrate Insight Events with EventBridge.
- Trigger SNS notifications for security teams.
- Investigate every unexpected Insight Event.

------------------------------------------------------------------------

# Key Takeaways

- CloudTrail Insights detects unusual API activity.
- It analyzes Write Management Events.
- Baselines are created automatically.
- Insight Events improve security monitoring and incident response.