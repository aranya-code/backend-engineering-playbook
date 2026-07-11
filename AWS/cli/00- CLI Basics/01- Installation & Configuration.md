# Installation & Configuration

> Learn how to install, verify, and configure the AWS Command Line Interface (AWS CLI) for professional software development and cloud administration.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand what AWS CLI is and how it works.
- Explain why AWS CLI is an essential tool for cloud engineers.
- Differentiate between AWS CLI Version 1 and Version 2.
- Understand the AWS CLI architecture.
- Install AWS CLI on Windows, macOS, and Linux.
- Verify that AWS CLI has been installed successfully.

---

# What is AWS CLI?

The **AWS Command Line Interface (AWS CLI)** is a unified command-line tool that enables developers and administrators to manage AWS services directly from a terminal.

Instead of interacting with the AWS Management Console, you can execute commands that invoke AWS APIs.

For example:

```bash
aws ec2 describe-instances
```

retrieves information about EC2 instances.

Similarly,

```bash
aws s3 ls
```

lists all S3 buckets associated with your AWS account.

AWS CLI supports hundreds of AWS services including:

- Amazon EC2
- Amazon S3
- AWS Lambda
- Amazon ECS
- Amazon ECR
- Amazon RDS
- Amazon DynamoDB
- Amazon Route 53
- AWS CloudFormation
- Amazon CloudWatch
- AWS IAM
- Amazon SNS
- Amazon SQS

and many more.

---

# Why Learn AWS CLI?

Although the AWS Management Console is convenient for learning AWS, real-world engineering teams rely heavily on the AWS CLI for automation and operational tasks.

Common use cases include:

- Infrastructure provisioning
- Continuous Integration and Continuous Deployment (CI/CD)
- Infrastructure as Code (IaC)
- Bulk resource management
- Deployment automation
- Production troubleshooting
- Disaster recovery
- Scheduled maintenance
- Resource auditing

Using the CLI enables engineers to automate repetitive tasks, reduce manual effort, and maintain consistent deployment processes.

---

# Benefits of AWS CLI

## Automation

Commands can be incorporated into shell scripts, PowerShell scripts, GitHub Actions, Jenkins pipelines, GitLab CI, and other automation platforms.

Example:

```bash
aws s3 sync ./backup s3://company-backup
```

---

## Speed

Executing a command is often significantly faster than navigating multiple pages within the AWS Console.

Example:

```bash
aws ec2 stop-instances \
    --instance-ids i-0123456789abcdef0
```

---

## Repeatability

Every command can be stored in version control and executed repeatedly with consistent results.

This is particularly useful for:

- Production deployments
- Infrastructure provisioning
- Disaster recovery
- Environment setup

---

## Scripting

AWS CLI integrates seamlessly with:

- Bash
- PowerShell
- Python
- Shell scripts
- GitHub Actions
- Jenkins
- GitLab CI/CD
- AWS CodeBuild

Example:

```bash
INSTANCE_ID=$(aws ec2 describe-instances \
--query "Reservations[0].Instances[0].InstanceId" \
--output text)
```

---

## Production Troubleshooting

AWS CLI is one of the fastest ways to inspect production infrastructure.

Example:

```bash
aws logs tail \
/aws/lambda/my-function \
--follow
```

or

```bash
aws ecs describe-services
```

---

# AWS Console vs AWS CLI

| Feature | AWS Console | AWS CLI |
|----------|-------------|----------|
| Learning | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Automation | ❌ | ✅ |
| Scripting | ❌ | ✅ |
| CI/CD Integration | ❌ | ✅ |
| Bulk Operations | Limited | Excellent |
| Infrastructure Management | Manual | Automated |
| Speed | Moderate | Very Fast |
| Repeatability | Poor | Excellent |

The AWS Console is ideal for learning and visual exploration, while the AWS CLI is preferred for operational tasks, automation, and production environments.

---

# How AWS CLI Works

AWS CLI acts as a client that communicates with AWS services by making authenticated API requests.

The general workflow is:

