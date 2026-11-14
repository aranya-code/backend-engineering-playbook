# 04- AWS CLI Profile and Account Mismatch

## Overview

Amazon S3 operations can fail or affect the wrong resources when the AWS CLI uses an unexpected profile, credential source, IAM role, AWS account, or Region. These problems frequently occur when developers switch between local development, staging, production, cross-account environments, and CI/CD pipelines.

A common example is a command intended to inspect a production bucket that executes using a development account's credentials. Depending on the resource and permissions, the request may return `AccessDenied`, `NoSuchBucket`, a Region-related error, or even succeed against an unintended resource.

The critical distinction is between the **configured profile** and the **effective AWS identity**. A profile is a named configuration that can select credentials, a role, an SSO session, and a default Region. It does not, by itself, guarantee which principal ultimately signs the request.

This document covers:

- Diagnosing AWS CLI profile and account mismatches.
- Understanding credential-provider and configuration precedence.
- Inspecting profiles, credentials, Regions, and role assumptions.
- Troubleshooting Windows terminals, Docker, CI/CD, and AWS IAM Identity Center.
- Correcting cross-account S3 access failures safely.
- Preventing unintended production operations.

## Understand AWS CLI Profiles

An AWS CLI profile groups configuration associated with a particular way of accessing AWS.

For example, a developer might maintain separate profiles for development, staging, and production:

| Profile | Intended account | Typical purpose |
|---|---|---|
| `default` | Development account | Local experimentation |
| `development` | Development account | Development resources |
| `staging` | Staging account | Integration testing |
| `production` | Production account | Production operations |
| `analytics` | Analytics account | Data processing |

These are illustrative names. Profile names do not enforce account boundaries or permissions.

### Configuration files

On Windows, the shared AWS CLI files are normally located under:

```text
%USERPROFILE%\.aws\config
%USERPROFILE%\.aws\credentials
```

On Linux and macOS:

```text
~/.aws/config
~/.aws/credentials
```

The files serve different purposes:

- `config` stores settings such as Region, output format, role configuration, and IAM Identity Center configuration.
- `credentials` commonly stores static access keys or credential entries used by profiles.

Example `config` file:

```ini
[default]
region = ap-south-1
output = json

[profile development]
region = ap-south-1
output = json

[profile production]
region = ap-south-1
output = json
```

Example `credentials` file:

```ini
[default]
aws_access_key_id = EXAMPLE_DEVELOPMENT_ACCESS_KEY
aws_secret_access_key = EXAMPLE_DEVELOPMENT_SECRET_KEY

[development]
aws_access_key_id = EXAMPLE_DEVELOPMENT_ACCESS_KEY
aws_secret_access_key = EXAMPLE_DEVELOPMENT_SECRET_KEY
```

The credentials above are placeholders, not usable credentials. Production access should normally use an appropriate role or federated credential flow instead of long-lived access keys.

Notice that profile names in the two files have different syntax:

- In `config`, a named profile uses `[profile production]`.
- In `credentials`, it uses `[production]`.

The `default` profile does not use the `profile` prefix in either file.

## Understand Credential and Profile Precedence

The AWS CLI can obtain credentials from several sources, including environment variables, shared credential files, IAM Identity Center, role assumptions, web identity, container credentials, and EC2 instance profiles.

The exact provider behavior depends on the configured credential chain. Do not assume that the profile visible in the command determines the identity independently of all other settings.

### Common configuration sources

| Source | Example | Typical risk |
|---|---|---|
| Command-line option | `--profile production` | The selected profile may not target the expected account |
| `AWS_PROFILE` | Environment variable set to `development` | Commands without an explicit profile use an unexpected profile |
| `AWS_ACCESS_KEY_ID` and related variables | Credentials exported in the terminal | Environment credentials can take precedence over shared profile credentials |
| Shared credentials file | `~/.aws/credentials` | Old or incorrect credentials remain configured |
| Shared config file | `~/.aws/config` | Wrong Region, role ARN, or credential-source configuration |
| IAM Identity Center | SSO profile | Login is missing, expired, or associated with another account or role |
| Assume-role profile | `role_arn` and `source_profile` | Source credentials or target role are incorrect |
| Container credentials | ECS task role | Container uses a different principal from the host |
| Instance profile | EC2 IAM role | CLI uses the instance role rather than the developer's expected user credentials |
| Web identity | `AWS_ROLE_ARN` and `AWS_WEB_IDENTITY_TOKEN_FILE` | Runtime assumes a role different from the expected role |

