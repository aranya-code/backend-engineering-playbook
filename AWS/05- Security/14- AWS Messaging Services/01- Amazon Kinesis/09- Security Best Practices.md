# 09- Security Best Practices

## Overview

Securing Amazon Kinesis Data Streams requires controls across identity, networking, encryption, data handling, application processing, and operational monitoring. A secure streaming platform must protect records throughout their lifecycle, from the moment a producer creates an event to the point where consumers persist or forward it.

Security should be implemented as a layered architecture rather than relying on a single control such as IAM or server-side encryption.

The primary security objectives are:

- Prevent unauthorized producers from injecting records.
- Prevent unauthorized consumers from accessing sensitive streams.
- Restrict administrative operations to approved platform identities.
- Protect data in transit and at rest.
- Minimize sensitive information in event payloads.
- Detect unauthorized access and configuration changes.
- Preserve audit evidence and support incident investigation.
- Maintain security during failures, recovery, and cross-account operations.

## Identity and Access Management

### Use Least-Privilege IAM Roles

Every workload should have an IAM role that reflects its specific responsibility.

Avoid sharing one broad IAM role across producers, consumers, and administrators.

| Identity | Required permissions |
|---|---|
| Producer | `PutRecord`, `PutRecords` |
| Shared-throughput consumer | `DescribeStreamSummary`, `ListShards`, `GetShardIterator`, `GetRecords` |
| Enhanced fan-out consumer | Stream description and consumer subscription permissions |
| Stream administrator | Stream lifecycle and configuration operations |
| Security auditor | Read-only access to relevant audit and configuration information |

Example producer policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublishOrders",
      "Effect": "Allow",
      "Action": [
        "kinesis:PutRecord",
        "kinesis:PutRecords"
      ],
      "Resource": "arn:aws:kinesis:ap-south-1:111111111111:stream/orders-stream"
    }
  ]
}
```

Example consumer policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadOrders",
      "Effect": "Allow",
      "Action": [
        "kinesis:DescribeStreamSummary",
        "kinesis:ListShards",
        "kinesis:GetShardIterator",
        "kinesis:GetRecords"
      ],
      "Resource": "arn:aws:kinesis:ap-south-1:111111111111:stream/orders-stream"
    }
  ]
}
```

Use the minimum permissions required by the actual consumer implementation. Enhanced fan-out consumers require additional permissions on their registered consumer resources.

### Avoid Wildcard Permissions

Avoid policies such as:

```json
{
  "Effect": "Allow",
  "Action": "kinesis:*",
  "Resource": "*"
}
```

This allows much broader access than ordinary application workloads require.

Instead:

- Specify individual API actions.
- Restrict resources to exact stream ARNs.
- Separate administrative and runtime identities.
- Use permissions boundaries where appropriate.
- Apply organizational guardrails through Service Control Policies.
- Review policy changes through CI/CD.

### Use Temporary Credentials

Applications should obtain temporary credentials through workload identity.

Recommended mechanisms:

| Workload | Credential mechanism |
|---|---|
| EC2 | Instance profile |
| ECS | Task role |
| EKS | EKS Pod Identity or IRSA |
| Lambda | Execution role |
| External AWS account | Cross-account role assumption or supported resource policy access |

Never embed long-lived AWS access keys in source code, Docker images, Git repositories, or deployment manifests.

### Separate Administrative Permissions

Application runtime roles should not normally be allowed to:

- Delete streams.
- Change retention periods.
- Modify encryption settings.
- Update resource policies.
- Register or deregister consumers.
- Modify security-related infrastructure.

Use separate deployment and administration roles with controlled approval workflows.

## Secure Cross-Account Access

Cross-account access should be explicitly configured and limited to approved external principals.

For direct resource-policy access, the stream owner defines which external principals can access the stream.

