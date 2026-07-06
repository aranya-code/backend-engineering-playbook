# How AWS CloudTrail Works

AWS CloudTrail continuously monitors AWS API activity and records every supported API request performed within your AWS account.

These events are stored in Event History and can optionally be delivered to Amazon S3 and other AWS services through a Trail.

------------------------------------------------------------------------

# Event Lifecycle

CloudTrail follows a simple lifecycle.

```text
User / Application

↓

AWS API Call

↓

CloudTrail Records Event

↓

Event History

↓

Trail

↓

Amazon S3

↓

CloudWatch Logs

↓

EventBridge
```

------------------------------------------------------------------------

# Step 1 - API Call

An API call can originate from:

- AWS Console
- AWS CLI
- AWS SDK
- CloudFormation
- Lambda
- AWS Services

Example:

```text
RunInstances
```

------------------------------------------------------------------------

# Step 2 - CloudTrail Captures Event

CloudTrail records details such as:

- Event Name
- User
- Timestamp
- AWS Region
- Source IP
- Resource
- Request Parameters
- Response Elements

------------------------------------------------------------------------

# Step 3 - Event History

The event immediately appears in Event History.

Characteristics:

- Management Events only
- Last 90 days
- No Trail required

------------------------------------------------------------------------

# Step 4 - Trail Processing

If a Trail exists:

CloudTrail delivers the event to:

- Amazon S3
- CloudWatch Logs

------------------------------------------------------------------------

# Step 5 - Automation

Once delivered:

CloudWatch can:

- Create Metrics
- Trigger Alarms

EventBridge can:

- Invoke Lambda
- Send SNS Notifications
- Start Step Functions

------------------------------------------------------------------------

# Example Workflow

```text
Administrator

↓

Delete S3 Bucket

↓

CloudTrail Records Event

↓

EventBridge Rule

↓

Lambda

↓

Send Email Notification
```

------------------------------------------------------------------------

# Why This Matters

CloudTrail enables:

- Security auditing
- Compliance
- Change tracking
- Incident response
- Governance

------------------------------------------------------------------------

# Best Practices

- Enable Multi-Region Trails.
- Store logs securely.
- Monitor CloudTrail activity.
- Integrate with CloudWatch.
- Use EventBridge for automation.

------------------------------------------------------------------------

# Key Takeaways

- CloudTrail records supported AWS API calls.
- Events first appear in Event History.
- Trails archive logs in Amazon S3.
- CloudWatch and EventBridge provide monitoring and automation.