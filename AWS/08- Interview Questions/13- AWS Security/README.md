# README

## Overview

This folder contains senior-level interview preparation material for **AWS Security**, focused on the identity, access control, cryptography, network protection, threat detection, and operational practices required to secure production AWS workloads.

The documentation is intended for backend engineers progressing toward senior engineering and technical leadership roles. It emphasizes practical security decisions, troubleshooting, architectural trade-offs, and incident response rather than isolated service definitions.

The material connects AWS security controls with common backend technologies and delivery practices, including Python, Django, FastAPI, REST APIs, microservices, Docker, and CI/CD.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Core AWS Security Interview Questions](./01-%20Core%20AWS%20Security%20Interview%20Questions.md) | Core AWS security concepts, shared responsibility, and foundational interview questions |
| 02 | [02- IAM and Access Control Questions](./02-%20IAM%20and%20Access%20Control%20Questions.md) | IAM principals, roles, policies, trust relationships, explicit denies, SCPs, and authorization troubleshooting |
| 03 | [03- Encryption and KMS Questions](./03-%20Encryption%20and%20KMS%20Questions.md) | Encryption at rest and in transit, KMS keys, key policies, grants, envelope encryption, and rotation |
| 04 | [04- Network Security Questions](./04-%20Network%20Security%20Questions.md) | VPC security boundaries, security groups, network ACLs, VPC endpoints, PrivateLink, WAF, and Shield |
| 05 | [05- Threat Detection and Monitoring Questions](./05-%20Threat%20Detection%20and%20Monitoring%20Questions.md) | CloudTrail, GuardDuty, Security Hub, CloudWatch, AWS Config, centralized logging, and security findings |
| 06 | [06- Compliance and Auditing Questions](./06-%20Compliance%20and%20Auditing%20Questions.md) | Compliance controls, audit evidence, configuration evaluation, and regulatory requirements |
| 07 | [07- Scenario Based Security Questions](./07-%20Scenario%20Based%20Security%20Questions.md) | Scenario-based questions covering production security decisions, trade-offs, and design choices |
| 08 | [08- AWS Security Architecture Questions](./08-%20AWS%20Security%20Architecture%20Questions.md) | Production security architecture, multi-account environments, cross-account access, and defense-in-depth design |
| 09 | [09- Troubleshooting and Incident Response Questions](./09-%20Troubleshooting%20and%20Incident%20Response%20Questions.md) | Credential compromise, suspicious API activity, containment, evidence preservation, and recovery |
| 10 | [10- AWS Security Service Comparison Questions](./10-%20AWS%20Security%20Service%20Comparison%20Questions.md) | Comparative analysis of AWS security services, capabilities, and appropriate use cases |
| 11 | [11- Common Interview Traps](./11-%20Common%20Interview%20Traps.md) | Common security misconceptions, misleading interview statements, and scenario-based corrections |
| 12 | [12- Senior Level Questions](./12-%20Senior%20Level%20Questions.md) | Senior-level questions covering architecture, IAM, cryptography, incident response, and engineering trade-offs |

> **Note:** The navigation table describes the intended documentation structure. Verify that each linked file exists in the repository and adjust filenames or links to match the actual folder contents.

## Recommended Study Order

Study the material in a progression that builds from security fundamentals to implementation, operations, and senior-level reasoning.

| Phase | Focus | Expected capability |
|---|---|---|
| Foundations | Core Security Concepts | Explain shared responsibility, trust boundaries, least privilege, and defense in depth. |
| Identity | IAM and Policy Evaluation; Authentication and Authorization | Diagnose authorization failures and design secure role-assumption flows. |
| Data Protection | Encryption and KMS; Secrets Management | Secure sensitive data, manage key access, and implement credential rotation. |
| Infrastructure | Network Security; Security Architecture Scenarios | Design layered network and identity controls for backend workloads. |
| Operations | Security Monitoring and Detection; Incident Response | Investigate suspicious activity, preserve evidence, and recover securely. |
| Interview Preparation | Troubleshooting and Diagnostics; Common Interview Traps; Senior Level Questions | Explain root causes, defend architectural decisions, and evaluate operational trade-offs. |

## How to Use These Notes

### For concept revision

Focus on the purpose of each security control, its authorization model, its limitations, and the conditions under which it is appropriate.

### For hands-on practice

Use a dedicated development AWS account or sandbox with non-sensitive resources. Prefer temporary credentials and narrowly scoped IAM permissions. Review expected charges before enabling services that incur costs.

Practice tasks can include:

- Inspecting the active identity with `aws sts get-caller-identity`.
- Examining IAM role trust policies and attached permissions.
- Retrieving a test secret through an authorized workload identity.
- Inspecting KMS key metadata and applicable permissions.
- Investigating API activity using CloudTrail.
- Reviewing security-group rules and relevant security findings.
- Testing whether a workload can access its intended resources while being denied access to unrelated resources.

Clean up temporary resources after exercises and verify that no unnecessary credentials, public access paths, or privileged policies remain.

### For interview preparation

For scenario-based questions, structure answers around:

1. **Context:** Identify the principal, resource, account, network path, and data involved.
2. **Failure or threat:** State the suspected security boundary or control that may have failed.
3. **Evidence:** Identify the AWS CLI commands, logs, policies, and audit events needed to investigate.
4. **Remediation:** Explain the narrowest justified corrective action.
5. **Verification:** Demonstrate how to confirm the fix and preserve the intended security boundary.
6. **Prevention:** Identify automation, monitoring, testing, or governance improvements that reduce recurrence.

## Engineering Standards

Apply the following principles when designing or reviewing AWS security controls:

- Prefer short-lived credentials and workload identities over long-lived access keys.
- Apply least privilege to runtime roles, deployment identities, and cross-account access.
- Treat authentication, authorization, request signing, network reachability, and encryption as distinct concerns.
- Protect secrets and key material throughout retrieval, caching, logging, rotation, and recovery.
- Centralize audit evidence and security findings while restricting access to the evidence itself.
- Avoid resolving authorization failures by granting broad permissions without identifying the root cause.
- Validate security controls through negative tests, configuration checks, and observable evidence.
- Treat incident response, credential revocation, and recovery as operational workflows that require testing.

## Key Takeaways

- AWS security depends on coordinated identity, network, application, cryptographic, and operational controls.
- Senior engineers must understand effective authorization and diagnose failures using evidence rather than broad permission changes.
- Secure backend systems require workload identity, controlled secret lifecycles, least privilege, and layered protection.
- Centralized monitoring and incident-response readiness are essential for detecting, containing, and investigating security incidents.
- Interview answers should demonstrate practical implementation, root-cause analysis, measurable verification, and awareness of production trade-offs.