Example resource policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowExternalProducer",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::222222222222:role/orders-producer-role"
      },
      "Action": [
        "kinesis:PutRecord",
        "kinesis:PutRecords"
      ],
      "Resource": "arn:aws:kinesis:ap-south-1:111111111111:stream/orders-stream"
    }
  ]
}
```

Security recommendations:

- Trust specific IAM roles rather than entire accounts when practical.
- Restrict actions to the required producer or consumer operations.
- Review both identity-based and resource-based policies.
- Coordinate cross-account KMS permissions.
- Monitor resource policy changes through CloudTrail.
- Remove access immediately when a workload is decommissioned.

For role assumption, protect the target role's trust policy and restrict the source principal. Use external IDs when appropriate for third-party access scenarios.

## Encryption and Data Protection

### Encryption at Rest

Enable server-side encryption for Kinesis streams.

Kinesis supports encryption using AWS KMS keys. A customer-managed key provides additional control over key policies, access, rotation, and auditability.

Example CLI command:

```bash
aws kinesis start-stream-encryption \
  --stream-name orders-stream \
  --encryption-type KMS \
  --key-id alias/kinesis-production-key
```

Verify the stream configuration:

```bash
aws kinesis describe-stream-summary \
  --stream-name orders-stream
```

Recommended practices:

- Use customer-managed keys when independent key administration is required.
- Restrict key administration and key usage to separate roles.
- Monitor KMS key policy changes.
- Enable key rotation where appropriate.
- Protect against accidental key disablement or deletion.
- Test recovery procedures for encrypted streams.

A KMS key must be in the same Region as the Kinesis stream.

### Encryption in Transit

Use HTTPS and TLS for all Kinesis API communication.

AWS SDK clients use secure HTTPS connections by default.

For Python applications:

```python
import boto3
from botocore.config import Config

kinesis = boto3.client(
    "kinesis",
    region_name="ap-south-1",
    use_ssl=True,
    verify=True,
    config=Config(
        connect_timeout=5,
        read_timeout=30,
        retries={
            "mode": "standard",
            "total_max_attempts": 5,
        },
    ),
)
```

Production requirements:

- Never disable certificate verification.
- Keep container CA certificates updated.
- Avoid custom TLS configurations unless required.
- Use private connectivity for workloads that should not access public service endpoints.
- Monitor TLS and connectivity failures.

### Application-Level Encryption

Server-side encryption protects stored stream data, but authorized consumers receive readable records.

For highly sensitive fields, consider application-level encryption before publishing.

Examples include:

- Payment identifiers.
- Personal information.
- Confidential customer attributes.
- Sensitive account references.

Use envelope encryption and a managed key service for production implementations. Avoid distributing one shared encryption key across every producer and consumer.

Application-level encryption introduces key distribution, rotation, schema, and recovery requirements. Apply it selectively based on data classification.

### Data Minimization

Do not publish information that downstream consumers do not require.

Before publishing events:

- Remove unnecessary personal information.
- Never include passwords, access tokens, or API secrets.
- Avoid embedding complete database records when a smaller event is sufficient.
- Use references to sensitive records where appropriate.
- Define retention and deletion requirements.
- Prevent sensitive payloads from entering application logs.

## Secure Networking

### Use VPC Interface Endpoints

AWS PrivateLink interface endpoints provide private connectivity to Kinesis Data Streams.

Benefits include:

- Reduced dependency on public network paths.
- Private DNS-based service access.
- Network-level access restrictions.
- Better control over workload connectivity.

Recommended configuration:

- Deploy endpoints in appropriate Availability Zones.
- Restrict endpoint security groups.
- Enable private DNS where appropriate.
- Apply endpoint policies.
- Monitor endpoint changes.
- Restrict stream access independently through IAM.

A VPC endpoint is a connectivity control, not an authorization mechanism. Requests must still satisfy IAM and resource-policy requirements.

### Restrict Endpoint Access

An endpoint policy can limit which resources and actions are accessible through the endpoint.

Illustrative endpoint policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowOrdersStreamAccess",
      "Effect": "Allow",
      "Principal": "*",
      "Action": [
        "kinesis:PutRecord",
        "kinesis:PutRecords",
        "kinesis:GetRecords",
        "kinesis:GetShardIterator"
      ],
      "Resource": "arn:aws:kinesis:ap-south-1:111111111111:stream/orders-stream"
    }
  ]
}
```

The endpoint policy does not independently grant permissions to principals. The caller must also have the necessary IAM permissions, and the resource must permit the request.

### Apply Network Segmentation

Separate workloads according to trust and responsibility.

For example:

