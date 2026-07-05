# EventBridge Security

Security is a critical aspect of any event-driven architecture. Amazon EventBridge provides multiple security features to protect events, control access, and ensure secure communication between AWS services and external applications.

These security mechanisms include Identity and Access Management (IAM), Resource Policies, encryption, and audit logging.

------------------------------------------------------------------------

# Why is Security Important?

EventBridge often carries sensitive business events such as:

- Customer orders
- Payment transactions
- Security alerts
- User registrations
- Financial records

Protecting these events is essential to maintain confidentiality, integrity, and availability.

------------------------------------------------------------------------

# IAM Integration

Amazon EventBridge integrates with AWS Identity and Access Management (IAM).

IAM policies control:

- Who can create Event Buses
- Who can publish events
- Who can create Rules
- Who can configure Targets
- Who can manage Archives

Follow the principle of least privilege when assigning permissions.

------------------------------------------------------------------------

# Resource Policies

Resource Policies are attached directly to Event Buses.

They allow:

- Cross-account publishing
- Cross-account event routing
- Controlled access to EventBridge resources

Resource Policies complement IAM policies.

------------------------------------------------------------------------

# Encryption

EventBridge encrypts events in transit using HTTPS.

For stored event data, AWS-managed encryption protects EventBridge resources.

When integrating with other services such as Amazon SQS or Amazon SNS, enable encryption using AWS KMS where appropriate.

------------------------------------------------------------------------

# Cross-Account Security

For multi-account environments:

- Grant access only to trusted AWS accounts.
- Use Resource Policies instead of wildcard permissions.
- Audit access regularly.

------------------------------------------------------------------------

# CloudTrail Integration

AWS CloudTrail records EventBridge API activity.

Examples include:

- CreateRule
- PutEvents
- DeleteRule
- PutTargets

CloudTrail helps with auditing and compliance.

------------------------------------------------------------------------

# Monitoring Security

Use Amazon CloudWatch to monitor:

- Failed event deliveries
- Retry attempts
- Rule invocation failures
- DLQ activity

Configure CloudWatch Alarms to notify administrators of suspicious behavior.

------------------------------------------------------------------------

# Security Best Practices

- Apply least privilege IAM policies.
- Avoid wildcard (`*`) permissions.
- Encrypt related AWS resources with AWS KMS.
- Enable CloudTrail logging.
- Configure DLQs for important workloads.
- Review Resource Policies regularly.
- Rotate API credentials used in Connections.

------------------------------------------------------------------------

# Common Security Mistakes

- Granting overly broad IAM permissions.
- Using wildcard principals in Resource Policies.
- Ignoring CloudTrail logs.
- Storing secrets directly in application code.
- Not monitoring failed event deliveries.

------------------------------------------------------------------------

# Real-World Example

A company has separate AWS accounts for Development and Production.

The Production account hosts a centralized Event Bus.

A Resource Policy allows only the Development account to publish deployment events.

CloudTrail records every API call, and CloudWatch monitors delivery failures, providing a secure and auditable event-driven platform.

------------------------------------------------------------------------

# Key Takeaways

- EventBridge security relies on IAM, Resource Policies, encryption, and CloudTrail.
- Follow the principle of least privilege.
- Use CloudWatch and CloudTrail for monitoring and auditing.
- Secure event-driven architectures require both preventive and detective security controls.