### Explicitly select the intended profile

Prefer making the profile explicit for local administrative and troubleshooting commands:

```bash
aws sts get-caller-identity \
  --profile production
```

For an S3 operation:

```bash
aws s3api head-bucket \
  --bucket company-prod-documents-123456789012 \
  --expected-bucket-owner 123456789012 \
  --region ap-south-1 \
  --profile production
```

Replace the example bucket, account ID, Region, and profile with the verified production values.

Specifying `--profile production` is useful, but still inspect the resulting identity. Environment-provided credentials and profile-specific credential settings can affect which credentials are used.

### Inspect environment variables

On Windows PowerShell:

```powershell
$env:AWS_PROFILE
$env:AWS_REGION
$env:AWS_DEFAULT_REGION
$env:AWS_ACCESS_KEY_ID
$env:AWS_SECRET_ACCESS_KEY
$env:AWS_SESSION_TOKEN
```

On Linux or macOS:

```bash
printf 'AWS_PROFILE=%s\n' "${AWS_PROFILE:-<unset>}"
printf 'AWS_REGION=%s\n' "${AWS_REGION:-<unset>}"
printf 'AWS_DEFAULT_REGION=%s\n' "${AWS_DEFAULT_REGION:-<unset>}"
```

To check whether credential variables are present without displaying their values in Linux or macOS:

```bash
for name in AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN; do
  if printenv "$name" >/dev/null; then
    printf '%s is set\n' "$name"
  else
    printf '%s is not set\n' "$name"
  fi
done
```

Do not share terminal output containing secret keys or session tokens. In particular, avoid posting the output of indiscriminate environment-dump commands to incident tickets.

## Diagnose the Effective AWS Identity

The most reliable first step is to query STS using the same profile and execution environment as the failing operation.

### Check the default identity

```bash
aws sts get-caller-identity
```

### Check a named profile

```bash
aws sts get-caller-identity \
  --profile production
```

Example output:

```json
{
  "UserId": "AROAXXXXXXXXXXXXX:production-session",
  "Account": "123456789012",
  "Arn": "arn:aws:sts::123456789012:assumed-role/ProductionAccessRole/production-session"
}
```

Interpret the result as follows:

| Field | What it establishes |
|---|---|
| `Account` | AWS account associated with the effective principal |
| `Arn` | Effective IAM user, role session, or other principal ARN |
| `UserId` | Principal identifier, which may include role-session information |

Compare the account ID and ARN with the identity expected for the operation.

A role-session ARN such as:

```text
arn:aws:sts::123456789012:assumed-role/ProductionAccessRole/production-session
```

is different from the IAM role ARN:

```text
arn:aws:iam::123456789012:role/ProductionAccessRole
```

The role session is the identity making the request. This distinction is important when troubleshooting policies that use `aws:PrincipalArn`, trust relationships, or other principal-related conditions.

### Compare default and named-profile identities

Run both commands:

```bash
aws sts get-caller-identity
```

```bash
aws sts get-caller-identity \
  --profile production
```

If the identities differ, the default credential configuration and the named profile select different effective identities.

That difference is not inherently wrong. It becomes a problem when the command uses the wrong identity for the intended resource.

If both commands unexpectedly return the same identity, inspect environment credentials, the selected profile configuration, and any role or credential-source settings.

## Inspect Available Profiles and Configuration

### List configured profiles

```bash
aws configure list-profiles
```

Example output:

```text
default
development
staging
production
analytics
```

