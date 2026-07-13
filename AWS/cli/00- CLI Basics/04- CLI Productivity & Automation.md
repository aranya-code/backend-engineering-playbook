# CLI Productivity & Automation

> Learn practical techniques to become more productive with the AWS CLI by leveraging shell features, command generation, automation, and reusable workflows.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Navigate AWS CLI documentation efficiently.
- Use command completion and interactive prompts.
- Save time with aliases and shell functions.
- Redirect and pipe AWS CLI output.
- Generate command skeletons.
- Build reusable automation scripts.
- Follow best practices for scripting with AWS CLI.

---

# Why Productivity Matters

Knowing AWS CLI commands is only part of being productive.

Experienced engineers spend more time:

- Investigating production issues
- Writing automation scripts
- Building CI/CD pipelines
- Managing cloud infrastructure
- Performing repetitive operational tasks

Small improvements in workflow can save hours over the course of a project.

---

# The AWS CLI Help System

One of the most underused features of AWS CLI is its built-in documentation.

Instead of searching online for every command, use the help system.

Display general help:

```bash
aws help
```

Display help for a service:

```bash
aws s3 help
```

Display help for a specific operation:

```bash
aws s3 cp help
```

or

```bash
aws ec2 run-instances help
```

---

## Why Use the Help System?

The help pages include:

- Command syntax
- Required parameters
- Optional parameters
- Examples
- Available global options
- Links to related commands

Using the built-in documentation is often faster than searching the web.

---

# Command Auto-Completion

Typing long AWS CLI commands repeatedly can be tedious.

Most shells support command completion.

Examples:

```text
aws ec2 des<TAB>
```

becomes

```text
aws ec2 describe-
```

Similarly,

```text
aws s3<TAB>
```

lists available S3 operations.

Auto-completion reduces typing errors and helps discover available commands.

---

## Benefits

- Faster command entry
- Fewer typing mistakes
- Easier discovery of commands
- Better learning experience

---

# Interactive Auto Prompt

AWS CLI Version 2 introduced interactive prompting.

Launch it using:

```bash
aws --cli-auto-prompt
```

Or use it with a specific command:

```bash
aws ec2 run-instances \
    --cli-auto-prompt
```

The CLI prompts for required parameters interactively.

Example:

```text
AMI ID:

Instance Type:

Key Pair:

Subnet:

Security Group:
```

This is especially useful when learning unfamiliar AWS services.

---

# Command History

Every shell maintains a command history.

Linux/macOS:

```bash
history
```

Search history:

```bash
history | grep aws
```

PowerShell:

```powershell
Get-History
```

Searching your command history is often faster than rewriting complex commands from memory.

---

# Reusing Previous Commands

Linux/macOS:

Execute the previous command again:

```bash
!!
```

Reuse the last argument from the previous command:

```bash
!$
```

Example:

```bash
mkdir backups

cd !$
```

Result:

```bash
cd backups
```

Although these are shell features rather than AWS CLI features, they greatly improve day-to-day productivity.

---

# Using Aliases

Frequently used commands can be shortened with aliases.

Example:

```bash
alias awsp='aws --profile production'
```

Now instead of:

```bash
aws s3 ls \
--profile production
```

you can simply run:

```bash
awsp s3 ls
```

---

## Another Example

Development profile:

```bash
alias awsd='aws --profile development'
```

Examples:

```bash
awsd ec2 describe-instances
```

```bash
awsp s3 ls
```

Aliases reduce typing and help prevent mistakes when switching between environments.

---

# Shell Functions

Aliases are useful for simple commands.

For more advanced workflows, use shell functions.

Example:

```bash
awswho() {
    aws sts get-caller-identity
}
```

Now execute:

```bash
awswho
```

Instead of typing:

```bash
aws sts get-caller-identity
```

This makes common operational tasks quicker and easier.

---

# Productivity Tips

- Learn the built-in help system before searching externally.
- Enable auto-completion in your shell.
- Use `--cli-auto-prompt` while learning new services.
- Create aliases for frequently used profiles.
- Use shell functions for repetitive operational tasks.
- Search your command history instead of retyping complex commands.

---

# Architecture Note

AWS CLI itself is intentionally lightweight.

