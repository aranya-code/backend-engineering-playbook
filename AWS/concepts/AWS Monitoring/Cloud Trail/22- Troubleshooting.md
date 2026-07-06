# Troubleshooting AWS CloudTrail

Although AWS CloudTrail is a managed service, you may occasionally encounter issues such as missing logs, delayed log delivery, permission errors, or incomplete event recording.

Understanding common problems and their solutions helps maintain reliable auditing and compliance.

------------------------------------------------------------------------

# Common CloudTrail Issues

Frequently encountered issues include:

- Missing CloudTrail logs
- Trail not recording events
- Delayed log delivery
- Access denied errors
- Missing Data Events
- CloudWatch integration failures
- EventBridge rules not triggering
- S3 delivery failures

------------------------------------------------------------------------

# Issue 1: No Events in Event History

## Symptoms

- Event History is empty.
- Recent API activity is not visible.

## Possible Causes

- Wrong AWS Region selected.
- API call is unsupported.
- Incorrect time range.

## Solution

- Verify the AWS Region.
- Adjust the search filters.
- Confirm that the API is supported by CloudTrail.

------------------------------------------------------------------------

# Issue 2: Logs Not Delivered to Amazon S3

## Symptoms

CloudTrail events appear in Event History but not in the S3 bucket.

## Possible Causes

- Incorrect S3 bucket policy.
- Bucket deleted or renamed.
- Insufficient permissions.
- Trail misconfiguration.

## Solution

- Verify the bucket policy.
- Confirm the bucket exists.
- Check Trail configuration.
- Review CloudTrail status.

------------------------------------------------------------------------

# Issue 3: Missing Data Events

## Symptoms

S3 object uploads or Lambda invocations do not appear.

## Cause

Data Events are disabled by default.

## Solution

Enable Data Events for the required resources.

------------------------------------------------------------------------

# Issue 4: CloudWatch Logs Not Receiving Events

## Symptoms

CloudWatch Log Group remains empty.

## Possible Causes

- Missing IAM role
- Incorrect Log Group
- CloudTrail integration disabled

## Solution

- Verify the IAM role.
- Confirm CloudWatch integration.
- Check Log Group permissions.

------------------------------------------------------------------------

# Issue 5: EventBridge Rules Not Triggering

## Symptoms

Automation never starts.

## Possible Causes

- Incorrect event pattern
- Wrong event source
- Missing target permissions

## Solution

- Review the EventBridge rule.
- Test the event pattern.
- Verify target IAM permissions.

------------------------------------------------------------------------

# Issue 6: Access Denied Errors

Example:

```text
AccessDeniedException
```

Possible Causes:

- Missing IAM permissions
- SCP restrictions
- Bucket policy restrictions

Solution:

Review IAM policies and S3 bucket permissions.

------------------------------------------------------------------------

# Issue 7: Delayed Log Delivery

CloudTrail logs are **not delivered instantly**.

Typical delivery time:

```text
5–15 Minutes
```

This delay is expected and should not be confused with service failures.

------------------------------------------------------------------------

# Troubleshooting Checklist

Verify:

- Trail status
- AWS Region
- IAM permissions
- S3 bucket policy
- CloudWatch configuration
- EventBridge rules
- Data Event configuration
- Log delivery status

------------------------------------------------------------------------

# Real-World Example

A security team cannot find S3 object deletion logs.

Investigation reveals:

```text
Trail

↓

Data Events Disabled
```

After enabling S3 Data Events, object-level activity begins appearing in CloudTrail.

------------------------------------------------------------------------

# Best Practices

- Enable Multi-Region Trails.
- Test log delivery regularly.
- Monitor CloudTrail health.
- Enable CloudWatch Alarms.
- Validate S3 permissions.
- Review Trail configuration after changes.

------------------------------------------------------------------------

# Key Takeaways

- Most CloudTrail issues involve Trail configuration or IAM permissions.
- Data Events must be explicitly enabled.
- Verify S3, CloudWatch, and EventBridge integrations.
- Regular testing ensures reliable auditing.