The command lists known profiles, not proof that each profile has usable credentials or targets a particular account.

### Inspect the selected profile's configuration

```bash
aws configure list \
  --profile production
```

This command displays the active CLI configuration values and their sources, which helps identify whether the Region and credentials originate from the expected configuration source.

It does not replace `sts get-caller-identity` for verifying the effective identity.

Inspect the configured Region:

```bash
aws configure get region \
  --profile production
```

If the returned value is empty, the profile may not define a Region. A Region can still be supplied by another configuration source or explicitly through `--region`.

### Inspect profile files safely

Review the configuration files for:

- Incorrect profile names.
- Stale or duplicate credential entries.
- Unexpected `role_arn` values.
- Incorrect `source_profile` references.
- Wrong Region settings.
- Unexpected credential-source configuration.
- An incorrect `sso_account_id` or `sso_role_name`.

Do not print or share credential files containing real keys. Prefer commands that display configuration metadata without exposing sensitive values.

## Troubleshoot Profile Selection in Windows PowerShell and VS Code

A frequent Windows scenario is that commands run in a VS Code terminal with a profile different from the one expected.

### Check the current PowerShell session

```powershell
$env:AWS_PROFILE
aws sts get-caller-identity
```

If `AWS_PROFILE` contains an unexpected value, set the intended profile for the current session:

```powershell
$env:AWS_PROFILE = "production"
aws sts get-caller-identity
```

For a one-off operation, using `--profile production` can make the selection explicit:

```powershell
aws s3api list-objects-v2 `
  --bucket company-prod-documents-123456789012 `
  --prefix reports/ `
  --region ap-south-1 `
  --profile production
```

PowerShell uses the backtick character for line continuation. Avoid trailing spaces after a continuation backtick because they can cause command-parsing errors.

### Remove unintended environment credential overrides

If old credentials were exported into the current PowerShell session, they can override the credentials expected from the shared profile.

First verify which credential variables are set. If they are no longer required and you intend to use the selected profile, remove them from the current process:

```powershell
Remove-Item Env:AWS_ACCESS_KEY_ID -ErrorAction SilentlyContinue
Remove-Item Env:AWS_SECRET_ACCESS_KEY -ErrorAction SilentlyContinue
Remove-Item Env:AWS_SESSION_TOKEN -ErrorAction SilentlyContinue
```

Then select the intended profile:

```powershell
$env:AWS_PROFILE = "production"
aws sts get-caller-identity
```

These commands affect the current PowerShell process only. They do not remove persisted environment variables or modify AWS credential files.

Before removing environment credentials, confirm that the current process does not depend on them for another required workflow.

### Check the profile using the CLI directly

Even when a profile environment variable is set:

```powershell
aws sts get-caller-identity --profile production
```

Use this to compare the explicitly selected profile with the current default identity.

If the identity remains unexpected, inspect the profile's credential and role configuration rather than repeatedly changing the profile name.

## Diagnose IAM Identity Center (AWS SSO)

Profiles using IAM Identity Center can select credentials for a particular account and role. A valid SSO login does not mean the session is associated with the intended account.

### Example SSO profile

```ini
[profile production]
sso_session = company-sso
sso_account_id = 123456789012
sso_role_name = ProductionAccessRole
region = ap-south-1
output = json

[sso-session company-sso]
sso_start_url = https://example.awsapps.com/start
sso_region = ap-south-1
sso_registration_scopes = sso:account:access
```

The URLs, account ID, and role name are illustrative placeholders. Use the organization's actual IAM Identity Center configuration.

### Log in to the intended profile

```bash
aws sso login --profile production
```

Then verify the actual identity:

```bash
aws sts get-caller-identity \
  --profile production
```

If the profile targets the wrong account or role, correct the profile configuration with the authorized account ID and role name.

Do not assume that logging in again will fix an incorrect `sso_account_id` or `sso_role_name`.

### Common SSO failure scenarios