Many productivity improvements come from combining the CLI with shell features such as:

- Bash
- Zsh
- PowerShell
- Fish

Mastering your shell is just as important as mastering AWS CLI.

---

# Interview Note

### Question

How do you improve your productivity when working with AWS CLI daily?

### Sample Answer

I rely heavily on the built-in help system, shell history, aliases for different AWS profiles, auto-completion, and `--cli-auto-prompt` when exploring unfamiliar services. For repetitive operational tasks, I create shell functions and small automation scripts to reduce manual effort and improve consistency.

---

# Key Takeaways

- AWS CLI includes an extensive built-in help system.
- Auto-completion reduces typing and improves command discovery.
- Shell history is valuable for reusing complex commands.
- Aliases and shell functions simplify repetitive tasks.
- Combining AWS CLI with shell features significantly improves productivity.

---

# Working with Input and Output

One of the greatest strengths of the AWS CLI is that it behaves like any other command-line application.

This means you can combine it with standard shell features such as:

- Pipes (`|`)
- Output redirection (`>`)
- Input redirection (`<`)
- Command substitution (`$()`)
- Variables
- Files

These features make the AWS CLI an excellent tool for automation.

---

# Redirecting Output

Instead of displaying command output on the terminal, you can save it to a file.

Syntax:

```bash
command > filename
```

Example:

```bash
aws s3 ls > buckets.txt
```

The output is written to:

```
buckets.txt
```

instead of the terminal.

---

## Overwriting vs Appending

Overwrite an existing file:

```bash
aws iam list-users > users.txt
```

Append to an existing file:

```bash
aws iam list-users >> users.txt
```

The `>>` operator preserves the existing contents.

---

# Redirecting Error Output

Sometimes you only want to capture errors.

Example:

```bash
aws s3 ls 2> error.log
```

Only error messages are written to:

```
error.log
```

Standard output still appears on the terminal.

---

## Redirect Everything

Capture both standard output and error output.

```bash
aws s3 ls > output.log 2>&1
```

Useful for:

- Automation
- CI/CD
- Debugging
- Scheduled jobs

---

# Piping Output

Instead of saving output to a file, you can send it directly to another command.

Syntax:

```bash
command1 | command2
```

Example:

```bash
aws s3 ls | grep backup
```

This displays only buckets containing:

```
backup
```

---

# Searching Results

Example:

```bash
aws iam list-users \
--output text | grep admin
```

Only matching users are displayed.

---

Windows PowerShell:

```powershell
aws iam list-users |
Select-String admin
```

---

# Counting Results

Count the number of buckets:

```bash
aws s3 ls | wc -l
```

Count Lambda functions:

```bash
aws lambda list-functions \
--query "Functions[*].FunctionName" \
--output text | wc -w
```

---

# Sorting Results

Sort bucket names:

```bash
aws s3 ls | sort
```

Reverse sort:

```bash
aws s3 ls | sort -r
```

---

# Saving JSON Output

Many engineers save API responses for later analysis.

Example:

```bash
aws ec2 describe-instances \
--output json > instances.json
```

Advantages:

- Easier debugging
- Offline analysis
- Version comparison
- Documentation

---

# Reading JSON from Files

Several AWS CLI commands support reading parameters from files.

Example:

```bash
aws iam create-policy \
--policy-document file://policy.json
```

Instead of embedding JSON directly inside the command, AWS CLI reads the file.

Example:

```
policy.json
```

```json
{
    "Version":"2012-10-17",
    "Statement":[]
}
```

Using files keeps commands shorter and easier to maintain.

---

# Reading Large Configuration Files

Examples include:

```bash
aws cloudformation deploy \
--template-file template.yaml
```

```bash
aws cloudformation validate-template \
--template-body file://template.yaml
```

Large infrastructure templates should always be stored in files rather than embedded in commands.

---

# Using Command Substitution

Sometimes one AWS CLI command produces input for another.

Example:

```bash
INSTANCE_ID=$(aws ec2 describe-instances \
--query "Reservations[0].Instances[0].InstanceId" \
--output text)
```

Now stop the instance:

```bash
aws ec2 stop-instances \
--instance-ids $INSTANCE_ID
```