```text
+----------------------+
|     Developer        |
+----------+-----------+
           |
           v
+----------------------+
|  Terminal / Shell    |
+----------+-----------+
           |
           v
+----------------------+
|      AWS CLI         |
+----------+-----------+
           |
 HTTPS Request (Signed)
           |
           v
+----------------------+
|      AWS APIs        |
+----------+-----------+
           |
           v
+----------------------+
|    AWS Services      |
+----------------------+
```

When you execute a command such as:

```bash
aws ec2 describe-instances
```

the AWS CLI:

1. Reads your credentials.
2. Signs the request.
3. Sends an HTTPS request to the EC2 API.
4. Receives the JSON response.
5. Formats the output for your terminal.

Understanding this workflow makes it easier to troubleshoot authentication issues and API errors.

---

# AWS CLI Version 1 vs Version 2

AWS currently provides two major versions of the CLI.

| Feature | Version 1 | Version 2 |
|----------|-----------|-----------|
| Current Recommendation | ❌ | ✅ |
| Self-contained Installer | ❌ | ✅ |
| AWS IAM Identity Center (SSO) | Limited | Full Support |
| Interactive Auto Prompt | ❌ | ✅ |
| Performance | Good | Better |
| Security Improvements | Basic | Enhanced |
| Cross-platform Installer | Limited | Yes |

### Recommendation

Always install **AWS CLI Version 2** for new projects unless a legacy environment specifically requires Version 1.

---

# System Requirements

AWS CLI Version 2 supports the following operating systems:

### Windows

- Windows 10
- Windows 11
- Windows Server

---

### macOS

- Recent macOS versions
- Homebrew (recommended)

---

### Linux

Supported distributions include:

- Ubuntu
- Debian
- Amazon Linux
- CentOS
- Fedora
- Red Hat Enterprise Linux (RHEL)

Most modern Linux distributions support AWS CLI Version 2.

---

# Choosing an Installation Method

| Platform | Recommended Method |
|----------|--------------------|
| Windows | Official MSI Installer |
| macOS | Homebrew |
| Ubuntu/Debian | Official Installer |
| Amazon Linux | Official Installer |
| CI/CD Pipelines | Official ZIP Installer |
| Docker Images | Package during image build |

Choosing the recommended installation method simplifies updates and ensures compatibility with AWS CLI Version 2.

---

# Installing AWS CLI

AWS CLI Version 2 is available for Windows, macOS, and Linux. AWS recommends using **Version 2** for all new projects because it includes enhanced security, better performance, support for AWS IAM Identity Center (formerly AWS SSO), and a simplified installation experience.

> **Production Recommendation**
>
> Always install **AWS CLI Version 2** unless you're maintaining a legacy environment that explicitly depends on Version 1.

---

# Installing on Windows

The simplest way to install AWS CLI on Windows is by using the official MSI installer.

## Step 1: Download the Installer

Download the latest AWS CLI Version 2 installer from the official AWS documentation.

The installer automatically includes:

- AWS CLI executable
- Required runtime dependencies
- PATH configuration

---

## Step 2: Run the Installer

Launch the downloaded MSI installer.

The setup wizard will:

- Install AWS CLI
- Add the executable to the system PATH
- Make the `aws` command available globally

No additional configuration is required.

---

## Step 3: Restart Your Terminal

If Command Prompt, PowerShell, or Windows Terminal was already open, close and reopen it.

This ensures the updated PATH is loaded.

---

## Step 4: Verify Installation

Run:

```bash
aws --version
```

Example output:

```text
aws-cli/2.27.41 Python/3.13.3 Windows/11 exe/AMD64
```

Your version number may differ.

---

# Installing on macOS

The recommended installation method is **Homebrew**.

## Install

```bash
brew install awscli
```

---

## Verify

```bash
aws --version
```

Example:

```text
aws-cli/2.x.x
```

---

## Upgrade

```bash
brew upgrade awscli
```

---

## Verify Installation Path

```bash
which aws
```

Example:

```text
/usr/local/bin/aws
```

or

```text
/opt/homebrew/bin/aws
```

depending on your Mac architecture.

---

# Installing on Linux

AWS provides an official ZIP installer for Linux.

