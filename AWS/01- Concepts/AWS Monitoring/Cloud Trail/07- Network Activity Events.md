# Network Activity Events

Network Activity Events are a newer category of CloudTrail events that provide visibility into API activity performed through supported **AWS VPC Endpoints (AWS PrivateLink)**.

Unlike Management Events and Data Events, Network Activity Events help monitor how AWS services are accessed through private network connections.

------------------------------------------------------------------------

# What are Network Activity Events?

Network Activity Events record API calls made through supported VPC endpoints.

These events help organizations monitor:

- Private connectivity
- Network access
- VPC Endpoint usage
- Service-to-service communication

------------------------------------------------------------------------

# Why are Network Activity Events Important?

Organizations increasingly use private networking to improve security.

Network Activity Events help answer questions such as:

- Which application accessed Amazon S3 through a VPC Endpoint?
- Which IAM role called AWS KMS?
- Was a service accessed over the public internet or privately?
- Which VPC Endpoint was used?

------------------------------------------------------------------------

# Supported Services

Examples of services that support Network Activity Events include:

- AWS KMS
- Amazon S3 (supported scenarios)
- AWS Secrets Manager
- Other supported AWS services through PrivateLink

Support continues to expand as AWS adds more integrations.

------------------------------------------------------------------------

# Event Flow

```text
Application

↓

VPC Endpoint

↓

AWS Service

↓

CloudTrail

↓

Network Activity Event
```

------------------------------------------------------------------------

# Information Captured

A Network Activity Event may include:

- Event Name
- Event Time
- IAM Identity
- AWS Region
- VPC Endpoint ID
- Source IP
- Destination Service
- Request Parameters

------------------------------------------------------------------------

# Benefits

- Increased network visibility
- Better compliance
- Private connectivity auditing
- Security investigations
- Detect unauthorized network access

------------------------------------------------------------------------

# Real-World Example

A company stores encryption keys in AWS KMS.

```text
Application

↓

VPC Endpoint

↓

AWS KMS

↓

CloudTrail Logs Event
```

Security engineers can verify that encryption requests occurred through the private network instead of the public internet.

------------------------------------------------------------------------

# Best Practices

- Enable Network Activity Events for critical workloads.
- Monitor VPC Endpoint usage.
- Review unusual access patterns.
- Integrate with EventBridge for automated security responses.
- Store logs securely in Amazon S3.

------------------------------------------------------------------------

# Key Takeaways

- Network Activity Events monitor API activity through supported VPC Endpoints.
- They improve visibility into private AWS networking.
- These events enhance security, auditing, and compliance.