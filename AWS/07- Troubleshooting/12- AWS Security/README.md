# README

## Overview

This directory contains troubleshooting documentation for **AWS Security**, organized around diagnosing identity, authentication, authorization, cryptography, secrets management, network security, and audit-investigation failures in production AWS environments.

The documentation is intended for backend engineers operating Python services, REST APIs, microservices, serverless workloads, containerized applications, and supporting AWS infrastructure. It emphasizes systematic fault isolation, least-privilege remediation, evidence preservation, and verification rather than broad permission changes or disabling security controls.

Security failures frequently span multiple AWS services. An application may receive an `AccessDenied` response because of an IAM policy, a role trust policy, an organization-level Service Control Policy (SCP), a permissions boundary, a resource policy, a KMS key policy, or a VPC endpoint policy. Effective troubleshooting therefore requires identifying the principal, action, resource, request context, and applicable policy layers.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Authentication and Signature Validation Issues](./01-%20Authentication%20and%20Signature%20Validation%20Issues.md) | Diagnose AWS API authentication failures involving SigV4 signing, credentials, and request validation |
| 02 | [02- IAM Permissions and Access Denied Errors](./02-%20IAM%20Permissions%20and%20Access%20Denied%20Errors.md) | Investigate IAM authorization failures, explicit denies, permissions boundaries, and SCP restrictions |
| 03 | [03- Encryption and KMS Key Access Issues](./03-%20Encryption%20and%20KMS%20Key%20Access%20Issues.md) | Troubleshoot KMS access denials, key policies, grants, and encryption-context mismatches |
| 04 | [04- Secrets Retrieval and Rotation Issues](./04-%20Secrets%20Retrieval%20and%20Rotation%20Issues.md) | Diagnose secret retrieval failures, Parameter Store access issues, and rotation configuration problems |
| 05 | [05- VPC Connectivity and Security Rule Issues](./05-%20VPC%20Connectivity%20and%20Security%20Rule%20Issues.md) | Investigate security groups, network ACLs, routing, VPC endpoints, and private connectivity failures |
| 06 | [06- WAF Rule and DDoS Protection Issues](./06-%20WAF%20Rule%20and%20DDoS%20Protection%20Issues.md) | Troubleshoot WAF rule misconfigurations, false positives, and DDoS protection issues |
| 07 | [07- GuardDuty Findings and Security Hub Issues](./07-%20GuardDuty%20Findings%20and%20Security%20Hub%20Issues.md) | Investigate GuardDuty findings, Security Hub aggregation issues, and detection gaps |
| 08 | [08- CloudTrail and Audit Investigation](./08-%20CloudTrail%20and%20Audit%20Investigation.md) | Investigate API activity, missing audit events, suspicious operations, and CloudTrail delivery issues |

> **Repository maintenance:** Keep this navigation table synchronized with the actual filenames in this directory. The links above assume the listed documents exist with these exact names.

## Troubleshooting Approach

Follow a consistent investigation process to avoid unnecessary permission changes and preserve useful evidence.

1. **Identify the failing operation.** Capture the AWS service, API action, resource ARN, timestamp, region, request ID, and complete error message. Remove credentials and sensitive application data from diagnostic output.
2. **Verify the active identity.** Determine which IAM user, assumed role, federated session, or workload identity is making the request.
3. **Inspect the relevant control plane.** Review identity policies, trust policies, resource policies, permissions boundaries, SCPs, session policies, KMS key policies, endpoint policies, and network controls as applicable.
4. **Collect independent evidence.** Use AWS CLI inspection commands, CloudTrail events, service logs, and application telemetry to establish where the request fails.
5. **Apply the narrowest correction.** Add only the missing permission or correct the specific trust, configuration, routing, or signing defect. Do not grant administrator access as a general troubleshooting measure.
6. **Verify and prevent recurrence.** Reproduce the original operation, confirm the intended behavior, test that unrelated access remains restricted, and add appropriate monitoring or regression tests.

## Failure Categories

| Failure category | Primary investigation areas | Useful evidence |
|---|---|---|
| IAM authorization | Identity policies, resource policies, boundaries, SCPs, session policies | Error response, policy documents, caller identity, CloudTrail event |
| Role assumption | Trust policy, principal ARN, external ID, MFA conditions, STS configuration | `AssumeRole` error, trust policy, STS event |
| Temporary credentials | Expiration, session token, credential provider chain, role session | `get-caller-identity`, credential-provider diagnostics, request timestamp |
| Request signing | SigV4 canonical request, signing region, service name, timestamp, session token | HTTP response, sanitized signing metadata, endpoint configuration |
| Encryption and KMS | IAM permissions, key policy, grants, encryption context, key state | KMS API error, key metadata, CloudTrail event |
| Secrets and configuration | Secret ARN, resource policy, retrieval permissions, rotation, network access | Secret metadata, application logs, rotation status |
| Network security | Security groups, network ACLs, route tables, DNS, endpoint policies | Connectivity tests, VPC configuration, flow logs where enabled |
| Audit and detection | CloudTrail configuration, event selectors, delivery status, service integration | Trail status, event history, destination health, security findings |

