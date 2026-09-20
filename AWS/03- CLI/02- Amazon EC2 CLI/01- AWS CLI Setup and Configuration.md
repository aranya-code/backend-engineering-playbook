# 01- AWS CLI Setup and Configuration

## Overview

The AWS Command Line Interface (AWS CLI) provides a scriptable interface for managing AWS resources. For EC2 operations, it is commonly used for instance inspection, lifecycle management, networking, storage, Auto Scaling, load balancers, and operational automation.

A production AWS CLI setup should make four things explicit:

- **Identity** — which AWS principal is making the request
- **Account** — which AWS account is being operated on
- **Region** — where the resources exist
- **Configuration** — which CLI settings and credentials are being used

A useful mental model is:

```text
AWS CLI Command
      |
      v
CLI Configuration
      |
      +--> Profile
      |
      +--> Credentials
      |
      +--> Region
      |
      +--> Output / Query settings
      |
      v
AWS API
      |
      v
IAM Authorization
      |
      v
EC2 / Other AWS Service
```

The CLI does not bypass IAM. Every AWS API operation is still evaluated against the permissions of the authenticated principal.

## Why AWS CLI Configuration Matters

EC2 operations are often performed repeatedly and programmatically. Using the CLI allows engineers to:

- Inspect infrastructure quickly
- Automate operational workflows
- Integrate AWS operations into CI/CD
- Troubleshoot production incidents
- Query resources by tags and state
- Perform repeatable infrastructure operations
- Avoid manually navigating the AWS Console for routine tasks

However, the same automation capability makes incorrect credentials or regions dangerous.

A command such as:

```bash
aws ec2 terminate-instances --instance-ids i-0123456789abcdef0
```

is operationally significant. Before running destructive commands, confirm:

```text
Who am I?
Which account?
Which region?
Which resources?
What action?
```

## Installing AWS CLI

AWS CLI version 2 is the standard choice for current AWS CLI usage.

After installation, verify:

```bash
aws --version
```

Typical output resembles:

```text
aws-cli/2.x.x Python/3.x.x ...
```

The exact version varies by platform and release.

Verify that the executable is available:

```bash
which aws
```

On Windows PowerShell:

```powershell
Get-Command aws
```

### Production Consideration

Do not assume that an installed AWS CLI is correctly configured.

Installation only establishes that the client exists. Authentication and authorization are separate concerns.

## AWS CLI Configuration Model

The AWS CLI can obtain configuration from multiple sources.

A simplified precedence model is:

```text
Command-line options
        |
        v
Environment variables
        |
        v
Profile configuration
        |
        v
Shared AWS configuration
        |
        v
Credential providers
```

The exact precedence depends on the specific setting and credential provider.

Common configuration sources include:

| Source | Typical Use |
|---|---|
| Command-line options | One-off overrides |
| Environment variables | CI/CD and temporary configuration |
| `~/.aws/config` | Region, profile, CLI settings |
| `~/.aws/credentials` | Long-lived access-key credentials |
| IAM role | EC2 and AWS-managed workloads |
| AWS IAM Identity Center | Human workforce authentication |
| Container credential provider | Containers running with AWS identity |
| Instance metadata credentials | EC2 workloads using an IAM role |

For production workloads, prefer temporary credentials and IAM roles over long-lived access keys.

## Configuring a Default Profile

The simplest setup is:

```bash
aws configure
```

The CLI prompts for:

```text
AWS Access Key ID
AWS Secret Access Key
Default region name
Default output format
```

For example:

```text
AWS Access Key ID [None]: ...
AWS Secret Access Key [None]: ...
Default region name [None]: ap-south-1
Default output format [None]: json
```

A typical configuration uses:

```text
Region: ap-south-1
Output: json
```

The region should match the AWS resources being operated on.

## Profiles

Profiles allow multiple AWS configurations to coexist.

For example:

```text
default
development
staging
production
```

Configure a named profile:

```bash
aws configure --profile development
```

Then use it explicitly:

```bash
aws ec2 describe-instances \
    --profile development \
    --region ap-south-1
```

This is safer than repeatedly overwriting the default profile when working across multiple environments.

## Profile-Based Environment Separation

A common engineering setup is:

```text
AWS CLI
 |
 +--> development
 |
 +--> staging
 |
 +--> production
```

For example:

```bash
aws sts get-caller-identity --profile development
aws sts get-caller-identity --profile staging
aws sts get-caller-identity --profile production
```

Before performing production operations:

```bash
aws sts get-caller-identity --profile production
```

This provides a basic identity check.

### Production Recommendation

