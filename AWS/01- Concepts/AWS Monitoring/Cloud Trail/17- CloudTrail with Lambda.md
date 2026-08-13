# AWS CloudTrail with AWS Lambda

CloudTrail integrates with AWS Lambda to automate responses to AWS API activity.

Instead of only recording events, Lambda allows organizations to automatically remediate security issues, enforce compliance policies, and perform operational tasks whenever specific CloudTrail events occur.

------------------------------------------------------------------------

# Why Integrate CloudTrail with Lambda?

Automation helps eliminate manual intervention.

Examples include:

- Automatically remove public S3 access
- Recreate deleted resources
- Disable compromised IAM users
- Notify security teams
- Enforce compliance

------------------------------------------------------------------------

# Architecture

```text
AWS API Call

↓

CloudTrail

↓

Amazon EventBridge

↓

Lambda Function

↓

AWS Resource
```

------------------------------------------------------------------------

# How Integration Works

1. CloudTrail records an API event.
2. EventBridge evaluates the event.
3. A matching rule invokes a Lambda function.
4. Lambda performs the required action.

------------------------------------------------------------------------

# Common Automation Scenarios

Lambda can automatically respond to:

- CreateUser
- DeleteBucket
- TerminateInstances
- PutBucketPolicy
- CreateSecurityGroup
- ConsoleLogin

------------------------------------------------------------------------

# Example Workflow

```text
User

↓

Delete Security Group

↓

CloudTrail

↓

EventBridge Rule

↓

Lambda

↓

Recreate Security Group

↓

SNS Notification
```

------------------------------------------------------------------------

# Automatic Remediation

Examples include:

- Remove public S3 bucket permissions
- Disable unused IAM access keys
- Restore deleted tags
- Stop unauthorized EC2 instances
- Rotate compromised credentials

------------------------------------------------------------------------

# Benefits

- Real-time automation
- Faster recovery
- Reduced operational effort
- Improved compliance
- Enhanced security

------------------------------------------------------------------------

# Real-World Example

A developer accidentally makes an S3 bucket public.

CloudTrail records the **PutBucketPolicy** API call.

EventBridge invokes a Lambda function.

Lambda removes the public access policy and sends a notification to the security team.

------------------------------------------------------------------------

# Best Practices

- Keep Lambda functions lightweight.
- Use least-privilege IAM roles.
- Log Lambda execution in CloudWatch.
- Test automation before production deployment.
- Avoid recursive event triggers.

------------------------------------------------------------------------

# Key Takeaways

- CloudTrail records the event.
- EventBridge routes the event.
- Lambda performs automated remediation.
- This integration enables event-driven security automation.