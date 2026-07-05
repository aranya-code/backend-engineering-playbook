# Cross-Account Observability

Modern AWS environments often consist of multiple AWS accounts to separate workloads, environments, and business units. Monitoring each account individually can make troubleshooting difficult and time-consuming.

**CloudWatch Cross-Account Observability** enables you to monitor resources across multiple AWS accounts from a single monitoring account, providing centralized visibility into your entire AWS environment.

---

# What is Cross-Account Observability?

Cross-Account Observability is a CloudWatch feature that allows you to:

- Monitor multiple AWS accounts
- Search logs across accounts
- View metrics from multiple accounts
- Analyze traces from AWS X-Ray
- Troubleshoot applications from one place

Instead of switching between AWS accounts, engineers can investigate issues from a centralized monitoring account.

---

# Why Use Cross-Account Observability?

Large organizations commonly use multiple AWS accounts for:

- Development
- Testing
- Staging
- Production
- Security
- Shared Services

Without Cross-Account Observability, engineers must log in to each account individually.

With Cross-Account Observability, monitoring becomes centralized, reducing operational complexity and improving incident response times.

---

# How Cross-Account Observability Works

```text
             AWS Organization

        +---------------------------+
        |                           |
        |  Monitoring Account       |
        |        (Central)          |
        +-------------+-------------+
                      |
      ----------------------------------------
      |                |                    |
      v                v                    v

 Production      Development         Shared Services

 AWS Account      AWS Account          AWS Account

      |                |                    |
      +----------------+--------------------+
                       |
                       v
          CloudWatch Cross-Account
               Observability
```

The monitoring account collects and displays telemetry from multiple source accounts.

---

# Key Components

Cross-Account Observability supports multiple telemetry types.

## Metrics

Monitor CloudWatch Metrics across AWS accounts.

Examples:

- EC2 CPU Utilization
- Lambda Errors
- RDS Connections
- Network Traffic

---

## Logs

Search CloudWatch Logs stored in different AWS accounts.

Examples:

- Lambda Logs
- Application Logs
- ECS Logs
- API Gateway Logs

This eliminates the need to switch accounts while troubleshooting.

---

## Traces

ServiceLens integrates AWS X-Ray traces from multiple AWS accounts.

This provides complete visibility into distributed applications spanning several AWS accounts.

---

## Dashboards

CloudWatch Dashboards can display metrics from:

- Multiple AWS Accounts
- Multiple AWS Regions

This provides a single operational dashboard for an entire organization.

---

# Monitoring Account

The **Monitoring Account** is the central AWS account used by operations teams.

Responsibilities include:

- Viewing metrics
- Searching logs
- Investigating traces
- Managing dashboards
- Monitoring alarms

This account does not need to host application workloads.

---

# Source Accounts

Source Accounts contain the actual AWS resources.

Examples:

- Production
- Development
- Testing
- Shared Infrastructure

These accounts securely share telemetry with the monitoring account.

---

# Supported Services

Cross-Account Observability supports:

- CloudWatch Metrics
- CloudWatch Logs
- CloudWatch Dashboards
- CloudWatch ServiceLens
- AWS X-Ray

Support for additional AWS services continues to expand.

---

# Benefits

- Centralized monitoring
- Reduced operational complexity
- Faster troubleshooting
- Better collaboration
- Improved visibility
- Organization-wide dashboards
- Simplified incident response

---

# Real-World Example

A company operates using five AWS accounts:

- Production
- Development
- QA
- Networking
- Security

During a production incident, engineers need to investigate:

- Lambda logs
- API Gateway metrics
- RDS performance
- X-Ray traces

Without Cross-Account Observability, they would log in to each AWS account separately.

With Cross-Account Observability, all metrics, logs, and traces are available from the monitoring account, allowing engineers to identify the root cause much faster.

---

# Security Considerations

Cross-Account Observability uses AWS Identity and Access Management (IAM) to securely share telemetry.

Best practices include:

- Follow the principle of least privilege.
- Share only the required telemetry.
- Separate production and non-production access.
- Audit IAM roles regularly.
- Enable AWS CloudTrail for auditing.

---

# Best Practices

- Use a dedicated monitoring account.
- Integrate with AWS Organizations where possible.
- Create organization-wide dashboards.
- Monitor all production workloads centrally.
- Combine Cross-Account Observability with ServiceLens.
- Review IAM permissions regularly.
- Standardize CloudWatch dashboards across teams.

---

# Limitations

- Requires configuration between monitoring and source accounts.
- IAM permissions must be configured correctly.
- Cross-account access should be carefully controlled.
- Some features may vary depending on AWS Region and service support.

---

# Cross-Account Observability vs Traditional Monitoring

| Traditional Monitoring | Cross-Account Observability |
|------------------------|-----------------------------|
| One account at a time | Multiple accounts simultaneously |
| Separate dashboards | Centralized dashboards |
| Multiple logins required | Single monitoring account |
| Limited visibility | Organization-wide visibility |

---

# Key Takeaways

- Cross-Account Observability centralizes monitoring across multiple AWS accounts.
- It supports CloudWatch Metrics, Logs, Dashboards, ServiceLens, and AWS X-Ray.
- Organizations can monitor development, testing, and production environments from a single monitoring account.
- Centralized observability improves operational efficiency and reduces incident response time.
- Cross-Account Observability is a best practice for enterprises using AWS Organizations and multi-account architectures.