This pattern is extremely common in automation scripts.

---

# Working with Variables

Example:

```bash
BUCKET=my-production-backups
```

Upload a file:

```bash
aws s3 cp backup.zip s3://$BUCKET
```

Variables improve readability and simplify maintenance.

---

# Generating Command Skeletons

AWS CLI can generate JSON templates automatically.

Example:

```bash
aws ec2 run-instances \
--generate-cli-skeleton
```

Example output:

```json
{
    "ImageId":"",
    "InstanceType":"",
    "KeyName":""
}
```

This is useful when learning new services or creating complex commands.

---

# Generating Input Templates

```bash
aws lambda create-function \
--generate-cli-skeleton input
```

AWS CLI produces a complete JSON template.

Populate the values and execute:

```bash
aws lambda create-function \
--cli-input-json file://function.json
```

This approach is much cleaner than specifying dozens of command-line parameters.

---

# Generating Output Skeletons

```bash
aws ec2 run-instances \
--generate-cli-skeleton output
```

Displays the expected response format without making an API call.

Useful when developing automation.

---

# Real-World Workflow

Suppose your deployment pipeline needs to:

1. Retrieve the latest EC2 instance ID.
2. Save it into a variable.
3. Stop the instance.
4. Store the response in a log file.

Example:

```bash
INSTANCE_ID=$(aws ec2 describe-instances \
--query "Reservations[0].Instances[0].InstanceId" \
--output text)

aws ec2 stop-instances \
--instance-ids $INSTANCE_ID \
> deployment.log
```

This pattern appears frequently in deployment scripts and maintenance automation.

---

# Production Tips

- Store large JSON documents in files.
- Redirect command output to log files during automation.
- Use pipes to avoid unnecessary temporary files.
- Prefer command substitution over manually copying values.
- Use variables instead of repeating resource names.
- Generate CLI skeletons when working with unfamiliar services.

---

# Architecture Note

AWS CLI integrates naturally with operating system tools.

```text
AWS CLI
    │
    ▼
JSON Output
    │
    ├────────► File
    │
    ├────────► Variable
    │
    ├────────► Pipe
    │
    └────────► Another Command
```

This composability is one of the reasons the AWS CLI is widely used for automation.

---

# Interview Note

### Question

Why would you use `--generate-cli-skeleton`?

### Sample Answer

`--generate-cli-skeleton` produces a JSON template for a command's input or output. It is useful for learning complex commands, documenting request structures, validating automation, and creating reusable input files instead of specifying numerous command-line arguments.

---

# Key Takeaways

- Redirect output using `>` or `>>`.
- Pipe output to other commands using `|`.
- Store API responses in JSON files.
- Read configuration from files using the `file://` prefix.
- Use command substitution to chain AWS CLI commands.
- Generate command skeletons to simplify complex API operations.

# Shell Scripting with AWS CLI

AWS CLI becomes significantly more powerful when combined with shell scripting.

Instead of manually executing commands one at a time, scripts allow you to automate repetitive operational tasks.

Common examples include:

- Daily backups
- Infrastructure validation
- Resource cleanup
- Deployment automation
- Monitoring
- Health checks
- Incident response

Automation reduces manual effort and improves consistency.

---

# Creating Your First AWS CLI Script

Linux/macOS

```bash
#!/bin/bash

echo "Listing S3 Buckets..."

aws s3 ls
```

Save the file:

```text
list-buckets.sh
```

Make it executable:

```bash
chmod +x list-buckets.sh
```

Execute:

```bash
./list-buckets.sh
```

---

# Using Variables

Instead of hardcoding values:

```bash
aws s3 cp backup.zip s3://company-backup
```

Use variables:

```bash
#!/bin/bash

BUCKET=company-backup
FILE=backup.zip

aws s3 cp $FILE s3://$BUCKET
```

Advantages:

- Easier maintenance
- Better readability
- Reusable scripts

---

# Accepting User Input

Scripts can accept parameters.

Example:

```bash
#!/bin/bash

INSTANCE_ID=$1

aws ec2 stop-instances \
--instance-ids $INSTANCE_ID
```

Run:

```bash
./stop-instance.sh i-0123456789abcdef0
```