- Producer workloads in application subnets.
- Consumer workloads in processing subnets.
- Administrative workloads in restricted management subnets.
- Audit and monitoring workloads in dedicated security accounts.

Avoid allowing unrelated applications to share unrestricted network paths to sensitive streaming infrastructure.

## Producer Security Best Practices

Producers are a critical trust boundary because they can inject records into downstream business workflows.

A compromised producer may publish invalid events, manipulate business data, or trigger unauthorized downstream operations.

### Validate Events Before Publishing

Validate event schemas and business constraints before sending records.

Example using Pydantic:

```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OrderCreatedEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=100)
    event_type: Literal["order.created"]
    order_id: str = Field(min_length=1, max_length=100)
    customer_id: str = Field(min_length=1, max_length=100)
    occurred_at: datetime
    schema_version: int = Field(ge=1)
```

Validation should include:

- Required fields.
- Field types and length constraints.
- Allowed event types.
- Schema versions.
- Business invariants.
- Maximum payload size.

Consumers must validate records independently because authenticated producers can still publish malicious or malformed data.

### Use Stable Event Identifiers

Every business event should contain a stable event ID.

```json
{
  "event_id": "evt-01JORDERS9K3X",
  "event_type": "order.created",
  "order_id": "ORD-10025",
  "customer_id": "CUST-5001",
  "schema_version": 1
}
```

Stable identifiers help consumers detect duplicate records caused by retries or ambiguous publishing outcomes.

### Handle Retries Safely

Kinesis publishing can fail because of throttling, transient service errors, or network timeouts.

Use bounded retries with exponential backoff and jitter.

Do not assume a timeout means the record was rejected. Kinesis may have accepted the request even when the producer did not receive the response.

### Use the Transactional Outbox Pattern

For database-backed applications, avoid directly publishing an event after a database transaction without a durable intermediate mechanism.

The transactional outbox pattern stores the business update and event in the same database transaction. A separate publisher reads pending events and sends them to Kinesis.

This prevents the application from committing a business transaction while silently losing the corresponding event.

The publisher must still handle duplicate publication, so consumers need idempotency.

## Consumer Security Best Practices

Consumers process records and frequently access databases, APIs, and other sensitive systems.

A compromised consumer can expose data or perform unauthorized downstream operations.

### Validate Incoming Records

Consumers should validate:

- Event type.
- Schema version.
- Required identifiers.
- Field lengths and data types.
- Allowed state transitions.
- External resource ownership.
- Business authorization requirements.

Never trust a record simply because it came from an authenticated Kinesis stream.

### Implement Idempotent Processing

Kinesis consumers can process records more than once because of retries, worker restarts, or checkpoint recovery.

Use database uniqueness constraints to prevent duplicate business effects.

Example PostgreSQL table:

```sql
CREATE TABLE processed_events (
    event_id VARCHAR(100) PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Insert the event ID and perform the business update in the same transaction.

```sql
BEGIN;

INSERT INTO processed_events (event_id)
VALUES ('evt-01JORDERS9K3X')
ON CONFLICT (event_id) DO NOTHING;

-- Apply the business update only if the event was newly inserted.

