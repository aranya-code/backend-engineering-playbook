# IAM & AWS CloudTrail

AWS Identity and Access Management (IAM) and AWS CloudTrail work together to provide secure access control and comprehensive auditing across AWS environments.

While IAM controls **who can perform actions**, CloudTrail records **who actually performed those actions**, making them complementary services for security, governance, and compliance.

------------------------------------------------------------------------

# Why Integrate IAM with CloudTrail?

IAM enforces permissions, while CloudTrail provides visibility into IAM activity.

Together they help answer questions such as:

- Who created an IAM user?
- Who attached an IAM policy?
- Who assumed an IAM role?
- Who deleted an IAM role?
- Who modified MFA settings?

------------------------------------------------------------------------

# IAM Activities Recorded by CloudTrail

CloudTrail records almost every IAM API call.

Examples include:

- CreateUser
- DeleteUser
- CreateRole
- DeleteRole
- AttachRolePolicy
- DetachRolePolicy
- CreatePolicy
- DeletePolicy
- UpdateAccessKey
- CreateAccessKey
- DeleteAccessKey
- AssumeRole

------------------------------------------------------------------------

# Architecture

```text
IAM User / Role

↓

AWS API Call

↓

CloudTrail

↓

Trail

↓

Amazon S3

↓

CloudWatch Logs
```

------------------------------------------------------------------------

# Information Recorded

Each IAM event includes:

- IAM User or Role
- Event Name
- Event Time
- Source IP Address
- AWS Region
- User Agent
- Request Parameters
- Response Elements

------------------------------------------------------------------------

# Monitoring IAM Activity

CloudTrail helps monitor:

- New IAM users
- Policy changes
- Permission modifications
- Access key creation
- Root account activity
- Role assumptions

------------------------------------------------------------------------

# Security Benefits

Using CloudTrail with IAM allows organizations to:

- Detect unauthorized changes
- Audit privileged access
- Investigate security incidents
- Track administrator activity
- Meet compliance requirements

------------------------------------------------------------------------

# Real-World Example

An administrator accidentally attaches the **AdministratorAccess** policy to a developer role.

CloudTrail records:

```text
AttachRolePolicy

↓

IAM Administrator

↓

Timestamp

↓

Source IP

↓

Policy Name
```

Security teams can quickly identify who made the change and when.

------------------------------------------------------------------------

# Best Practices

- Enable Multi-Region Trails.
- Monitor IAM Write Events.
- Enable MFA for privileged users.
- Create CloudWatch Alarms for sensitive IAM API calls.
- Regularly review IAM activity logs.

------------------------------------------------------------------------

# Key Takeaways

- IAM controls permissions, while CloudTrail records IAM activity.
- CloudTrail captures nearly all IAM API calls.
- Monitoring IAM events improves security and compliance.
- CloudTrail is essential for auditing privileged access.