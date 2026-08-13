# AWS CloudTrail with Amazon EventBridge

AWS CloudTrail integrates with Amazon EventBridge to enable event-driven automation.

Instead of simply recording API activity, EventBridge can respond immediately to CloudTrail events by triggering Lambda functions, Step Functions, SNS notifications, or other AWS services.

------------------------------------------------------------------------

# Why Integrate CloudTrail with EventBridge?

This integration enables:

- Automated incident response
- Compliance automation
- Security monitoring
- Infrastructure automation
- Event-driven workflows

------------------------------------------------------------------------

# Architecture

```text
AWS API Call

↓

CloudTrail

↓

Amazon EventBridge

↓

Rule

↓

Target

↓

Lambda / SNS / SQS / Step Functions
```

------------------------------------------------------------------------

# How Integration Works

1. An AWS API call occurs.
2. CloudTrail records the event.
3. EventBridge receives the event.
4. EventBridge evaluates matching rules.
5. The configured target executes automatically.

------------------------------------------------------------------------

# Common EventBridge Targets

CloudTrail events can trigger:

- AWS Lambda
- Amazon SNS
- Amazon SQS
- AWS Step Functions
- AWS Systems Manager
- Amazon ECS Tasks

------------------------------------------------------------------------

# Common Automation Scenarios

Examples include:

- Notify when an IAM user is created.
- Detect root account logins.
- Automatically remediate public S3 buckets.
- Detect deleted Security Groups.
- Restart critical services.

------------------------------------------------------------------------

# Example Workflow

```text
Administrator

↓

Delete Security Group

↓

CloudTrail Event

↓

EventBridge Rule

↓

Lambda Function

↓

Recreate Security Group

↓

SNS Notification
```

------------------------------------------------------------------------

# Event Pattern Example

A rule may match:

```text
Source:

aws.ec2

↓

Event Name:

TerminateInstances
```

Whenever the event occurs, EventBridge triggers the configured target.

------------------------------------------------------------------------

# Benefits

- Real-time automation
- Faster incident response
- Improved security
- Reduced manual effort
- Compliance enforcement
- Infrastructure self-healing

------------------------------------------------------------------------

# Real-World Example

A company prohibits manual deletion of production S3 buckets.

Workflow:

```text
DeleteBucket API

↓

CloudTrail

↓

EventBridge

↓

Lambda

↓

Restore Bucket Policy

↓

Notify Security Team
```

The entire process completes automatically within seconds.

------------------------------------------------------------------------

# Best Practices

- Create focused EventBridge rules.
- Trigger only necessary targets.
- Monitor failed rule executions.
- Use least-privilege IAM roles.
- Test automation workflows regularly.

------------------------------------------------------------------------

# Key Takeaways

- EventBridge enables real-time responses to CloudTrail events.
- CloudTrail provides the event data, while EventBridge provides the automation.
- Common targets include Lambda, SNS, SQS, and Step Functions.
- This integration is essential for automated security and compliance workflows.