COMMIT;
```

For external services, use provider-supported idempotency keys or a durable reconciliation mechanism.

### Protect Consumer Checkpoints

Consumers using Kinesis Client Library may store leases and checkpoints in DynamoDB.

Protect this storage because unauthorized modifications can cause records to be skipped, reprocessed, or consumed incorrectly.

- Use dedicated IAM roles.
- Restrict access to the required checkpoint table.
- Protect lease and checkpoint records from unauthorized updates.
- Monitor table deletion and permission changes.
- Include checkpoint recovery in disaster recovery testing.

### Isolate Consumer Permissions

Different consumers should have independent roles and downstream permissions.

For example:

| Consumer | Kinesis access | Downstream access |
|---|---|---|
| Fraud detection | Read transactions | Fraud database |
| Analytics | Read approved events | Analytics warehouse |
| Notifications | Read notification events | Notification provider |
| Data lake ingestion | Read archival events | S3 destination |

A notification consumer should not automatically have access to a fraud database simply because both consume the same stream.

## Secure Event Processing and Failure Handling

### Classify Processing Failures

| Failure | Handling |
|---|---|
| Transient database outage | Bounded retry with backoff |
| Kinesis throttling | Backoff and capacity review |
| Invalid event schema | Quarantine and alert |
| Business rule violation | Record rejection and investigate |
| External API outage | Retry with idempotency controls |
| Authorization failure | Alert and investigate IAM configuration |

### Quarantine Poison Records

Kinesis does not provide an SQS-style built-in dead-letter queue for individual records.

Implement a separate quarantine mechanism using an approved destination such as S3 or another stream.

Quarantine records should include:

- Original event ID.
- Source stream and shard information.
- Failure category.
- Processing attempt metadata.
- Failure timestamp.
- Schema version.

Protect quarantine storage with independent IAM policies, encryption, and retention controls. Quarantined records may contain the same sensitive data as the original stream.

### Avoid Unbounded Retries

Unbounded retries can cause:

- Consumer processing stalls.
- Repeated downstream load.
- Increased processing lag.
- Duplicate external side effects.
- Operational instability.

Use bounded retry policies and explicit escalation for records that cannot be processed safely.

## Monitoring and Auditing

### Enable CloudTrail

CloudTrail should capture relevant Kinesis management events, including:

- Stream creation and deletion.
- Retention changes.
- Encryption configuration changes.
- Resource policy modifications.
- Consumer registration changes.

Configure data events for sensitive publishing and consuming operations where supported and required.

Data events can generate significant volume and cost. Scope selectors to approved streams and operations.

### Monitor CloudWatch Metrics

Monitor both Kinesis service metrics and application-level metrics.

| Metric | Security or operational purpose |
|---|---|
| `IncomingRecords` | Detect unexpected publishing volume |
| `IncomingBytes` | Identify ingestion spikes |
| `WriteProvisionedThroughputExceeded` | Detect producer throttling |
| `ReadProvisionedThroughputExceeded` | Identify shared read pressure |
| `GetRecords.IteratorAgeMilliseconds` | Detect delayed consumer processing |
| `SubscribeToShard.RateExceeded` | Identify enhanced fan-out throttling |
| Application authorization failures | Detect permission problems or unauthorized requests |
| KMS access failures | Identify encryption authorization issues |
| Consumer processing failures | Detect malformed or unexpected events |

Combine service metrics with structured application logs and distributed tracing.

### Protect Application Logs

Do not log complete Kinesis payloads by default.

Prefer metadata such as:

- Event ID.
- Event type.
- Stream name.
- Shard ID.
- Processing duration.
- Result status.
- Correlation ID.

Avoid exposing tokens, credentials, personal information, or decrypted sensitive fields.

### Centralize Audit Logs

For enterprise environments:

- Use an organization trail.
- Deliver logs to a dedicated log archive account.
- Restrict S3 bucket access.
- Enable log file integrity validation.
- Encrypt audit logs.
- Define retention policies.
- Monitor trail and bucket configuration changes.

The workload account should not have unrestricted control over its own audit evidence.

## Infrastructure and Deployment Security

### Separate Runtime and Deployment Roles

Use separate identities for infrastructure provisioning and application execution.

| Role | Responsibility |
|---|---|
| Infrastructure deployment | Create and configure streams |
| Producer runtime | Publish records |
| Consumer runtime | Read records |
| Security administration | Manage security controls |
| Audit reader | Investigate audit records |

This separation limits the impact of compromised application credentials.

### Use Infrastructure as Code

Manage streams, IAM policies, KMS keys, VPC endpoints, and resource policies through Terraform or another approved infrastructure tool.

Example Kinesis stream:

```hcl
resource "aws_kinesis_stream" "orders" {
  name             = "orders-stream"
  retention_period = 48
  encryption_type  = "KMS"
  kms_key_id       = aws_kms_key.kinesis.arn

  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }

  tags = {
    Environment = "production"
    DataClass   = "confidential"
    ManagedBy   = "terraform"
  }
}
```

Security-sensitive infrastructure changes should require review and approval.

### CI/CD Security Checks

Include the following checks in infrastructure pipelines:

- IAM wildcard permission detection.
- Resource policy principal validation.
- KMS key policy review.
- Public access and network configuration checks.
- Terraform formatting and validation.
- Security policy tests.
- Production approval gates.
- Post-deployment authorization tests.

Static analysis helps detect common misconfigurations but does not replace integration testing against AWS.

## High Availability and Disaster Recovery

Security controls must remain effective during failover and recovery.

Recommended practices:

- Deploy workloads across multiple Availability Zones where appropriate.
- Use durable producer buffering when required by business recovery objectives.
- Configure stream retention based on replay requirements.
- Persist checkpoints in durable storage.
- Make consumers idempotent.
- Replicate required stream data to another Region when necessary.
- Recreate IAM policies and resource policies in the recovery environment.
- Replicate or recreate required KMS keys and permissions.
- Protect audit storage independently.
- Test access restoration and recovery procedures regularly.

Kinesis Data Streams is regional. Cross-account permissions do not provide automatic cross-Region replication.

A complete recovery plan must account for the stream, encryption keys, identities, network paths, consumers, checkpoints, and downstream systems.

## Common Security Mistakes

| Mistake | Risk | Recommended approach |
|---|---|---|
| Using one role for all applications | Excessive access and weak isolation | Assign dedicated workload roles |
| Granting `kinesis:*` | Unnecessary administrative permissions | Use action-specific policies |
| Storing access keys in Docker images | Credential compromise | Use workload identity |
| Assuming encryption protects consumers | Data remains readable after authorized retrieval | Apply downstream controls and selective field encryption |
| Trusting every authenticated producer | Malicious or invalid events can enter the stream | Validate producer authorization and consumer business rules |
| Ignoring duplicate processing | Repeated business operations | Use durable idempotency |
| Logging complete payloads | Sensitive data exposure | Log event metadata |
| Using VPC endpoints as the only security control | Unauthorized principals may still access permitted network paths | Enforce IAM and resource policies |
| Giving consumers broad DynamoDB access | Checkpoint compromise | Restrict access to specific tables and operations |
| Ignoring data-event audit costs | Unexpected CloudTrail expenses | Scope data-event selectors |
| Treating Kinesis as an exactly-once system | Duplicate side effects | Design idempotent consumers |
| Failing to test recovery permissions | Recovery workloads may be unable to access streams or keys | Test complete DR security configuration |

## Production Security Checklist

### Identity and Access

- [ ] Separate producer, consumer, administrator, and auditor roles.
- [ ] Apply least-privilege IAM policies.
- [ ] Use temporary credentials through workload identity.
- [ ] Restrict cross-account access to approved principals.
- [ ] Review trust policies and resource policies.
- [ ] Separate runtime and deployment permissions.

### Encryption and Networking

- [ ] Enable server-side encryption.
- [ ] Review KMS key policies and key lifecycle controls.
- [ ] Use TLS for all service communication.
- [ ] Use VPC endpoints where private connectivity is required.
- [ ] Restrict endpoint security groups and policies.
- [ ] Apply application-level encryption selectively.
- [ ] Minimize sensitive event payloads.

### Application Processing

- [ ] Validate producer and consumer event schemas.
- [ ] Include stable event identifiers.
- [ ] Implement idempotent business processing.
- [ ] Protect consumer checkpoints.
- [ ] Use bounded retries and backoff.
- [ ] Quarantine malformed and permanently failing records.
- [ ] Prevent sensitive payloads from entering logs.

### Monitoring and Operations

- [ ] Enable CloudTrail management event auditing.
- [ ] Configure required Kinesis data events.
- [ ] Monitor publishing and consumption metrics.
- [ ] Alert on unexpected policy and encryption changes.
- [ ] Protect audit and quarantine storage.
- [ ] Review security-sensitive infrastructure changes.
- [ ] Test cross-account authorization.
- [ ] Test disaster recovery and access restoration.

## Key Takeaways

- Secure Kinesis deployments require layered controls across IAM, networking, encryption, application validation, and audit logging.
- Separate producer, consumer, and administrative identities to limit the impact of compromised workloads.
- Encryption protects stored and transmitted data, but sensitive payloads and downstream systems require independent protection.
- Idempotent processing, bounded retries, protected checkpoints, and quarantine workflows are essential for secure and reliable consumers.
- Treat security policies, audit configuration, and disaster recovery controls as version-controlled production infrastructure.