Although some distributions provide packages through their package managers, AWS recommends using the official installer to receive the latest version.

---

## Step 1: Download

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
-o "awscliv2.zip"
```

For ARM-based systems, download the ARM64 package instead.

---

## Step 2: Extract

```bash
unzip awscliv2.zip
```

This creates an `aws/` directory containing the installer.

---

## Step 3: Install

```bash
sudo ./aws/install
```

Expected output:

```text
You can now run:
/usr/local/bin/aws --version
```

---

## Step 4: Verify

```bash
aws --version
```

---

# Updating AWS CLI

Keeping AWS CLI updated ensures you receive:

- New AWS service support
- Bug fixes
- Security patches
- Performance improvements

---

## Windows

Download and run the latest installer.

The existing installation will be upgraded automatically.

---

## macOS

```bash
brew upgrade awscli
```

---

## Linux

```bash
sudo ./aws/install --update
```

---

# Uninstalling AWS CLI

Occasionally you may need to remove an outdated installation before upgrading.

---

## Windows

Navigate to:

```
Settings
→ Apps
→ Installed Apps
→ AWS Command Line Interface
→ Uninstall
```

---

## macOS

```bash
brew uninstall awscli
```

---

## Linux

Remove the installation directory:

```bash
sudo rm -rf /usr/local/aws-cli
```

Remove the executable:

```bash
sudo rm -f /usr/local/bin/aws
```

---

# Verifying the Installation

Installing AWS CLI successfully does not necessarily mean your shell can execute it.

Always verify the installation.

---

## Check Version

```bash
aws --version
```

Example:

```text
aws-cli/2.27.41 Python/3.13.3 Linux/6.8 exe/x86_64
```

---

## Locate the Executable

### Windows

```powershell
where aws
```

Example:

```text
C:\Program Files\Amazon\AWSCLIV2\aws.exe
```

---

### Linux

```bash
which aws
```

Example:

```text
/usr/local/bin/aws
```

---

### macOS

```bash
which aws
```

Example:

```text
/opt/homebrew/bin/aws
```

---

## Display Help

```bash
aws help
```

This command opens the AWS CLI documentation.

---

## Service-Specific Help

Display help for a specific service:

```bash
aws s3 help
```

or

```bash
aws ec2 help
```

This is one of the quickest ways to explore supported commands and options.

---

# Verify PATH Configuration

If the `aws` command is not recognized, check whether the installation directory is present in your system PATH.

### Windows

PowerShell:

```powershell
echo $Env:Path
```

Command Prompt:

```cmd
echo %PATH%
```

---

### Linux / macOS

```bash
echo $PATH
```

Ensure the directory containing the `aws` executable appears in the output.

---

# Installation Checklist

Before proceeding to configuration, verify the following:

- ✅ AWS CLI Version 2 is installed.
- ✅ `aws --version` executes successfully.
- ✅ `aws help` opens the documentation.
- ✅ `which aws` or `where aws` locates the executable.
- ✅ PATH is configured correctly.
- ✅ No older AWS CLI installation conflicts with Version 2.

---

## Production Tip

Before configuring credentials, verify exactly which AWS CLI executable your terminal is using.

On systems with multiple Python environments or package managers, it's possible to have multiple AWS CLI installations. This can lead to inconsistent behavior and version mismatches.

Using `which aws` (Linux/macOS) or `where aws` (Windows) early can save significant debugging time later.

---

# Configuring AWS CLI

Installing the AWS CLI only makes the `aws` command available on your system. Before you can interact with AWS services, the CLI must know **who you are**, **which AWS account to access**, and **which Region to use**.

This process is called **configuration**.

---

# What Happens During Configuration?

When you configure the AWS CLI, it stores information such as:

- AWS Access Key ID
- AWS Secret Access Key
- Default AWS Region
- Default Output Format

The CLI uses these settings to authenticate every request sent to AWS APIs.

Without proper configuration, most commands will fail with authentication errors.

---

# Basic Configuration

The easiest way to configure the CLI is by running:

```bash
aws configure
```

The CLI prompts for four values:

```text
AWS Access Key ID [None]:
AWS Secret Access Key [None]:
Default region name [None]:
Default output format [None]:
```

Example:

```text
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: ****************************************
Default region name [None]: ap-south-1
Default output format [None]: json
```

After entering these values, AWS CLI stores them locally.

---

# Understanding Each Prompt

## AWS Access Key ID

This is the public portion of your AWS credentials.

Example:

```text
AKIAIOSFODNN7EXAMPLE
```

Every authenticated request includes this identifier.

---

## AWS Secret Access Key

The secret access key acts like a password.

Example:

```text
wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