| Symptom | Likely cause | Corrective action |
|---|---|---|
| Expired-session error | The cached SSO session is no longer valid | Log in again with the intended profile |
| Unexpected account ID | Profile points to another account | Verify `sso_account_id` |
| Unexpected principal | Profile selects a different permission set or role | Verify `sso_role_name` and organization assignments |
| Profile fails to authenticate | Incorrect SSO configuration or missing assignment | Verify the start URL, SSO Region, account access, and role assignment |
| CLI succeeds but S3 access fails | SSO authentication works, but resource authorization may be missing | Inspect S3 permissions and applicable resource policies |

Authentication and authorization are separate. A successful SSO login provides credentials, but those credentials still need the permissions required for the requested S3 operation.

## Diagnose AssumeRole Profile Mismatches

An AWS CLI profile can assume a role using another profile as its credential source.

Example:

```ini
[profile production]
role_arn = arn:aws:iam::123456789012:role/ProductionAccessRole
source_profile = development
region = ap-south-1
role_session_name = production-cli-session
```

In this example, the `development` profile supplies the credentials used to request the production role session. If the source credentials cannot assume the role, the request fails before the target role can access S3.

The active identity should be the assumed role when the configuration works as intended.

### Verify the source profile

```bash
aws sts get-caller-identity \
  --profile development
```

### Verify the assumed-role profile

```bash
aws sts get-caller-identity \
  --profile production
```

Compare the output with the expected role ARN and account ID.

Investigate:

- Whether the source profile has the required `sts:AssumeRole` permission.
- Whether the target role's trust policy authorizes the source principal.
- Whether an external ID or another trust condition is required.
- Whether the target role has permission for the required S3 operation.
- Whether an applicable session policy or permissions boundary restricts the request.

### Different credential-source patterns

Role profiles can use different credential sources, including shared profiles, web identity, and other supported mechanisms. When troubleshooting, inspect the actual profile definition rather than assuming `source_profile` is always present.

Do not store long-lived production access keys inside a profile merely to simplify role assumption when an approved federated or workload identity flow is available.

## Verify the S3 Bucket Account and Region

After confirming the caller identity, validate that the request targets the intended bucket.

For an existing bucket, use an appropriately authorized profile:

```bash
aws s3api head-bucket \
  --bucket company-prod-documents-123456789012 \
  --expected-bucket-owner 123456789012 \
  --region ap-south-1 \
  --profile production
```

The `--expected-bucket-owner` option helps detect an unexpected resource owner. It does not grant permissions, and a failed response should be interpreted in context.

Inspect the bucket Region when authorized:

```bash
aws s3api get-bucket-location \
  --bucket company-prod-documents-123456789012 \
  --profile production
```

When the returned `LocationConstraint` is `null`, the bucket is in `us-east-1`.

For the original object operation, specify the verified Region and identity explicitly:

```bash
aws s3api get-object \
  --bucket company-prod-documents-123456789012 \
  --key reports/report.pdf \
  ./report.pdf \
  --expected-bucket-owner 123456789012 \
  --region ap-south-1 \
  --profile production
```

Replace all placeholders with values verified for the target environment.

A `403` does not prove that the bucket exists or that the profile is incorrect. It may indicate that the selected principal lacks permission or that an applicable policy restricts the request.

If the bucket can be accessed but an object operation fails, continue with the relevant S3 authorization, object-key, and encryption diagnostics instead of repeatedly changing the profile.

## Diagnose Docker and Container Identity Mismatches

The identity of the host shell is not necessarily the identity used by an application inside a container.

For example, a developer can verify the production profile on the host while a Docker container uses different environment variables or an attached workload credential source.

### Inspect configuration in the container

Run the identity check from inside the container using the same execution context as the application:

```bash
aws sts get-caller-identity
```

If supported by the container's setup, inspect non-secret configuration values:

```bash
printf 'AWS_PROFILE=%s\n' "${AWS_PROFILE:-<unset>}"
printf 'AWS_REGION=%s\n' "${AWS_REGION:-<unset>}"
printf 'AWS_DEFAULT_REGION=%s\n' "${AWS_DEFAULT_REGION:-<unset>}"
```

