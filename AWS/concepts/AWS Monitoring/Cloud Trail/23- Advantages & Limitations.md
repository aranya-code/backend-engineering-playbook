# Advantages & Limitations of AWS CloudTrail

AWS CloudTrail is one of the most important governance and auditing services in AWS.

It provides complete visibility into AWS API activity, but like every AWS service, it has both strengths and limitations.

------------------------------------------------------------------------

# Advantages

## Complete AWS API Auditing

CloudTrail records supported API calls made by:

- IAM Users
- IAM Roles
- AWS Services
- Applications
- AWS CLI
- AWS SDKs

------------------------------------------------------------------------

## Improved Security

CloudTrail helps detect:

- Unauthorized access
- Resource deletion
- IAM modifications
- Privilege escalation
- Suspicious API activity

------------------------------------------------------------------------

## Compliance

CloudTrail supports compliance standards such as:

- PCI DSS
- HIPAA
- SOC 2
- ISO 27001
- FedRAMP

------------------------------------------------------------------------

## Long-Term Log Storage

Using Amazon S3, logs can be retained for years.

Benefits include:

- Auditing
- Forensics
- Historical analysis

------------------------------------------------------------------------

## AWS Service Integration

CloudTrail integrates with:

- Amazon S3
- CloudWatch Logs
- EventBridge
- Lambda
- SNS
- AWS Organizations
- CloudTrail Lake

------------------------------------------------------------------------

## Automation

CloudTrail events can automatically trigger:

- Lambda
- Step Functions
- SNS
- Systems Manager

------------------------------------------------------------------------

# Limitations

## Not Real-Time Logging

CloudTrail log delivery typically takes several minutes.

It should not be considered a real-time monitoring service.

------------------------------------------------------------------------

## Data Events Are Disabled

Object-level operations are not recorded unless explicitly enabled.

------------------------------------------------------------------------

## Additional Costs

Charges may apply for:

- Data Events
- CloudTrail Insights
- CloudTrail Lake

------------------------------------------------------------------------

## AWS-Focused

CloudTrail records AWS API activity only.

It does not monitor:

- Application logs
- Server performance
- Operating system events

------------------------------------------------------------------------

## Limited Event History

Without a Trail:

```text
90 Days

↓

Management Events Only
```

------------------------------------------------------------------------

# Advantages vs Limitations

| Advantages | Limitations |
|------------|-------------|
| API auditing | Log delivery delay |
| Security visibility | Data Events disabled by default |
| Compliance | Additional paid features |
| Automation | AWS services only |
| Long-term retention | Requires Trail for long-term storage |

------------------------------------------------------------------------

# Real-World Example

A healthcare company uses CloudTrail to satisfy compliance requirements.

Benefits:

- Complete audit trail
- Long-term storage
- Security investigations

Limitations:

- Application logs still require CloudWatch Logs.
- Performance monitoring still requires CloudWatch Metrics.

------------------------------------------------------------------------

# Best Practices

- Use CloudTrail with CloudWatch.
- Enable Data Events only when needed.
- Archive logs.
- Monitor costs.
- Enable CloudTrail Insights.

------------------------------------------------------------------------

# Key Takeaways

- CloudTrail excels at auditing AWS API activity.
- It complements CloudWatch and X-Ray.
- Long-term storage requires Trails.
- Understanding its limitations helps design better monitoring solutions.