Use separate AWS accounts for environments where possible:

```text
Development Account
        |
Staging Account
        |
Production Account
```

Profiles then become explicit entry points into those environments.

## Region Configuration

AWS resources are generally regional.

For example:

```bash
aws ec2 describe-instances --region ap-south-1
```

is different from:

```bash
aws ec2 describe-instances --region us-east-1
```

An instance existing in one region will not appear in an EC2 query against another region.

### Common Mistake

An engineer runs:

```bash
aws ec2 describe-instances
```

and sees no instances.

The resources may simply exist in another region.

Check the configured region:

```bash
aws configure get region
```

For a specific profile:

```bash
aws configure get region --profile production
```

You can also override it:

```bash
aws ec2 describe-instances \
    --region ap-south-1
```

### Operational Recommendation

For scripts, make the region explicit when ambiguity could cause operational risk.

For example:

```bash
aws ec2 describe-instances \
    --region ap-south-1 \
    --profile production
```

This makes the execution context visible.

## Credential Configuration

### Long-Lived Access Keys

Traditional AWS CLI configuration can store access keys:

```text
AWS Access Key ID
AWS Secret Access Key
```

These credentials identify an IAM principal.

However, long-lived credentials introduce operational risks:

- Credential leakage
- Accidental commits
- Difficult rotation
- Excessive lifetime
- Developer-machine exposure

Never commit credentials to Git.

Do not place them directly into application source code:

```python
# Do not do this.
AWS_ACCESS_KEY_ID = "..."
AWS_SECRET_ACCESS_KEY = "..."
```

Do not put secrets into:

```text
Dockerfile
Git repository
README.md
Shell scripts
CI logs
```

## Environment Variables

AWS CLI can use environment variables such as:

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_DEFAULT_REGION="ap-south-1"
```

On PowerShell:

```powershell
$env:AWS_DEFAULT_REGION="ap-south-1"
```

Environment variables are particularly useful for temporary credentials and CI/CD systems.

Check the active region:

```bash
echo $AWS_DEFAULT_REGION
```

On PowerShell:

```powershell
$env:AWS_DEFAULT_REGION
```

### Security Consideration

Avoid printing secret environment variables in logs.

A debugging command such as:

```bash
env
```

can expose credentials if they are present in the environment.

## IAM Identity Center

For human users, AWS IAM Identity Center is generally preferable to distributing long-lived IAM user access keys.

A typical workflow is:

```bash
aws configure sso
```

Then authenticate:

```bash
aws sso login --profile production
```

Verify:

```bash
aws sts get-caller-identity --profile production
```

The exact authentication flow depends on the organization's AWS configuration.

### Why This Matters

Human authentication should generally use centrally managed identities and temporary credentials rather than permanent access keys.

## IAM Roles for EC2

Applications running on EC2 should generally obtain AWS credentials through an attached IAM role rather than storing access keys on disk.

Architecture:

```text
EC2 Instance
      |
      v
IAM Role
      |
      v
Temporary Credentials
      |
      v
AWS API
```

For example, a Django application running on EC2 may need to access S3.

Prefer:

```text
EC2
 |
 +--> IAM Instance Profile
          |
          v
       IAM Role
          |
          v
       S3 permissions
```

instead of:

```text
EC2
 |
 +--> AWS access key stored in .env
```

This reduces credential-management overhead and avoids embedding long-lived credentials into application deployments.

## Verifying Authentication

The most useful identity diagnostic command is:

```bash
aws sts get-caller-identity
```

Example response:

```json
{
    "UserId": "AIDAXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/example"
}
```

For role-based authentication, the ARN may represent an assumed role.

Use this before performing sensitive operations.

### Production Habit

Make identity verification part of operational workflows:

```bash
aws sts get-caller-identity --profile production
```

Then inspect the target resources:

```bash
aws ec2 describe-instances \
    --profile production \
    --region ap-south-1
```

Only then perform changes.

## Checking the Active Configuration

Useful commands include:

```bash
aws configure list
```

For a named profile:

```bash
aws configure list --profile production
```

Check the configured region:

```bash
aws configure get region
```

Check a profile's region:

```bash
aws configure get region --profile production
```

List configured profiles:

```bash
aws configure list-profiles
```

These commands help distinguish:

```text
CLI configuration problem
```

from:

```text
AWS authorization problem
```

or:

```text
Wrong region/account
```

## Testing EC2 Access

After authentication is verified:

```bash
aws ec2 describe-instances \
    --region ap-south-1
```

For a specific profile:

```bash
aws ec2 describe-instances \
    --profile production \
    --region ap-south-1