Compare the container's effective identity with the identity expected for the workload.

### Prefer workload identity over copied credentials

In production, prefer the credential mechanism designed for the environment, such as an ECS task role, EC2 instance profile, or an approved Kubernetes workload identity integration.

Do not copy a developer's entire `.aws` directory into a production image. This can expose credentials, produce unpredictable identity selection, and make deployments dependent on local configuration.

For local development, profile access can be configured intentionally, but credential files should be mounted or supplied securely and should not be embedded in the built image.

## Diagnose CI/CD and Deployment Pipeline Mismatches

Deployment pipelines often use a different identity from the application that runs after deployment.

For example:

- GitHub Actions assumes an infrastructure-deployment role.
- Terraform creates an S3 bucket.
- The application later runs under a restricted runtime role.
- The runtime role lacks permission to access the bucket even though infrastructure deployment succeeded.

The successful deployment proves only that the deployment identity could perform the actions it executed. It does not prove that the runtime identity can access the resulting resources.

### Verify identity during deployment

Add an identity check to the relevant workflow before sensitive infrastructure or S3 operations:

```yaml
- name: Verify AWS identity
  run: aws sts get-caller-identity
```

The workflow should already configure AWS credentials through its approved mechanism.

Do not print credential environment variables or secret values for debugging.

### Verify the runtime separately

After deployment, perform a smoke test using the runtime workload identity. Validate the bucket, object access, and other operations required by the application.

For infrastructure-as-code deployments, compare:

- The deployment account and Region.
- The actual bucket name returned by infrastructure outputs.
- The runtime account and role.
- The bucket's expected owner.
- The permissions assigned to the runtime role.

This separation prevents an administrator or deployment role from masking an application-level permission defect.

## Diagnose Common Profile and Account Failure Patterns

| Symptom | Likely cause | Diagnostic command or check |
|---|---|---|
| Default command returns the wrong account | Unexpected default profile or environment credentials | `aws sts get-caller-identity` |
| Explicit profile returns an unexpected account | Profile configuration or credential source is incorrect | `aws sts get-caller-identity --profile production` |
| CLI works without a profile but fails with one | Named profile contains different credentials, Region, or role settings | `aws configure list --profile production` |
| SSO login works but the wrong role is used | Incorrect SSO account or role configuration | Inspect the SSO profile and verify the resulting STS identity |
| Role assumption fails | Incorrect source credentials, trust policy, or STS permission | Verify caller identity and role configuration |
| Bucket exists but CLI reports `AccessDenied` | Permissions or conditions do not allow the active identity | Inspect IAM, bucket policy, and relevant restrictions |
| Bucket appears missing | Wrong name, account, or endpoint may be used | Verify caller, expected owner, bucket name, and Region |
| Host CLI succeeds but container fails | Container credential chain or environment differs | Run identity checks inside the container |
| Terraform succeeds but application fails | Deployment role and runtime role differ | Verify both identities and test using the runtime principal |
| Commands target different Regions | Region source or explicit option differs | `aws configure list --profile production` and inspect the request's `--region` |

## Correct the Mismatch Safely

Once the effective identity and intended resource have been established, apply the smallest necessary correction.

### Wrong profile selected

Set the intended profile for the current process:

```powershell
$env:AWS_PROFILE = "production"
aws sts get-caller-identity
```

Alternatively, use `--profile production` on the command.

### Stale environment credentials

If environment credential variables override the expected shared-profile credentials, remove the obsolete variables from the current process after confirming they are no longer required.

Repeat the identity check before running any operation that modifies production resources.

### Incorrect Region

Set the bucket's verified Region through the profile or explicitly through `--region`.

Do not assume the compute workload and S3 bucket must be in the same Region.

### Incorrect role or account configuration

Correct the source profile, target role ARN, SSO account, or role assignment according to the organization's access model.

Do not grant broader permissions simply to make an incorrect account configuration work.