Never share this key publicly.

Never commit it to Git.

Treat it exactly like a password.

---

## Default Region

The Region determines where AWS CLI sends requests when no `--region` option is specified.

Example:

```text
ap-south-1
```

Other common Regions include:

| Region | Code |
|----------|------|
| Mumbai | ap-south-1 |
| Singapore | ap-southeast-1 |
| Tokyo | ap-northeast-1 |
| Frankfurt | eu-central-1 |
| London | eu-west-2 |
| N. Virginia | us-east-1 |
| Ohio | us-east-2 |
| Oregon | us-west-2 |

---

## Default Output Format

AWS CLI supports multiple output formats.

Common choices include:

```text
json
```

```text
table
```

```text
text
```

For automation and scripting, **JSON** is strongly recommended.

---

# Where Does AWS CLI Store Configuration?

AWS CLI stores configuration in two separate files.

## Credentials File

Linux/macOS

```text
~/.aws/credentials
```

Windows

```text
C:\Users\<username>\.aws\credentials
```

Example:

```ini
[default]
aws_access_key_id = AKIAxxxxxxxxxxxxxxxx
aws_secret_access_key = ****************************************
```

---

## Configuration File

Linux/macOS

```text
~/.aws/config
```

Windows

```text
C:\Users\<username>\.aws\config
```

Example:

```ini
[default]
region = ap-south-1
output = json
```

Keeping credentials and configuration separate improves maintainability.

---

# Viewing Current Configuration

Display all configured values:

```bash
aws configure list
```

Example output:

```text
      Name                    Value             Type
      ----                    -----             ----
   profile                  default         manual
access_key     ****************ABCD         shared-credentials-file
secret_key     ****************EFGH         shared-credentials-file
    region             ap-south-1           config-file
```

This command is extremely useful when troubleshooting authentication issues.

---

# Viewing Individual Configuration Values

Display the configured Region:

```bash
aws configure get region
```

Example:

```text
ap-south-1
```

Display the configured output format:

```bash
aws configure get output
```

---

# Updating Configuration

Change only the Region:

```bash
aws configure set region us-east-1
```

Change output format:

```bash
aws configure set output json
```

You don't need to rerun `aws configure` for every small change.

---

# Removing Configuration

Unset a configuration value:

```bash
aws configure set region ""
```

Or manually edit the configuration files.

---

# Testing Your Configuration

A simple way to verify that your credentials work is:

```bash
aws sts get-caller-identity
```

Expected output:

```json
{
    "UserId": "AIDAxxxxxxxxxxxxx",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/backend-user"
}
```

This command does not require special IAM permissions and is commonly used to confirm that the CLI is authenticated correctly.

---

# Common Configuration Errors

## Unable to Locate Credentials

```text
Unable to locate credentials
```

Cause:

- Credentials have not been configured.

Solution:

```bash
aws configure
```

---

## InvalidClientTokenId

```text
The security token included in the request is invalid.
```

Cause:

- Incorrect Access Key
- Incorrect Secret Key

---

## ExpiredToken

```text
ExpiredToken
```

Cause:

Temporary credentials have expired.

Refresh the credentials or obtain a new session token.

---

## SignatureDoesNotMatch

Possible causes:

- Incorrect credentials
- Wrong Region
- System clock is inaccurate

---

# Production Best Practices

- Never use the AWS root account for CLI access.
- Create dedicated IAM users or IAM roles.
- Store credentials securely.
- Rotate access keys regularly.
- Use JSON as the default output format.
- Verify your identity with `aws sts get-caller-identity` before making production changes.
- Avoid editing credential files manually unless necessary.