```

If the command succeeds but returns no instances, verify:

- Region
- Account
- Filters
- Resource state
- Resource type

Do not immediately assume the EC2 service is unavailable.

## Testing Permissions

Authentication answers:

> Who am I?

Authorization answers:

> What am I allowed to do?

For example:

```bash
aws sts get-caller-identity
```

may succeed while:

```bash
aws ec2 terminate-instances \
    --instance-ids i-0123456789abcdef0
```

fails with an authorization error.

This means the identity is valid but lacks the required permission.

### Example

An IAM policy might permit:

```text
ec2:DescribeInstances
```

without permitting:

```text
ec2:TerminateInstances
```

This is a normal least-privilege configuration.

## Configuration Files

AWS CLI commonly uses:

```text
~/.aws/config
~/.aws/credentials
```

On Windows, these are typically under:

```text
%UserProfile%\.aws\
```

A configuration file may contain:

```ini
[default]
region = ap-south-1
output = json

[profile development]
region = ap-south-1
output = json

[profile production]
region = us-east-1
output = json
```

Credential configuration may contain profiles associated with credentials or credential providers.

### Security Rule

Treat the AWS credentials file as sensitive.

Do not commit:

```text
.aws/
```

into source control.

A repository `.gitignore` should normally exclude local credential files where appropriate.

## Named Profile Workflow

A practical workflow is:

```bash
aws sso login --profile production

aws sts get-caller-identity \
    --profile production

aws ec2 describe-instances \
    --profile production \
    --region ap-south-1
```

For automation:

```text
Authenticate
    |
    v
Verify identity
    |
    v
Verify region
    |
    v
Inspect target
    |
    v
Perform operation
    |
    v
Verify result
```

This is safer than directly executing a destructive command.

## Safe CLI Practices

### Always Identify the Target

Before changing an instance, inspect it:

```bash
aws ec2 describe-instances \
    --instance-ids i-0123456789abcdef0 \
    --region ap-south-1
```

Inspect tags:

```bash
aws ec2 describe-tags \
    --filters \
    "Name=resource-id,Values=i-0123456789abcdef0" \
    --region ap-south-1
```

Confirm:

- Instance ID
- Environment
- Application
- Owner
- Region
- Account

### Prefer Tags Over Guessing

Production resources should use consistent tags such as:

```text
Environment=production
Application=payments-api
Owner=backend-platform
ManagedBy=terraform
```

Then operational commands can target resources deterministically.

### Avoid Broad Destructive Commands

Be extremely careful with commands such as:

```bash
aws ec2 terminate-instances
```

and:

```bash
aws ec2 deregister-image
```

Before destructive operations:

1. Verify account.
2. Verify region.
3. Inspect resource.
4. Confirm resource identity.
5. Understand dependencies.
6. Execute the minimum required change.
7. Verify the result.

## CLI and CI/CD

AWS CLI is frequently used from GitHub Actions and other CI/CD systems.

A production workflow should avoid hard-coded credentials.

Prefer short-lived credentials obtained through an identity federation mechanism such as GitHub Actions OIDC with an appropriately scoped AWS IAM role.

Conceptually:

```text
GitHub Actions
      |
      v
OIDC Identity
      |
      v
AWS IAM Role
      |
      v
Temporary Credentials
      |
      v
AWS CLI
      |
      v
EC2 / AWS APIs
```

This avoids storing long-lived AWS access keys as repository secrets.

## CLI and Python Automation

The AWS CLI is useful for operational commands, while Python applications commonly use the AWS SDK for programmatic integration.

For Python, `boto3` is generally used for AWS API calls.

Example:

```python
import boto3

ec2 = boto3.client("ec2", region_name="ap-south-1")

response = ec2.describe_instances()

for reservation in response["Reservations"]:
    for instance in reservation["Instances"]:
        print(instance["InstanceId"], instance["State"]["Name"])
```

Use the SDK when AWS operations are part of application logic or reusable automation.

Use the CLI when an engineer needs direct operational control or shell-based automation.

## CLI vs AWS Console vs SDK

| Tool | Best Use |
|---|---|
| AWS Console | Visual exploration and configuration |
| AWS CLI | Operations, scripting, troubleshooting, automation |
| Python/Boto3 | Application integration and complex programmatic workflows |
| Infrastructure as Code | Reproducible infrastructure provisioning |
| CI/CD | Automated deployments and controlled operational workflows |

For production infrastructure, manual CLI changes should be used carefully when resources are managed by Infrastructure as Code.

## CLI and Infrastructure as Code

If an EC2 instance is managed by Terraform or CloudFormation, manually changing it with the CLI can create configuration drift.

For example:

```text
Terraform
    |
    v