## Common Diagnostic Commands

The following commands are primarily read-only inspection operations. Replace placeholders with the relevant account IDs, regions, role names, and resource identifiers. Run them using an identity authorized to inspect the relevant resources.

### Verify the active identity

```bash
aws sts get-caller-identity
```

**Purpose:** Identify the AWS account and principal associated with the current credential provider chain.

**Interpretation:** An unexpected account or assumed-role ARN often indicates a profile, environment-variable, workload-identity, or credential-provider configuration issue.

### Inspect an IAM role

```bash
aws iam get-role \
  --role-name <ROLE_NAME>
```

**Purpose:** Retrieve role metadata and its trust policy.

**Interpretation:** Check the trusted principal, allowed STS action, and relevant conditions. This command does not establish that the role's identity policies permit the intended workload operation.

### Inspect attached role policies

```bash
aws iam list-attached-role-policies \
  --role-name <ROLE_NAME>

aws iam list-role-policies \
  --role-name <ROLE_NAME>
```

**Purpose:** Identify managed policies attached to a role and inline policies defined directly on it.

**Interpretation:** These commands enumerate policies; they do not calculate all effective permissions across organization controls, resource policies, session policies, and other applicable restrictions.

### Inspect a KMS key

```bash
aws kms describe-key \
  --key-id <KEY_ID> \
  --region <AWS_REGION>

aws kms get-key-policy \
  --key-id <KEY_ID> \
  --policy-name default \
  --region <AWS_REGION>
```

**Purpose:** Inspect key metadata and the default key policy.

**Interpretation:** Verify key state, key ARN, account, region, and policy statements. Effective access can also depend on IAM policies, grants, encryption context, and the calling service's authorization path.

### Inspect a secret without retrieving its value

```bash
aws secretsmanager describe-secret \
  --secret-id <SECRET_ID> \
  --region <AWS_REGION>
```

**Purpose:** Inspect secret metadata, rotation configuration, and relevant status information without requesting the secret value.

**Interpretation:** Metadata inspection does not prove that the application can retrieve the secret. Verify the caller's permissions, secret resource policy where applicable, KMS access if a customer-managed key is used, and network connectivity.

### Inspect CloudTrail delivery status

```bash
aws cloudtrail describe-trails \
  --region <AWS_REGION>

aws cloudtrail get-trail-status \
  --name <TRAIL_ARN_OR_NAME> \
  --region <AWS_REGION>
```

**Purpose:** Inspect trail configuration and delivery status.

**Interpretation:** Check the configured destination and relevant delivery errors. A healthy trail status does not prove that every event category, resource type, or region is covered by the trail's selectors.

## Security Investigation Principles

- **Do not broaden permissions to discover the cause.** Inspect policy evaluation and resource-specific controls before changing authorization.
- **Distinguish authentication from authorization.** Invalid or expired credentials, failed SigV4 validation, and valid credentials lacking permissions are different failure classes.
- **Preserve audit evidence.** Record timestamps, request IDs, principal ARNs, event names, and resource identifiers before making changes.
- **Protect sensitive diagnostics.** Never paste access keys, secret values, session tokens, authorization headers, or complete signed requests into tickets or logs.
- **Account for policy layers.** A valid identity policy may not overcome an explicit deny, an SCP restriction, a permissions boundary, a session policy, or a resource-level restriction.
- **Verify the complete request path.** Application authorization, IAM authorization, KMS permissions, network reachability, and service configuration may independently affect the outcome.

## Production Readiness Checklist

Use this checklist during security troubleshooting and post-incident reviews.

- [ ] The active AWS account, principal, region, and resource ARN have been verified.
- [ ] The original error, request ID, timestamp, and relevant CloudTrail evidence have been captured.
- [ ] Applicable identity, trust, resource, boundary, session, and organization policies have been inspected.
- [ ] KMS, secrets, endpoint, and network controls have been evaluated where relevant.
- [ ] The remediation changes only the required permission or configuration.
- [ ] The original operation succeeds after remediation.
- [ ] Unrelated permissions and security boundaries remain intact.
- [ ] Credential exposure, persistence, and rotation risks have been addressed.
- [ ] Monitoring, regression tests, and preventive controls have been updated where appropriate.

## Key Takeaways

- Diagnose AWS security failures by verifying the principal, action, resource, region, and applicable policy layers before changing controls.
- Separate credential and SigV4 failures from IAM authorization, KMS access, secrets retrieval, and network connectivity failures.
- Use read-only AWS CLI commands and CloudTrail evidence to establish the cause before applying a narrowly scoped remediation.
- Preserve sensitive information and audit evidence throughout investigations, especially during suspected credential compromise.
- Validate the fix end to end and add preventive controls, monitoring, and regression tests to reduce recurrence.