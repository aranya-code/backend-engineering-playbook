# Introduction

Even though Amazon SQS is a fully managed service, applications interacting with SQS may encounter operational issues due to configuration errors, permission problems, application bugs, or infrastructure failures.

Effective troubleshooting requires understanding how SQS works internally and identifying whether the issue lies with:

- The producer
- The queue configuration
- The consumer
- AWS permissions
- Network connectivity
- Downstream services

This guide covers the most common production issues, their causes, and recommended solutions.

---

# Troubleshooting Workflow

```
Producer

↓

Amazon SQS Queue

↓

Consumer

↓

CloudWatch Logs

↓

CloudTrail

↓

Application Logs

↓

Root Cause
```

Always determine where the failure occurs before attempting a fix.

---

# Issue 1 - Messages Are Not Appearing in the Queue

## Symptoms

- Producer reports success.
- Queue appears empty.
- Consumer receives no messages.

---

## Possible Causes

- Wrong Queue URL
- Wrong AWS Region
- Delay Queue enabled
- Producer sending to another queue
- Queue deleted or recreated

---

## Verification

```bash
aws sqs get-queue-attributes \
    --queue-url QUEUE_URL \
    --attribute-names ApproximateNumberOfMessages
```

---

## Solution

- Verify Queue URL.
- Verify AWS Region.
- Check Delivery Delay configuration.
- Confirm producer configuration.

---

# Issue 2 - Consumer Cannot Receive Messages

## Symptoms

```
ReceiveMessage()

↓

No Messages Returned
```

---

## Possible Causes

- Queue is empty.
- Delay Queue active.
- Messages currently invisible.
- Long Polling disabled.
- Wrong queue.

---

## Verification

Check:

```
ApproximateNumberOfMessagesVisible
```

and

```
ApproximateNumberOfMessagesNotVisible
```

---

## Solution

- Enable Long Polling.
- Verify Visibility Timeout.
- Check whether another consumer is processing messages.

---

# Issue 3 - Duplicate Messages

## Symptoms

```
Message Processed

↓

Processed Again
```

---

## Possible Causes

- Standard Queue behavior
- Consumer crash
- DeleteMessage() not called
- Visibility Timeout expired

---

## Solution

- Design idempotent consumers.
- Delete messages immediately.
- Increase Visibility Timeout if processing is slow.

---

# Issue 4 - Messages Reappear After Processing

## Symptoms

```
Receive

↓

Process

↓

Message Appears Again
```

---

## Possible Causes

- DeleteMessage() not executed.
- Invalid Receipt Handle.
- Visibility Timeout expired before processing completed.

---

## Solution

- Always call DeleteMessage().
- Verify Receipt Handle.
- Extend Visibility Timeout when required.

---

# Issue 5 - Access Denied

## Error

```
AccessDenied
```

---

## Possible Causes

- Missing IAM permission
- Incorrect Queue Policy
- Missing KMS permission
- Cross-account access not configured

---

## Verification

Review:

- IAM Policy
- Queue Policy
- KMS Key Policy
- CloudTrail logs

---

## Solution

Grant the required permissions.

Example

```json
{
  "Effect": "Allow",
  "Action": [
    "sqs:SendMessage",
    "sqs:ReceiveMessage",
    "sqs:DeleteMessage"
  ],
  "Resource": "QUEUE_ARN"
}
```

---

# Issue 6 - Messages Going to Dead Letter Queue

## Symptoms

```
Main Queue

↓

Retries

↓

DLQ
```

---

## Possible Causes

- Application exception
- Invalid payload
- Database failure
- Timeout
- External API unavailable

---

## Solution

- Inspect DLQ messages.
- Review application logs.
- Fix the underlying issue.
- Redrive messages back to the source queue.

---

# Issue 7 - Visibility Timeout Expiring Too Soon

## Symptoms

```
Receive

↓

Processing

↓

Visibility Timeout Ends

↓

Duplicate Processing
```

---

## Solution

Increase Visibility Timeout.

Example

```
Processing Time

=

90 Seconds

↓

Visibility Timeout

=

120 Seconds
```

---

# Issue 8 - High Number of Empty Receives

## Symptoms

CloudWatch shows:

```
NumberOfEmptyReceives
```

continuously increasing.

---

## Possible Causes