---

# Configuration Files

After running `aws configure`, the AWS CLI stores your settings locally in two separate files.

Separating credentials from configuration improves security and makes it easier to manage multiple AWS accounts.

---

## Credentials File

The credentials file stores sensitive authentication information.

### Linux/macOS

```text
~/.aws/credentials
```

### Windows

```text
C:\Users\<username>\.aws\credentials
```

Example:

```ini
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

> **Security Warning**
>
> Never commit this file to Git.
>
> Never share your Access Key or Secret Access Key.
>
> Treat the Secret Access Key exactly like a password.

---

## Configuration File

The configuration file stores non-sensitive settings.

Linux/macOS

```text
~/.aws/config
```

Windows

```text
C:\Users\<username>\.aws\config
```

Example:

```ini
[default]
region = ap-south-1
output = json
```

Typical configuration options include:

- Default Region
- Default Output Format
- CLI behavior
- Named profile configuration

---

# Testing Your Configuration

After configuration, it's important to verify that your credentials are valid.

The most common command is:

```bash
aws sts get-caller-identity
```

Example output:

```json
{
  "UserId": "AIDAIEXAMPLE123456789",
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:user/backend-engineer"
}
```

This command confirms:

- Credentials are valid.
- Authentication succeeded.
- Which AWS account is currently active.
- Which IAM identity is being used.

This is one of the first commands experienced AWS engineers run before making changes to production resources.

---

# Verify the Current Configuration

Display the active configuration:

```bash
aws configure list
```

Example output:

```text
      Name                    Value             Type
      ----                    -----             ----
profile                   default           manual
access_key      ****************ABCD        shared-credentials-file
secret_key      ****************EFGH        shared-credentials-file
region                 ap-south-1           config-file
```

This command is particularly useful when troubleshooting configuration problems.

---

## Display the Configured Region

```bash
aws configure get region
```

Output:

```text
ap-south-1
```

---

## Display the Configured Output Format

```bash
aws configure get output
```

Output:

```text
json
```

---

# Updating Configuration

Configuration values can be modified without running the interactive wizard again.

Update the default Region:

```bash
aws configure set region us-east-1
```

Update the default output format:

```bash
aws configure set output table
```

You can update individual settings at any time without affecting the remaining configuration.

---

# Common Installation & Configuration Errors

## Command Not Found

```text
aws: command not found
```

### Cause

- AWS CLI is not installed.
- PATH is not configured correctly.

### Solution

- Verify the installation.
- Restart the terminal.
- Check your PATH configuration.

---

## Unable to Locate Credentials

```text
Unable to locate credentials
```

### Cause

AWS CLI has not been configured.

### Solution

Run:

```bash
aws configure
```

---

## InvalidClientTokenId

```text
The security token included in the request is invalid.
```

### Cause

- Incorrect Access Key
- Incorrect Secret Key
- Credentials belong to another AWS account

---

## ExpiredToken

```text
ExpiredToken
```

### Cause

Temporary credentials have expired.

### Solution

Generate a new session token or refresh the credentials.

---

## SignatureDoesNotMatch

Possible causes:

- Incorrect Secret Access Key
- Wrong AWS Region
- Local system time is incorrect

---

# Best Practices

- Always install **AWS CLI Version 2**.
- Never use the AWS Root Account for daily operations.
- Use an IAM User or IAM Role instead.
- Keep AWS CLI updated.
- Use `json` as the default output format.
- Verify your identity with `aws sts get-caller-identity` before making production changes.
- Avoid manually editing credential files unless necessary.
- Store credentials securely.
- Rotate access keys regularly.
- Never expose credentials in screenshots, code snippets, or Git repositories.

---

# Key Takeaways

By completing this chapter, you have learned how to:

- Install AWS CLI Version 2.
- Verify a successful installation.
- Configure AWS CLI.
- Understand where configuration data is stored.
- Test your authentication.
- Update CLI settings.
- Troubleshoot common installation and configuration issues.
- Follow production-ready installation best practices.

---
