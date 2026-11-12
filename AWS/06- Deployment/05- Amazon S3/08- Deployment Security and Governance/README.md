# README

## Overview

Deployment security and governance for Amazon S3 covers the role design, permission separation, encryption validation, public access guardrails, tagging standards, policy-as-code checks, production resource protection, deployment auditability, compliance validation, and secure template practices required to deploy S3 infrastructure that meets security and governance requirements consistently. It addresses the full security governance lifecycle from deployment role design through pre-deployment compliance validation and post-deployment audit evidence.

This section of the Backend Engineering Playbook provides a structured reference for backend engineers, security engineers, and platform teams who need to enforce security standards, governance controls, and compliance requirements throughout the S3 deployment lifecycle.

The focus is on practical deployment security engineering: designing least-privilege deployment identities, enforcing security standards through automated policy checks, protecting production resources from unauthorized modification, and generating the audit evidence required for security review and compliance validation.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Least-Privilege Deployment Roles](./01-%20Least-Privilege%20Deployment%20Roles.md) | Designing deployment IAM roles with minimum required permissions across S3, IAM, KMS, Lambda, and monitoring services |
| 02 | [02- Separating Infrastructure and Application Permissions](./02-%20Separating%20Infrastructure%20and%20Application%20Permissions.md) | Separating deployment-time infrastructure permissions from runtime application permissions |
| 03 | [03- Encryption and Key Policy Validation](./03-%20Encryption%20and%20Key%20Policy%20Validation.md) | Validating encryption configuration and KMS key policies before and after deployment |
| 04 | [04- Public Access Prevention Guardrails](./04-%20Public%20Access%20Prevention%20Guardrails.md) | Enforcing Block Public Access through IaC, SCP guardrails, and pre-deployment policy checks |
| 05 | [05- Mandatory Tags and Resource Standards](./05-%20Mandatory%20Tags%20and%20Resource%20Standards.md) | Enforcing mandatory resource tags, naming conventions, and resource standards through policy and automation |
| 06 | [06- Policy-as-Code and Configuration Checks](./06-%20Policy-as-Code%20and%20Configuration%20Checks.md) | Automating IaC security scanning using `checkov`, `tfsec`, `cfn-nag`, and custom policy rules |
| 07 | [07- Protected Production Resources](./07-%20Protected%20Production%20Resources.md) | Protecting production S3 buckets and KMS keys from unintended modification, deletion, or access changes |
| 08 | [08- Deployment Auditability and CloudTrail](./08-%20Deployment%20Auditability%20and%20CloudTrail.md) | Recording deployment actions in CloudTrail, protecting audit logs, and producing deployment audit evidence |
| 09 | [09- Compliance Validation Before Deployment](./09-%20Compliance%20Validation%20Before%20Deployment.md) | Verifying security, governance, and regulatory requirements before infrastructure changes reach AWS |
| 10 | [10- Secure Infrastructure Templates](./10-%20Secure%20Infrastructure%20Templates.md) | Building Terraform, CloudFormation, and CDK templates that enforce security defaults and pass automated checks |

## Why Deployment Security and Governance Matters

Deployment pipelines that lack security controls create a path from source code to production that bypasses all manual security review. A single pipeline with overly permissive credentials can be used to create publicly accessible buckets, disable encryption, modify production IAM policies, or exfiltrate data.

Common deployment security risks include:

- Deployment roles with wildcard actions or `arn:*` resource ARNs that grant significantly more access than the deployment requires.
- Infrastructure and application permissions not separated, allowing the deployment pipeline to modify its own execution role or escalate privileges.
- IaC configurations that deploy buckets without Block Public Access, encryption, or versioning, passing no automated security check.
- Production resources without deletion protection, vulnerable to accidental removal during routine deployment operations.
- Deployment actions not recorded in CloudTrail data events, making it impossible to audit what was deployed and by whom.
- Compliance validation performed manually after deployment rather than automatically before, resulting in non-compliant configurations reaching production.

Effective S3 deployment security combines least-privilege deployment roles, automated policy-as-code scanning, production resource protection, mandatory tagging enforcement, and pre-deployment compliance validation integrated into the CI/CD pipeline.

## Documentation Structure

This section is organized into focused documents covering the full deployment security governance lifecycle from identity design through audit evidence.

