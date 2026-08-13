# Troubleshooting AWS X-Ray

Even after correctly configuring AWS X-Ray, traces may not appear or may contain incomplete information. Troubleshooting helps identify configuration issues, permission problems, SDK errors, or networking failures.

This chapter discusses common problems and how to resolve them.

------------------------------------------------------------------------

# Common Issues

Frequently encountered issues include:

- Missing traces
- Missing segments
- Missing Service Map
- IAM permission errors
- Daemon not running
- Sampling configuration issues
- Incomplete traces
- Missing downstream services

------------------------------------------------------------------------

# Issue 1: No Traces Appearing

## Symptoms

- X-Ray Console shows no traces.
- No Service Map is generated.

## Possible Causes

- SDK not installed
- Tracing disabled
- Daemon not running
- Incorrect IAM permissions

## Solution

- Verify the SDK is installed.
- Enable Active Tracing.
- Start the X-Ray Daemon.
- Attach the correct IAM policy.

------------------------------------------------------------------------

# Issue 2: Missing Segments

## Symptoms

Only some services appear in traces.

Example:

```text
API Gateway

↓

Lambda

❌ Database Missing
```

## Causes

- Database calls not instrumented
- Missing SDK instrumentation
- SDK version outdated

## Solution

- Instrument database calls.
- Upgrade the SDK.
- Verify subsegment creation.

------------------------------------------------------------------------

# Issue 3: Service Map Not Generated

## Symptoms

Traces exist but no Service Map appears.

## Causes

- Insufficient trace data
- Sampling rate too low
- Services not communicating through traced requests

## Solution

- Increase sampling temporarily.
- Generate additional traffic.
- Verify SDK configuration.

------------------------------------------------------------------------

# Issue 4: Access Denied Errors

Example:

```text
AccessDeniedException
```

## Causes

Missing IAM permissions.

## Solution

Attach:

```text
AWSXRayDaemonWriteAccess
```

or the appropriate custom IAM policy.

------------------------------------------------------------------------

# Issue 5: Daemon Not Running

## Symptoms

No traces uploaded.

## Verification

Check daemon status.

Example:

```text
systemctl status xray
```

## Solution

Restart the daemon and verify logs.

------------------------------------------------------------------------

# Issue 6: Sampling Problems

Too few traces appear.

Possible causes:

- Sampling rules too restrictive
- Low reservoir size
- Low fixed rate

Temporarily increase the sampling rate during troubleshooting.

------------------------------------------------------------------------

# Issue 7: Missing Downstream Calls

Example:

```text
Lambda

↓

External API

❌ Missing
```

Cause:

External requests were not instrumented.

Solution:

Create manual subsegments for external API calls.

------------------------------------------------------------------------

# Issue 8: Network Connectivity

The daemon must communicate with AWS X-Ray over HTTPS.

Verify:

- Internet connectivity
- VPC routing
- Security Groups
- Proxy configuration

------------------------------------------------------------------------

# Debugging Tips

Check:

- Application logs
- Daemon logs
- CloudWatch Logs
- CloudTrail events
- IAM policies
- Service Map

------------------------------------------------------------------------

# Best Practices

- Monitor daemon health.
- Enable CloudWatch Alarms.
- Update SDK regularly.
- Verify IAM permissions.
- Test tracing after deployments.
- Review sampling configuration.

------------------------------------------------------------------------

# Key Takeaways

- Most X-Ray issues involve SDK configuration, IAM permissions, or daemon problems.
- Missing traces usually indicate instrumentation or permission issues.
- CloudWatch Logs and daemon logs are valuable troubleshooting tools.
- Regular monitoring helps detect tracing problems before they affect production.