The script becomes reusable for any EC2 instance.

---

# Conditional Execution

Example:

```bash
if aws s3 ls s3://company-backup
then
    echo "Bucket exists."
else
    echo "Bucket not found."
fi
```

This allows scripts to react to AWS CLI command success or failure.

---

# Looping Through Resources

Example:

```bash
for bucket in $(aws s3api list-buckets \
--query "Buckets[*].Name" \
--output text)
do
    echo $bucket
done
```

Result:

```text
company-backups

application-logs

images
```

Loops are useful when performing bulk operations.

---

# Automating EC2 Operations

Example:

Retrieve every running instance.

```bash
for instance in $(aws ec2 describe-instances \
--query "Reservations[].Instances[].InstanceId" \
--output text)
do
    echo $instance
done
```

You could easily extend the script to:

- Stop instances
- Tag instances
- Create snapshots
- Generate reports

---

# Error Handling

Always verify command success.

Example:

```bash
aws s3 cp backup.zip s3://company-backup

if [ $? -eq 0 ]
then
    echo "Upload successful."
else
    echo "Upload failed."
fi
```

Ignoring errors can lead to unreliable automation.

---

# Logging

Production scripts should always log important actions.

Example:

```bash
LOGFILE=deployment.log

echo "Deployment started" >> $LOGFILE

aws s3 sync build/ s3://frontend-assets >> $LOGFILE 2>&1

echo "Deployment completed" >> $LOGFILE
```

Logging simplifies troubleshooting and auditing.

---

# Exit Codes

AWS CLI returns standard shell exit codes.

| Exit Code | Meaning |
|-----------|---------|
| `0` | Success |
| Non-zero | Failure |

Example:

```bash
aws cloudformation validate-template \
--template-body file://template.yaml

echo $?
```

A value of `0` indicates that the command completed successfully.

---

# Building Reusable Functions

Instead of repeating commands, define reusable functions.

Example:

```bash
aws_identity() {
    aws sts get-caller-identity
}
```

Use:

```bash
aws_identity
```

Functions improve readability and reduce duplication.

---

# Automation Best Practices

When writing AWS CLI scripts:

- Use variables instead of hardcoded values.
- Validate user input.
- Check exit codes.
- Log important actions.
- Avoid interactive prompts.
- Specify Regions explicitly.
- Specify Profiles explicitly.
- Use `--output json` for automation.
- Filter responses using `--query`.

---

# Production Workflow

## Scenario

A deployment pipeline needs to:

1. Verify the active AWS account.
2. Upload build artifacts.
3. Confirm the upload completed.
4. Record the deployment log.

Example:

```bash
#!/bin/bash

LOGFILE=deploy.log
BUCKET=frontend-production

echo "Checking identity..." | tee -a $LOGFILE

aws sts get-caller-identity | tee -a $LOGFILE

echo "Uploading artifacts..." | tee -a $LOGFILE

aws s3 sync build/ s3://$BUCKET \
--delete \
>> $LOGFILE 2>&1

if [ $? -eq 0 ]
then
    echo "Deployment successful." | tee -a $LOGFILE
else
    echo "Deployment failed." | tee -a $LOGFILE
    exit 1
fi
```

This simple workflow demonstrates several best practices:

- Identity verification
- Logging
- Exit code validation
- Reusable variables
- Automated deployment

---

# Common Mistakes

## Hardcoding Credentials

Never store credentials directly inside scripts.

Incorrect:

```bash
AWS_ACCESS_KEY_ID=AKIAxxxxxxxx
```

Instead:

- Use IAM Roles.
- Use Named Profiles.
- Use AWS IAM Identity Center (SSO).
- Use environment variables managed by your CI/CD platform.

---

## Ignoring Exit Codes

Avoid:

```bash
aws s3 sync build/ s3://production
echo "Deployment completed."
```

If the upload fails, the script still reports success.

Always validate the exit code.

---

## Missing Region

Avoid relying on the default Region.

Instead:

```bash
aws s3 sync build/ s3://production \
--region ap-south-1
```

This makes automation more predictable.

---

# Architecture Note

Professional AWS automation typically follows this flow:

```text
Shell Script
      │
      ▼
AWS CLI
      │
      ▼
AWS APIs
      │
      ▼
Cloud Resources
      │
      ▼
Logs & Monitoring
```

The AWS CLI acts as the bridge between automation scripts and AWS services.

---

# Interview Note

### Question

How do you make AWS CLI automation reliable?

### Sample Answer

Reliable automation starts with secure authentication, explicit Regions and Profiles, proper error handling, structured logging, and validation of command exit codes. I also use `--query` to simplify parsing, avoid hardcoded credentials by using IAM Roles or temporary credentials, and ensure every script can be rerun safely whenever possible.

---

# Chapter Summary

In this chapter, you learned:

- Using the AWS CLI help system
- Auto-completion and interactive prompts
- Aliases and shell functions
- Redirecting and piping output
- Working with files
- Command skeleton generation
- Shell scripting with AWS CLI
- Logging and error handling
- Production automation techniques

These skills transform the AWS CLI from a simple command-line tool into a powerful automation platform for cloud operations.

---


---

# Senior-Level Deep Dives

---

## Production-Grade Bash Scripts — Defensive Patterns

Basic scripts work in development. Production scripts need robustness.

### Strict Mode

Always start scripts with:

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
```

- `set -e`: exit immediately on non-zero exit code
- `set -u`: treat unset variables as errors
- `set -o pipefail`: a pipe fails if any command in it fails
- `IFS=$'\n\t'`: prevents word splitting bugs with spaces in filenames

### Retry Logic for Transient AWS Errors

AWS API calls occasionally fail with throttling or transient errors. Production scripts retry:

```bash
aws_with_retry() {
  local max_attempts=5
  local attempt=0
  local delay=2

  while (( attempt < max_attempts )); do
    if "$@"; then
      return 0
    fi
    attempt=$(( attempt + 1 ))
    echo "Attempt $attempt failed. Retrying in ${delay}s..." >&2
    sleep $delay
    delay=$(( delay * 2 ))  # exponential backoff
  done

  echo "All $max_attempts attempts failed." >&2
  return 1
}

# Usage
aws_with_retry aws s3 sync ./build s3://production-assets --region ap-south-1
```

### Validate Required Tools

```bash
check_dependencies() {
  local tools=("aws" "jq" "curl")
  for tool in "${tools[@]}"; do
    command -v "$tool" &>/dev/null || { echo "$tool not found"; exit 1; }
  done
}
```

### Verify AWS Authentication Before Starting

```bash
verify_auth() {
  local profile="${1:-default}"
  local identity
  identity=$(aws sts get-caller-identity --profile "$profile" 2>&1) || {
    echo "Authentication failed for profile: $profile"
    echo "$identity"
    exit 1
  }
  echo "Authenticated as: $(echo "$identity" | jq -r .Arn)"
}
```

### Structured Logging

```bash
LOG_FILE="deploy-$(date +%Y%m%d-%H%M%S).log"

log() {
  local level="$1"
  shift
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$level] $*" | tee -a "$LOG_FILE"
}

log INFO "Starting deployment"
log ERROR "Upload failed"
```

### Cleanup on Exit

```bash
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT
```

---

## CI/CD Integration Patterns

### GitHub Actions with OIDC (No Long-Lived Keys)

```yaml
# .github/workflows/deploy.yml
permissions:
  id-token: write  # required for OIDC
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsDeployRole
          aws-region: ap-south-1

      - name: Verify identity
        run: aws sts get-caller-identity

      - name: Deploy
        run: aws s3 sync ./build s3://production-frontend --delete
```

The IAM role's trust policy must allow GitHub's OIDC provider:
```json
{
  "Principal": { "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com" },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
    "StringLike": { "token.actions.githubusercontent.com:sub": "repo:myorg/myrepo:*" }
  }
}
```

### Parallel Multi-Region Operations

Using background processes for concurrent operations:

```bash
REGIONS=("ap-south-1" "us-east-1" "eu-west-1")
PIDS=()

for region in "${REGIONS[@]}"; do
  (
    aws ec2 describe-instances \
      --region "$region" \
      --query "Reservations[].Instances[].[InstanceId,State.Name]" \
      --output text | awk -v r="$region" '{print r, $0}'
  ) &
  PIDS+=($!)