### Incorrect S3 authorization

If the effective principal and destination resource are correct, investigate the required S3 permissions, resource policy, organizational restrictions, VPC endpoint policy, and KMS authorization where applicable.

A profile correction cannot fix a missing permission on the intended identity.

## Production Prevention and Operational Best Practices

### Make identity selection explicit

For sensitive production CLI operations, specify the profile and Region explicitly when appropriate, and use `--expected-bucket-owner` for supported S3 operations when the bucket owner is known.

Before destructive operations, verify the effective account and resource identifiers independently. Do not rely on profile names such as `production` as proof of the account being targeted.

### Keep environments isolated

Use clearly named profiles and environment-specific configuration. Avoid reusing one generic profile for unrelated AWS accounts unless the role and environment-selection model is deliberate.

Where possible, separate production deployment identities from runtime identities and grant each only the permissions needed for its role.

### Prefer temporary credentials

Use approved federated access, IAM Identity Center, or workload roles rather than distributing long-lived credentials.

Avoid embedding static access keys in source code, Docker images, workflow files, or committed configuration.

### Add deployment and runtime checks

Identity checks should run at the points where configuration can differ:

- Local developer workflows.
- Infrastructure deployment pipelines.
- Application startup or deployment smoke tests.
- Background worker deployment.
- Production operational runbooks.

These checks should confirm the intended account and role without exposing credentials.

### Make failures actionable

Record the operation, error code, request ID, expected account, and relevant resource identifier in an appropriately protected log. Do not expose secrets or unnecessary internal resource information to public API callers.

Investigate recurring mismatches to determine whether the root cause is profile selection, credential-provider precedence, deployment configuration, role assumption, or missing authorization.

## Production Troubleshooting Checklist

- [ ] Run `aws sts get-caller-identity` in the exact environment that runs the failing command.
- [ ] Compare the default identity with the explicitly selected profile.
- [ ] Inspect `AWS_PROFILE`, Region variables, and the presence of credential environment variables.
- [ ] Review `aws configure list-profiles` and `aws configure list --profile production`.
- [ ] Verify SSO account and role configuration, if applicable.
- [ ] Verify source-profile credentials, role trust, and target-role permissions, if using `AssumeRole`.
- [ ] Confirm the bucket name, expected owner account, and actual Region.
- [ ] Test the original S3 operation using the intended identity and request parameters.
- [ ] Run identity checks inside Docker, CI/CD, or runtime environments when their credentials may differ from the host.
- [ ] Apply the smallest necessary correction without expanding permissions unnecessarily.
- [ ] Verify that unauthorized identities and unintended resource scopes remain inaccessible.
- [ ] Update deployment documentation and regression tests to prevent recurrence.

## Official References

- [AWS CLI configuration and credential settings](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- [AWS CLI configuration variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)
- [AWS CLI `configure list` reference](https://docs.aws.amazon.com/cli/latest/reference/configure/list.html)
- [AWS CLI `configure list-profiles` reference](https://docs.aws.amazon.com/cli/latest/reference/configure/list-profiles.html)
- [AWS CLI `get-caller-identity` reference](https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html)
- [AWS CLI IAM Identity Center configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html)
- [AWS CLI role configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-role.html)
- [AWS CLI `HeadBucket` reference](https://docs.aws.amazon.com/cli/latest/reference/s3api/head-bucket.html)
- [AWS IAM policy evaluation logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html)

## Key Takeaways

- Always verify the effective AWS identity with `aws sts get-caller-identity`; a profile name alone does not establish the account or principal used by a request.
- Environment credentials, profile configuration, SSO sessions, and role assumptions can select different identities, so inspect the credential source when the account is unexpected.
- Validate the caller account, bucket owner, Region, and actual endpoint before concluding that an S3 resource is missing.
- Deployment credentials and runtime credentials are separate security contexts; test S3 operations using the identity that actually runs the application.
- Correct the source of the mismatch instead of granting broader permissions or recreating production resources as a workaround.