Desired Infrastructure
    |
    v
AWS
```

A manual CLI change creates:

```text
Terraform state
      !=
AWS actual state
```

### Production Recommendation

Use the CLI for:

- Inspection
- Troubleshooting
- Emergency operations
- Supported operational workflows

Use Infrastructure as Code for:

- Long-lived infrastructure configuration
- Repeatable environments
- Version-controlled changes
- Standardized production provisioning

Follow the organization's source-of-truth model.

## Troubleshooting Authentication Problems

### `Unable to locate credentials`

Likely causes:

- No credentials configured
- Wrong profile
- Missing environment variables
- Expired authentication session
- Credential provider unavailable

Check:

```bash
aws configure list
```

Then:

```bash
aws sts get-caller-identity
```

### `AccessDenied`

The identity is authenticated but lacks authorization.

Check:

- IAM policies
- Resource policies
- Permission boundaries
- Service control policies
- Session policies
- Explicit denies

### Wrong Account

Verify:

```bash
aws sts get-caller-identity
```

Do not infer the account from the profile name alone.

A profile named:

```text
production
```

does not prove that it points to the production account.

### Wrong Region

Check:

```bash
aws configure get region
```

Then explicitly specify the intended region:

```bash
aws ec2 describe-instances \
    --region ap-south-1
```

### Expired SSO Session

Re-authenticate:

```bash
aws sso login --profile production
```

Then verify:

```bash
aws sts get-caller-identity --profile production
```

## Operational CLI Checklist

Before an EC2 change:

```text
[ ] Correct AWS account
[ ] Correct identity
[ ] Correct region
[ ] Correct profile
[ ] Correct instance/resource
[ ] Correct environment
[ ] Correct IAM permissions
[ ] Resource dependencies understood
[ ] Change is reversible where possible
[ ] Result will be verified
```

For destructive operations, add:

```text
[ ] Backup/recovery requirements checked
[ ] Instance state checked
[ ] Auto Scaling ownership checked
[ ] Infrastructure-as-Code ownership checked
[ ] Production impact understood
```

## Common Mistakes

### Running Commands Against the Wrong Region

An empty EC2 response does not necessarily mean there are no instances.

Check the region first.

### Assuming Profile Names Guarantee Safety

A profile called `production` is only a label.

Verify the actual account:

```bash
aws sts get-caller-identity --profile production
```

### Storing Access Keys in Source Code

Never embed AWS credentials in Python, shell scripts, Dockerfiles, or repositories.

Use IAM roles, IAM Identity Center, environment-provided temporary credentials, or another approved credential provider.

### Using Root Credentials

Routine CLI operations should not use the AWS account root user.

Use appropriately scoped IAM identities or roles.

### Using Excessive Permissions

Avoid giving operational users unrestricted permissions when narrower policies are sufficient.

### Ignoring IaC Ownership

A manual CLI change may be overwritten by the next Terraform or CloudFormation deployment.

### Running Destructive Commands Without Inspection

Do not make:

```bash
aws ec2 terminate-instances ...
```

your first command.

Inspect first.

## Production Configuration Pattern

A practical human workflow can look like:

```text
IAM Identity Center
        |
        v
AWS CLI Profile
        |
        v
STS Identity Verification
        |
        v
Region Verification
        |
        v
EC2 Inspection
        |
        v
Targeted Operation
        |
        v
Post-Change Verification
```

For AWS workloads:

```text
EC2
 |
 v
IAM Instance Profile
 |
 v
Temporary Credentials
 |
 v
AWS APIs
```

For CI/CD:

```text
CI System
 |
 v
OIDC
 |
 v
AWS IAM Role
 |
 v
Temporary Credentials
 |
 v
AWS CLI
```

These patterns minimize the need for long-lived static credentials.

## Key Takeaways

- **Always verify identity, account, region, and target resource before EC2 operations:** `aws sts get-caller-identity` is a critical safety check.
- **Prefer temporary credentials and role-based authentication:** use IAM roles for EC2 workloads and modern federation mechanisms for humans and CI/CD.
- **Use profiles to make environment boundaries explicit:** development, staging, and production should not depend on an ambiguous default configuration.
- **Treat destructive CLI commands as production operations:** inspect resources first, understand ownership and dependencies, then make the smallest safe change.
- **Use the CLI according to the source-of-truth model:** combine it with Infrastructure as Code and CI/CD rather than allowing unmanaged manual changes to become permanent configuration.