done

# Wait for all and check status
for pid in "${PIDS[@]}"; do
  wait "$pid" || echo "Region job $pid failed"
done
```

### AWS CLI in Docker

```dockerfile
FROM public.ecr.aws/amazonlinux/amazonlinux:2023

RUN yum install -y unzip curl && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip aws/

# In ECS/EKS — credentials come from task role, no static creds needed
ENTRYPOINT ["aws"]
```

---

## AWS CLI Configuration for Power Users

### `~/.aws/config` — Advanced Patterns

```ini
# Assume a role from a base profile
[profile production]
role_arn = arn:aws:iam::987654321098:role/ProdDeployRole
source_profile = base-account
region = ap-south-1
mfa_serial = arn:aws:iam::123456789012:mfa/john
duration_seconds = 14400

# Assume a role with external ID (for 3rd party access)
[profile partner-access]
role_arn = arn:aws:iam::111222333444:role/PartnerRole
external_id = unique-external-id-12345
source_profile = base-account

# SSO profile
[profile dev-sso]
sso_session = company
sso_account_id = 123456789012
sso_role_name = DeveloperAccess
region = ap-south-1

[sso-session company]
sso_start_url = https://company.awsapps.com/start
sso_region = us-east-1
sso_registration_scopes = sso:account:access
```

### Environment-Based Profile Switching

```bash
# In .zshrc or .bashrc
awsprofile() {
  export AWS_PROFILE="$1"
  aws sts get-caller-identity
  echo "Switched to profile: $1"
}

# Usage: awsprofile production
# Usage: awsprofile development
```

### Disabling the Pager Globally

Instead of `--no-cli-pager` on every command:

```ini
# ~/.aws/config
[default]
cli_pager =
```

An empty `cli_pager` disables the pager globally.

---

## `credential_process` — External Credential Helpers

The `credential_process` config key lets you use any script or binary to supply credentials:

```ini
[profile vault-backed]
credential_process = /usr/local/bin/vault-aws-creds --role deploy
region = ap-south-1
```

The script must output JSON matching:
```json
{
  "Version": 1,
  "AccessKeyId": "...",
  "SecretAccessKey": "...",
  "SessionToken": "...",
  "Expiration": "2026-07-12T15:00:00Z"
}
```

This is the integration point for HashiCorp Vault, 1Password CLI, and custom HSM-backed credential systems.

---

## Senior Interview Questions — Automation

**Q: How do you ensure AWS CLI automation is safe to run multiple times (idempotent)?**

- Use commands that apply desired state rather than imperative actions: `aws s3 sync` (not repeated `cp`), `aws cloudformation deploy` (not `create-stack`).
- For operations without native idempotency, check current state before acting: describe the resource, compare to desired state, apply only if needed.
- Use `--no-clobber` or `--dryrun` flags where available.
- Use `aws cloudformation deploy` with change sets — it's a no-op if nothing changed.

---

**Q: A deployment script takes 45 minutes to sync to S3 in a CI/CD pipeline. How would you optimize it?**

1. Add `--exclude` patterns to skip unchanged asset types
2. Use `--delete` to clean stale files in one pass
3. Enable `--size-only` or `--exact-timestamps` to avoid re-hashing every file
4. Use `--cache-control` headers for CDN optimization
5. Consider parallelism with `--storage-class` selection per file type
6. If the bucket is in a different region, enable Transfer Acceleration:
```bash
aws s3 sync ./build s3://frontend-assets \
  --region us-east-1 \
  --sse AES256 \
  --cache-control "max-age=31536000" \
  --size-only
```

---

**Q: How do you handle AWS API throttling in a script processing 500 resources?**

1. Use exponential backoff with jitter (not fixed sleep)
2. Reduce `--page-size` to reduce per-call load
3. Parallelize across resources with rate limiting (e.g., `xargs -P 10`)
4. Use `--no-paginate` carefully — it issues sequential paginated calls
5. Consider batching: many AWS APIs accept lists (e.g., `--instance-ids` accepts up to 1000)
6. For sustained high throughput, request a quota increase via Service Quotas

---