- Short Polling enabled
- Queue idle
- Frequent polling

---

## Solution

Enable Long Polling.

Recommended value

```
20 Seconds
```

---

# Issue 9 - Messages Not Deleted

## Symptoms

Queue size never decreases.

---

## Possible Causes

- DeleteMessage() not called.
- Invalid Receipt Handle.
- Application exception before deletion.

---

## Solution

Delete the message immediately after successful processing.

---

# Issue 10 - High Queue Backlog

## Symptoms

```
ApproximateNumberOfMessagesVisible

=

50000
```

---

## Possible Causes

- Consumers too slow
- Traffic spike
- Consumer failures

---

## Solution

- Increase consumer count.
- Scale ECS Tasks.
- Scale Lambda concurrency.
- Scale EC2 workers.

---

# Issue 11 - Dead Letter Queue Growing Rapidly

## Symptoms

```
DLQ

↓

100

↓

500

↓

1000 Messages
```

---

## Possible Causes

- Deployment bug
- Invalid payloads
- External dependency failure

---

## Solution

- Pause producers if necessary.
- Inspect DLQ.
- Fix application.
- Redrive messages after validation.

---

# Issue 12 - KMS Permission Errors

## Error

```
KMS.AccessDeniedException
```

---

## Possible Causes

- Missing kms:Decrypt permission
- Missing kms:GenerateDataKey permission
- Incorrect KMS Key Policy

---

## Solution

Verify IAM permissions and KMS Key Policies.

---

# Issue 13 - Amazon S3 Cannot Send Events to SQS

## Symptoms

Objects uploaded to S3 do not generate SQS messages.

---

## Possible Causes

- Incorrect Queue Policy
- Wrong Queue ARN
- Event Notification not configured
- KMS permission issue

---

## Solution

Verify:

- Queue Policy
- Event Notification configuration
- S3 permissions
- Queue ARN

---

# Issue 14 - Lambda Not Processing Messages

## Symptoms

Messages remain in the queue.

Lambda is never invoked.

---

## Possible Causes

- Event Source Mapping disabled
- Lambda execution role missing permissions
- Reserved concurrency reached

---

## Solution

Check:

- Event Source Mapping
- Lambda logs
- CloudWatch metrics
- IAM Role

---

# Useful AWS CLI Commands

## List Queues

```bash
aws sqs list-queues
```

---

## Get Queue Attributes

```bash
aws sqs get-queue-attributes \
  --queue-url QUEUE_URL \
  --attribute-names All
```

---

## Purge Queue

```bash
aws sqs purge-queue \
  --queue-url QUEUE_URL
```

---

## Receive Messages

```bash
aws sqs receive-message \
  --queue-url QUEUE_URL
```

---

## Send Test Message

```bash
aws sqs send-message \
  --queue-url QUEUE_URL \
  --message-body "Test"
```

---

# Monitoring Checklist

During troubleshooting, always review:

- CloudWatch Metrics
- CloudWatch Logs
- CloudTrail Events
- DLQ Message Count
- Application Logs
- Queue Attributes
- IAM Policies
- Queue Policies
- KMS Key Policies

---

# Production Troubleshooting Checklist

| Check | Status |
|--------|--------|
| Queue URL verified | ☐ |
| AWS Region verified | ☐ |
| IAM permissions validated | ☐ |
| Queue Policy reviewed | ☐ |
| KMS permissions checked | ☐ |
| CloudWatch metrics reviewed | ☐ |
| DLQ inspected | ☐ |
| Consumer logs reviewed | ☐ |
| Visibility Timeout verified | ☐ |
| Long Polling enabled | ☐ |

---

# Best Practices

- Enable CloudWatch monitoring for every queue.
- Configure Dead Letter Queues for production workloads.
- Log all processing failures with sufficient context.
- Test retry and failure scenarios regularly.
- Monitor queue growth and DLQ activity.
- Use Infrastructure as Code to maintain consistent queue configurations.

---

# Summary

Most Amazon SQS issues are caused by configuration errors, permission problems, application failures, or incorrect queue settings. A systematic troubleshooting approach—combined with CloudWatch metrics, CloudTrail logs, application logs, and proper queue configuration—helps identify and resolve issues quickly. By implementing monitoring, Dead Letter Queues, and robust retry logic, production systems can remain reliable even when failures occur.