| Area | Primary focus |
|---|---|
| Deployment roles | Least-privilege IAM roles for deployment pipelines |
| Permission separation | Separating deployment-time and runtime permissions |
| Encryption validation | Pre and post-deployment encryption and key policy checks |
| Public access guardrails | Block Public Access enforcement through IaC and policy |
| Resource standards | Mandatory tags, naming, and configuration enforcement |
| Policy-as-code | Automated IaC security scanning and custom rules |
| Production protection | Deletion protection, change restrictions, and access safeguards |
| Auditability | CloudTrail coverage, log protection, and deployment records |
| Compliance validation | Pre-deployment compliance checks integrated in CI/CD |
| Secure templates | IaC templates with enforced security defaults |

## Core Deployment Security Principles

### Design Deployment Roles with Minimum Required Permissions

A deployment pipeline needs enough IAM permission to create and configure the S3 resources it manages. It does not need access to every bucket in the account, the ability to modify IAM roles it does not own, or access to resources unrelated to S3 deployment. Scope deployment roles to specific resource ARNs and limit actions to those required.

### Separate Deployment Permissions from Runtime Permissions

The IAM role used by a deployment pipeline should not include the permissions used by the application at runtime. An application role that reads from a specific S3 bucket should not also be able to modify bucket policies or create new buckets. Separating these roles limits the blast radius of a compromised pipeline or application credential.

### Automate Security Checks Before Deployment

Integrate IaC security scanning tools such as `checkov`, `tfsec`, or `cfn-nag` into the CI/CD pipeline. Configure these tools to fail the pipeline when insecure configurations are detected — such as missing Block Public Access, absent encryption, or overly permissive bucket policies. Treat security scan failures as deployment blockers, not advisory warnings.

### Protect Production Resources Explicitly

Production S3 buckets and KMS keys should be protected from accidental deletion and unauthorized modification. Use `prevent_destroy` in Terraform, stack policies in CloudFormation, or AWS Organizations SCPs that prevent `s3:DeleteBucket` on tagged production resources. Document and test the intentional decommissioning procedure separately from routine deployments.

### Generate and Protect Deployment Audit Evidence

Ensure CloudTrail management events and, for sensitive buckets, data events are enabled and delivered to a protected audit log destination. Record deployment metadata — pipeline run ID, deploying identity, commit SHA, and timestamp — alongside the CloudTrail evidence to support incident investigation and compliance audits.

## Recommended Deployment Security Workflow

1. **Design deployment roles.** Create dedicated roles per pipeline and environment scoped to minimum required S3, KMS, and IAM actions on specific resource ARNs.
2. **Separate runtime permissions.** Define application execution roles independently from deployment roles. Never grant the deployment role the application's runtime permissions.
3. **Integrate security scanning.** Add `checkov` or equivalent scanning to the CI/CD pipeline. Configure rules for Block Public Access, encryption, versioning, tagging, and bucket policy safety.
4. **Define compliance gates.** Require security scan pass and compliance validation before deployment proceeds to staging or production.
5. **Protect production resources.** Apply `prevent_destroy` or CloudFormation stack policies to production buckets. Apply SCPs where applicable.
6. **Enable CloudTrail coverage.** Confirm CloudTrail management events cover all deployment actions. Enable data events for security-sensitive buckets.
7. **Review and remediate.** Review compliance findings and audit evidence after each deployment. Investigate any unexpected access or configuration change.

## Operational Standards

- **Deployment roles:** Scope to specific S3 bucket ARNs, KMS key ARNs, and required actions. No wildcard resource ARNs in production deployment roles.
- **Permission separation:** Deploy-time and runtime IAM roles must be distinct. The deployment role must not be able to modify the application role.
- **Security scanning:** Run `checkov` or equivalent in CI on every IaC change. Fail the pipeline on security findings.
- **Public access:** Enforce Block Public Access through IaC. Include a policy-as-code check that fails the pipeline if Block Public Access is disabled.
- **Tagging:** Enforce mandatory tags through policy-as-code checks. Fail deployments that do not apply required tags.
- **Production protection:** Apply `prevent_destroy` or stack policies to all production S3 buckets.
- **CloudTrail:** Ensure CloudTrail management events cover all deployment actions. Protect the audit log destination bucket.
- **Compliance validation:** Run compliance checks before every deployment to staging and production. Block deployments that do not meet requirements.

## Key Takeaways

- Deployment roles must be scoped to minimum required permissions per pipeline and environment; wildcard resource ARNs in deployment roles create unnecessary risk.
- Deployment-time and runtime permissions must be separated to prevent privilege escalation through a compromised pipeline or application credential.
- Automated policy-as-code scanning integrated into CI/CD is the only scalable way to catch insecure IaC configurations before they reach AWS.
- Production resource protection through `prevent_destroy` or stack policies prevents accidental data loss during routine deployment operations.
- CloudTrail coverage of deployment actions is essential for incident investigation; without it, it is impossible to determine what was deployed, when, and by whom.
