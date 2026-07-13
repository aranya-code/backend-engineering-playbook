# Authentication & Credentials

> Learn how AWS CLI authenticates requests, manages credentials securely, and supports multiple authentication mechanisms for production environments.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand how AWS CLI authenticates requests.
- Differentiate between authentication and authorization.
- Explain the role of IAM in AWS CLI.
- Understand Access Keys and Secret Access Keys.
- Identify where credentials are stored.
- Understand temporary credentials.
- Learn how AWS signs every API request.
- Build a solid foundation before working with named profiles and IAM roles.

---

# Why Authentication Matters

Every AWS CLI command communicates directly with an AWS service.

For example:

```bash
aws s3 ls
```

or

```bash
aws ec2 describe-instances
```

Although these commands appear simple, AWS does **not** execute them immediately.

Before processing the request, AWS must answer two important questions:

1. **Who is making this request?**
2. **Is this identity allowed to perform the requested action?**

These two questions form the foundation of AWS security.

---

# Authentication vs Authorization

These terms are often confused, but they represent different concepts.

| Authentication | Authorization |
|---------------|---------------|
| Verifies your identity | Determines what you are allowed to do |
| "Who are you?" | "What can you access?" |
| Uses credentials | Uses IAM policies |
| Happens first | Happens after authentication |

Think of it like entering an office building.

### Authentication

The security guard checks your ID card.

This confirms **who you are**.

### Authorization

After verifying your identity, your access card determines which rooms you can enter.

This defines **what you are allowed to access**.

AWS follows the same process.

---

# How AWS CLI Authenticates a Request

Consider the following command:

```bash
aws ec2 describe-instances
```

Internally, AWS CLI performs several steps before the request reaches Amazon EC2.

```text
Developer
    │
    ▼
AWS CLI Command
    │
    ▼
Read Credentials
    │
    ▼
Create Signed HTTPS Request
    │
    ▼
AWS STS / IAM Authentication
    │
    ▼
IAM Policy Evaluation
    │
    ▼
Amazon EC2 API
    │
    ▼
Response Returned
```

Every request is authenticated before AWS evaluates permissions.

---

# Understanding AWS Credentials

AWS CLI identifies you using credentials.

A standard set of long-term credentials consists of:

- Access Key ID
- Secret Access Key

Example:

```text
Access Key ID:
AKIAIOSFODNN7EXAMPLE

Secret Access Key:
wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

These two values uniquely identify an IAM identity and allow AWS CLI to sign requests.

> **Important**
>
> The Secret Access Key should never be shared, emailed, or committed to source control.

---

# Access Key ID

The Access Key ID is similar to a username.

Example:

```text
AKIAIOSFODNN7EXAMPLE
```

Characteristics:

- Public identifier
- Included with every signed request
- Associated with an IAM User
- Can be rotated
- Cannot be used alone

Think of it as your username when logging into an application.

---

# Secret Access Key

The Secret Access Key is similar to a password.

Example:

```text
wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

Characteristics:

- Secret value
- Used to generate cryptographic signatures
- Never transmitted in plain text
- Visible only when created
- Cannot be recovered after creation

If the Secret Access Key is lost, a new one must be generated.

---

# How AWS Uses Your Credentials

A common misconception is that AWS sends your Secret Access Key over the internet.

It does **not**.

Instead, AWS CLI uses the Secret Access Key to generate a cryptographic signature using **AWS Signature Version 4 (SigV4)**.

The request is then sent to AWS.

AWS independently calculates the expected signature.

If both signatures match:

- Authentication succeeds.

If they do not match:

- Authentication fails.

This means your Secret Access Key never leaves your computer.

---

# AWS Signature Version 4 (SigV4)

Every AWS CLI request is digitally signed before being transmitted.

The signing process includes information such as:

- HTTP method
- Request URI
- Request headers
- Timestamp
- Request body (when applicable)
- Secret Access Key

The resulting signature proves:

- The request originated from a trusted identity.
- The request was not modified during transmission.
- The request has not expired.

You do **not** need to generate these signatures manually.

AWS CLI handles this process automatically.

---

# Why Time Matters

Because every request contains a timestamp, the local system clock must be accurate.

If your computer's clock differs significantly from AWS servers, authentication may fail.

Typical error:

```text
RequestTimeTooSkewed
```

or

```text
SignatureDoesNotMatch
```

This is why production servers synchronize their clocks using NTP.

---

# Architecture Note

The AWS CLI is **stateless**.

Each command independently:

1. Reads credentials.
2. Reads configuration.
3. Generates a Signature Version 4 signature.
4. Sends an HTTPS request.
5. Waits for the response.

No authentication session is maintained between commands.

---

# Interview Note

One of the most common AWS interview questions is:

> **Does AWS CLI send the Secret Access Key to AWS?**

**Answer:**

No.

The Secret Access Key never leaves your machine.

It is used locally to generate a Signature Version 4 (SigV4) cryptographic signature. AWS recreates the same signature using its stored copy of the key and compares the two values. If they match, the request is authenticated.

---

# Key Takeaways

- Authentication verifies **who** is making the request.
- Authorization determines **what** the identity can do.
- AWS CLI authenticates every request before sending it.
- Access Key IDs identify an IAM identity.
- Secret Access Keys generate cryptographic signatures.
- AWS uses **Signature Version 4 (SigV4)** for request authentication.
- The Secret Access Key never leaves your local machine.

---

# IAM Users vs IAM Roles

AWS provides multiple ways to authenticate requests. The two most common identities are:

- IAM Users
- IAM Roles

Although both can access AWS resources, they are designed for different use cases.

Understanding the difference is critical for building secure cloud applications.

---

# IAM User

An **IAM User** represents a person or application that requires long-term access to an AWS account.

An IAM User can have:

- Username
- Password (for AWS Console)
- Access Keys (for AWS CLI and SDKs)
- Attached IAM Policies

Example:

```text
AWS Account
│
├── IAM User
│      ├── Username
│      ├── Password
│      ├── Access Key
│      └── Secret Key
```

Typical use cases:

- Developers
- Administrators
- Automation accounts
- Legacy applications

---

## Advantages

- Easy to create.
- Supports Console and CLI access.
- Suitable for development environments.
- Can use IAM policies for fine-grained permissions.

---

## Disadvantages

- Long-term credentials.
- Manual key rotation.
- Higher risk if credentials are leaked.
- Not recommended for production workloads.

---

# IAM Role

An **IAM Role** is an AWS identity that provides **temporary credentials** instead of permanent access keys.

Unlike IAM Users, a role has **no password** and **no permanent Access Key**.

Instead, AWS issues temporary credentials whenever a trusted entity assumes the role.

Example:

```text
AWS Account
│
├── IAM Role
│      │
│      └── Temporary Credentials
```

---

## Who Can Assume a Role?

Many AWS services can assume roles.

Examples include:

- EC2
- Lambda
- ECS Tasks
- EKS Pods
- CloudFormation
- AWS Glue
- CodeBuild

Users and external AWS accounts can also assume roles.

---

## Why Roles Are Better

Temporary credentials automatically expire.

Advantages include:

- Improved security
- Automatic credential rotation
- No long-term secrets
- Reduced operational overhead

This is why AWS recommends IAM Roles for nearly all production workloads.

---

# IAM User vs IAM Role

| Feature | IAM User | IAM Role |
|----------|-----------|-----------|
| Long-term Credentials | ✅ | ❌ |
| Temporary Credentials | ❌ | ✅ |
| Password | ✅ | ❌ |
| Access Keys | ✅ | ❌ |
| Automatic Rotation | ❌ | ✅ |
| Best for Production | Limited | ✅ |

---

# Long-Term Credentials

Long-term credentials consist of:

- Access Key ID
- Secret Access Key

Example:

```text
AKIAIOSFODNN7EXAMPLE

wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

These credentials remain valid until:

- Deleted
- Disabled
- Rotated

Long-term credentials are commonly associated with IAM Users.

---

## Risks of Long-Term Credentials

If these credentials are leaked:

- Anyone possessing them can authenticate as that IAM User.
- The credentials remain valid until revoked.
- Attackers may gain persistent access.

Common causes of credential leakage:

- Git repositories
- Screenshots
- Log files
- Configuration files
- Shared documents

---

# Temporary Credentials

Temporary credentials are issued by **AWS Security Token Service (STS)**.

A temporary credential contains:

- Access Key ID
- Secret Access Key
- Session Token
- Expiration Time

Example:

```text
Access Key ID

Secret Access Key

Session Token

Expiration
```

Unlike long-term credentials, temporary credentials automatically become invalid after expiration.

---

# Why Temporary Credentials Are Preferred

Advantages:

- Automatic expiration
- Lower security risk
- Short-lived access
- Ideal for production workloads
- No manual key rotation

AWS recommends temporary credentials whenever possible.

---

# AWS Security Token Service (STS)

AWS STS is the service responsible for generating temporary credentials.

Typical workflow:

```text
IAM User
      │
      ▼
Assume Role
      │
      ▼
AWS STS
      │
      ▼
Temporary Credentials
      │
      ▼
AWS CLI
```

The AWS CLI automatically uses these temporary credentials after a successful role assumption.

---

# Example Scenario

Imagine a backend application running on an EC2 instance.

Instead of storing Access Keys:

```text
EC2 Instance
      │
      ▼
IAM Role
      │
      ▼
Temporary Credentials
      │
      ▼
Amazon S3
```

No credentials are stored on the server.

AWS automatically provides and rotates temporary credentials.

This is significantly more secure than embedding Access Keys inside configuration files.

---

# Architecture Note

A common misconception is that an IAM Role "contains" credentials.

It does not.

A role contains:

- Trust Policy
- Permission Policies

When a trusted entity assumes the role, AWS STS **generates temporary credentials**.

Those credentials are then used to sign AWS API requests.

---

# Security Recommendation

Avoid creating Access Keys unless absolutely necessary.

Preferred order:

1. IAM Roles
2. AWS IAM Identity Center (SSO)
3. Temporary STS Credentials
4. IAM User Access Keys (only when required)

This aligns with AWS security best practices.

---

# Interview Note

**Question**

Why are IAM Roles considered more secure than IAM Users?

**Answer**

IAM Roles use temporary credentials generated by AWS STS. These credentials automatically expire and are rotated by AWS, eliminating the need to manage long-term Access Keys. This significantly reduces the impact of credential leakage and is why AWS recommends IAM Roles for production workloads.

---

# Key Takeaways

- IAM Users typically use long-term credentials.
- IAM Roles use temporary credentials issued by AWS STS.
- Temporary credentials automatically expire.
- IAM Roles are the recommended authentication mechanism for production workloads.
- Long-term Access Keys should be minimized and rotated regularly.
- AWS STS plays a central role in secure authentication for AWS CLI and SDKs.

---

# Named Profiles

As your AWS usage grows, you'll often need to manage multiple AWS accounts or identities.

For example:

- Personal AWS Account
- Company Development Account
- QA Environment
- Staging Environment
- Production Environment

Reconfiguring the AWS CLI every time you switch accounts is inefficient and error-prone.

Named Profiles solve this problem.

---

# What is a Named Profile?

A **Named Profile** is a named collection of AWS CLI configuration settings.

Each profile contains its own:

- Access Key ID
- Secret Access Key
- Default Region
- Output Format

Instead of having only one configuration, you can maintain multiple independent configurations.

Example:

```text
default
development
testing
staging
production
```

---

# Why Use Named Profiles?

Without named profiles:

```text
Developer

↓

aws configure

↓

Overwrite Existing Credentials

↓

Use Another Account
```

Every account switch requires overwriting credentials.

---

With named profiles:

```text
Developer

↓

aws s3 ls --profile development

↓

aws s3 ls --profile production
```

No credentials are overwritten.

---

# Creating a Named Profile

Use:

```bash
aws configure --profile development
```

AWS CLI prompts:

```text
AWS Access Key ID:

AWS Secret Access Key:

Default region:

Default output format:
```

Example:

```bash
aws configure --profile production
```

You can create as many profiles as needed.

---

# Configuration Files

After creating profiles, the credentials file becomes:

```ini
[default]
aws_access_key_id=AKIAxxxxxxxxxxxx
aws_secret_access_key=xxxxxxxxxxxx

[development]
aws_access_key_id=AKIAyyyyyyyyyyyy
aws_secret_access_key=yyyyyyyyyyyy

[production]
aws_access_key_id=AKIAzzzzzzzzzzzz
aws_secret_access_key=zzzzzzzzzzzz
```

---

The configuration file:

```ini
[default]
region=ap-south-1
output=json

[profile development]
region=ap-south-1
output=json

[profile production]
region=us-east-1
output=json
```

Notice that the configuration file prefixes non-default profiles with:

```text
profile
```

while the credentials file does **not**.

This is one of the most common mistakes beginners make.

---

# Listing Profiles

Display all configured profiles:

```bash
aws configure list-profiles
```

Example:

```text
default
development
testing
production
```

This command is extremely useful when working across multiple AWS environments.

---

# Using a Profile

Specify the profile explicitly:

```bash
aws s3 ls \
--profile development
```

Example:

```bash
aws ec2 describe-instances \
--profile production
```

The specified profile overrides the default configuration for that command.

---

# Setting a Default Profile

Instead of specifying `--profile` every time, you can use an environment variable.

Linux/macOS

```bash
export AWS_PROFILE=development
```

Windows PowerShell

```powershell
$Env:AWS_PROFILE="development"
```

Verify:

```bash
echo $AWS_PROFILE
```

Now every AWS CLI command automatically uses the selected profile.

Example:

```bash
aws s3 ls
```

No `--profile` option is required.

---

# Checking the Active Identity

Never assume you're using the correct account.

Always verify before making infrastructure changes.

```bash
aws sts get-caller-identity
```

Example:

```json
{
    "Account":"123456789012",
    "Arn":"arn:aws:iam::123456789012:user/developer"
}
```

This command should become part of your daily workflow.

---

# Switching Between Accounts

Development

```bash
aws s3 ls \
--profile development
```

Production

```bash
aws s3 ls \
--profile production
```

Testing

```bash
aws s3 ls \
--profile testing
```

No files need to be modified.

No credentials are overwritten.

---

# Real-World Example

Imagine you're responsible for three AWS accounts.

```text
Development

↓

123456789012

↓

QA

↓

234567890123

↓

Production

↓

345678901234
```

Instead of repeatedly changing credentials, you simply switch profiles.

```bash
aws ecs list-clusters \
--profile development
```

```bash
aws ecs list-clusters \
--profile production
```

This approach is safer, faster, and less error-prone.

---

# Common Mistakes

## Forgetting the Profile

Running:

```bash
aws s3 rm s3://production-bucket/file.txt
```

instead of

```bash
aws s3 rm s3://production-bucket/file.txt \
--profile production
```

could execute against the wrong AWS account.

---

## Using the Default Profile for Everything

Many engineers configure only the default profile.

As environments grow, this becomes difficult to manage.

Use descriptive profile names instead.

Examples:

```text
development

testing

staging

production
```

Avoid:

```text
profile1

profile2

accountA
```

---

## Editing Files Manually

Avoid manually editing:

```text
~/.aws/config
```

or

```text
~/.aws/credentials
```

unless necessary.

Use:

```bash
aws configure
```

whenever possible.

---

# Production Best Practices

- Create separate profiles for every AWS account.
- Never use production as the default profile.
- Verify your identity using `aws sts get-caller-identity`.
- Prefer descriptive profile names.
- Store credentials securely.
- Remove unused profiles.
- Rotate access keys regularly.

---

# Architecture Note

Named Profiles are **local AWS CLI configurations**.

They are **not** AWS resources.

Deleting a profile only removes local configuration.

It does **not** delete:

- IAM Users
- IAM Roles
- Access Keys
- AWS Accounts

---

# Interview Note

**Question**

When would you use Named Profiles?

**Answer**

Named Profiles are used to manage multiple AWS accounts or identities from a single machine. Each profile stores separate credentials and configuration, allowing engineers to switch between environments without overwriting existing settings.

---

# Key Takeaways

- Named Profiles simplify multi-account management.
- Each profile has independent credentials and configuration.
- Use `--profile` to select a profile for a command.
- Use `AWS_PROFILE` to change the default profile for a session.
- Always verify the active account before making production changes.
- Use meaningful profile names such as `development`, `staging`, and `production`.


# AWS Credential Provider Chain

When you execute an AWS CLI command, the CLI must determine **which credentials** to use before it can authenticate the request.

For example:

```bash
aws s3 ls
```

Before contacting Amazon S3, the AWS CLI searches for credentials using a predefined order known as the **Credential Provider Chain**.

The first valid credentials it finds are used to sign the request.

---

# What is the Credential Provider Chain?

The Credential Provider Chain is the sequence AWS CLI follows to locate valid credentials.

Instead of checking every possible location randomly, AWS CLI searches in a fixed order.

If credentials are found at one step, the remaining steps are skipped.

---

# Credential Lookup Order

The AWS CLI searches for credentials in the following order:

```text
1. Command Line Options
        │
        ▼
2. Environment Variables
        │
        ▼
3. Named Profile
        │
        ▼
4. Credentials File
        │
        ▼
5. Configuration File
        │
        ▼
6. Assume Role Configuration
        │
        ▼
7. AWS IAM Identity Center (SSO)
        │
        ▼
8. EC2 Instance Profile
        │
        ▼
9. ECS Task Role
        │
        ▼
10. AWS CloudShell Credentials
```

The search stops as soon as valid credentials are found.

---

# Visual Workflow

```text
AWS CLI Command
        │
        ▼
Check Environment Variables
        │
        ▼
Found?
   │
   ├── Yes → Use Them
   │
   └── No
        │
        ▼
Check Named Profile
        │
        ▼
Found?
   │
   ├── Yes → Use Them
   │
   └── No
        │
        ▼
Continue Searching...
```

---

# Example 1

Suppose you execute:

```bash
aws s3 ls
```

Your machine contains:

Environment Variable:

```text
AWS_ACCESS_KEY_ID
```

Named Profile:

```text
production
```

Default Profile:

```text
default
```

AWS CLI immediately uses the **Environment Variable**.

It never checks the remaining locations.

---

# Example 2

You execute:

```bash
aws s3 ls \
--profile development
```

Since you explicitly specified a profile, AWS CLI immediately uses that profile.

It ignores the default profile.

---

# Example 3

Running on EC2

Imagine an EC2 instance with an attached IAM Role.

No credentials exist locally.

No profiles exist.

No environment variables exist.

AWS CLI automatically retrieves temporary credentials from the EC2 Instance Metadata Service (IMDS).

No manual configuration is required.

---

# Example 4

Running inside Amazon ECS

Your container has an ECS Task Role attached.

AWS CLI retrieves temporary credentials from the ECS metadata endpoint.

Again, no credentials need to be stored inside the container.

---

# Why This Matters

Many authentication issues occur because engineers assume the AWS CLI is using one set of credentials when it is actually using another.

For example:

You export:

```bash
export AWS_ACCESS_KEY_ID=XXXXXXXX
```

Months later you forget about it.

Even though your profile contains new credentials:

```text
production
```

AWS CLI continues using the environment variable because it has higher priority.

This often leads to confusing authentication failures.

---

# Checking Which Credentials Are Being Used

The simplest command is:

```bash
aws sts get-caller-identity
```

Example:

```json
{
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:user/backend-user"
}
```

This immediately shows which identity authenticated the request.

---

# Viewing Configuration

Display the active configuration:

```bash
aws configure list
```

Example:

```text
Name        Value       Type

profile     default     manual
region      ap-south-1  config-file
```

The **Type** column indicates where AWS CLI obtained each value.

This is extremely useful when troubleshooting.

---

# Common Authentication Problems

## Wrong AWS Account

Symptom:

Resources appear to be missing.

Cause:

AWS CLI authenticated using another profile or environment variable.

---

## Access Denied

Symptom:

```text
AccessDenied
```

Cause:

Authentication succeeded.

Authorization failed.

The IAM identity lacks the required permissions.

---

## Unable to Locate Credentials

Cause:

No valid credentials were found anywhere in the provider chain.

---

## Expired Token

Cause:

Temporary credentials have expired.

Refresh the credentials or assume the role again.

---

# Production Best Practices

- Prefer IAM Roles over long-term Access Keys.
- Avoid storing credentials in shell startup files.
- Use named profiles for local development.
- Verify your identity with `aws sts get-caller-identity` before making production changes.
- Remove unused environment variables.
- Never hardcode credentials into scripts or applications.

---

# Architecture Note

The AWS Credential Provider Chain is used not only by the AWS CLI but also by most AWS SDKs, including:

- Python (Boto3)
- Java
- JavaScript
- Go
- .NET
- Ruby

Learning this workflow will help you troubleshoot authentication issues across nearly every AWS development environment.

---

# Interview Note

**Question**

How does the AWS CLI decide which credentials to use?

**Answer**

AWS CLI follows the AWS Credential Provider Chain. It checks several credential sources in a predefined order—such as environment variables, named profiles, credentials files, IAM roles, and AWS IAM Identity Center (SSO)—and uses the first valid credentials it finds. Once valid credentials are located, the search stops.

---

# Key Takeaways

- AWS CLI does not randomly search for credentials.
- It follows a predefined Credential Provider Chain.
- The first valid credentials found are used.
- Environment variables can override profile-based authentication.
- IAM Roles eliminate the need for long-term credentials.
- `aws sts get-caller-identity` is the quickest way to verify the active identity.
- Understanding the Credential Provider Chain is essential for troubleshooting authentication issues.


# Environment Variables

Environment variables provide a convenient way to supply AWS credentials and configuration without storing them in configuration files.

Instead of reading values from `~/.aws/credentials`, AWS CLI can read them directly from your operating system's environment.

This approach is commonly used in:

- CI/CD pipelines
- Docker containers
- Kubernetes
- GitHub Actions
- Jenkins
- GitLab CI/CD
- AWS CodeBuild
- Temporary development sessions

---

# Why Use Environment Variables?

Environment variables are useful because they:

- Avoid storing credentials on disk.
- Simplify automation.
- Allow temporary credential injection.
- Work well in containerized environments.
- Integrate easily with secret management systems.

Unlike configuration files, environment variables exist only for the current shell session unless explicitly persisted.

---

# Common AWS Environment Variables

| Variable | Purpose |
|-----------|---------|
| `AWS_ACCESS_KEY_ID` | Access Key ID |
| `AWS_SECRET_ACCESS_KEY` | Secret Access Key |
| `AWS_SESSION_TOKEN` | Temporary session token |
| `AWS_DEFAULT_REGION` | Default AWS Region |
| `AWS_PROFILE` | Named profile to use |
| `AWS_DEFAULT_OUTPUT` | Output format |

These variables override values stored in configuration files.

---

# Setting Environment Variables

## Linux/macOS

```bash
export AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxxxxx

export AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxx

export AWS_DEFAULT_REGION=ap-south-1
```

Verify:

```bash
echo $AWS_ACCESS_KEY_ID

echo $AWS_DEFAULT_REGION
```

---

## Windows PowerShell

```powershell
$Env:AWS_ACCESS_KEY_ID="AKIAxxxxxxxxxxxxxxxx"

$Env:AWS_SECRET_ACCESS_KEY="xxxxxxxxxxxxxxxx"

$Env:AWS_DEFAULT_REGION="ap-south-1"
```

Verify:

```powershell
echo $Env:AWS_ACCESS_KEY_ID
```

---

## Windows Command Prompt

```cmd
set AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxxxxx

set AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxx

set AWS_DEFAULT_REGION=ap-south-1
```

---

# Using Temporary Credentials

When using temporary credentials from AWS STS, an additional variable is required.

Linux/macOS

```bash
export AWS_ACCESS_KEY_ID=ASIAxxxxxxxxxxxx

export AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxx

export AWS_SESSION_TOKEN=IQoJb3JpZ2luX2VjE...

export AWS_DEFAULT_REGION=ap-south-1
```

Without the session token, authentication will fail.

---

# Switching Profiles Using Environment Variables

Instead of specifying:

```bash
aws s3 ls \
--profile development
```

You can set:

Linux/macOS

```bash
export AWS_PROFILE=development
```

Windows PowerShell

```powershell
$Env:AWS_PROFILE="development"
```

Now every AWS CLI command automatically uses the selected profile.

Example:

```bash
aws ec2 describe-instances
```

No `--profile` argument is required.

---

# Viewing the Current Profile

Linux/macOS

```bash
echo $AWS_PROFILE
```

Windows PowerShell

```powershell
echo $Env:AWS_PROFILE
```

---

# Changing the Default Region

Instead of modifying configuration files, you can temporarily override the Region.

Linux/macOS

```bash
export AWS_DEFAULT_REGION=us-east-1
```

Windows PowerShell

```powershell
$Env:AWS_DEFAULT_REGION="us-east-1"
```

This affects only the current shell session.

---

# Checking Active Identity

Whenever environment variables are used, verify the active identity.

```bash
aws sts get-caller-identity
```

Example:

```json
{
    "Account":"123456789012",
    "Arn":"arn:aws:iam::123456789012:user/backend-user"
}
```

This confirms which credentials AWS CLI is currently using.

---

# Environment Variables vs Named Profiles

| Environment Variables | Named Profiles |
|-----------------------|----------------|
| Temporary | Persistent |
| Good for automation | Good for local development |
| Stored in memory | Stored in configuration files |
| Easy to inject into containers | Easy to switch manually |
| Common in CI/CD | Common on developer machines |

Both methods are widely used and often complement each other.

---

# Environment Variable Precedence

Environment variables have a higher priority than values stored in the AWS configuration files.

Example:

Configuration file:

```ini
region = ap-south-1
```

Environment variable:

```bash
export AWS_DEFAULT_REGION=us-east-1
```

Result:

AWS CLI uses:

```text
us-east-1
```

because the environment variable overrides the configuration file.

---

# Common Mistakes

## Forgetting Old Environment Variables

You exported credentials several days ago.

Today you configure a new profile.

AWS CLI still uses the environment variables.

This is one of the most common authentication problems.

---

## Forgetting Session Tokens

Temporary credentials require:

- Access Key ID
- Secret Access Key
- Session Token

Missing the session token results in authentication failures.

---

## Hardcoding Credentials

Avoid:

```bash
export AWS_ACCESS_KEY_ID=AKIA...
```

inside:

- `.bashrc`
- `.zshrc`
- PowerShell profile

unless absolutely necessary.

Long-lived credentials should not be permanently stored in shell startup files.

---

# Production Best Practices

- Prefer IAM Roles whenever possible.
- Use environment variables primarily for automation.
- Remove environment variables after temporary use.
- Store secrets in secret management systems rather than scripts.
- Verify the active identity before making infrastructure changes.
- Never expose credentials in logs or terminal recordings.

---

# Architecture Note

Container platforms such as Docker and Kubernetes frequently inject AWS credentials as environment variables.

Similarly, CI/CD platforms such as GitHub Actions, Jenkins, and GitLab CI provide secure mechanisms for supplying environment variables at runtime.

This approach eliminates the need to store credentials inside application images or source code repositories.

---

# Interview Note

### Question

Why are environment variables commonly used in CI/CD pipelines?

### Answer

Environment variables allow AWS credentials to be injected securely at runtime without storing them in configuration files or source code. Since they exist only for the lifetime of the process or job, they are well suited for automated deployments and temporary authentication.

---

# Key Takeaways

- Environment variables provide an alternative to configuration files.
- They are widely used in automation and containerized environments.
- They override configuration file values.
- Temporary credentials require an additional session token.
- Always verify the active identity with `aws sts get-caller-identity`.
- Avoid storing long-term credentials in persistent shell configuration files.

# AWS IAM Identity Center (SSO)

## What is AWS IAM Identity Center?

AWS IAM Identity Center (formerly **AWS Single Sign-On**) is AWS's recommended authentication solution for organizations that manage multiple AWS accounts.

Instead of creating IAM Users and Access Keys for every developer, engineers authenticate through an identity provider such as:

- Microsoft Entra ID (Azure AD)
- Okta
- Ping Identity
- Active Directory
- Built-in Identity Center Directory

After successful authentication, AWS CLI receives **temporary credentials**.

No permanent Access Keys are stored on the developer's machine.

---

# Why Use IAM Identity Center?

Traditional authentication:

```
Developer

↓

Access Key

↓

Secret Key

↓

AWS CLI
```

Modern authentication:

```
Developer

↓

Corporate Login

↓

AWS IAM Identity Center

↓

Temporary Credentials

↓

AWS CLI
```

Advantages:

- No long-term credentials
- Centralized identity management
- Automatic credential expiration
- Easier onboarding and offboarding
- Improved security
- Multi-account support

AWS recommends IAM Identity Center for enterprise environments.

---

# Configure AWS CLI for IAM Identity Center

Start the configuration wizard:

```bash
aws configure sso
```

The CLI prompts for:

```text
SSO session name

SSO start URL

SSO region

AWS Account

Permission Set
```

Example:

```text
SSO session name:
company

SSO start URL:
https://company.awsapps.com/start

SSO Region:
us-east-1
```

---

# Login

Authenticate using:

```bash
aws sso login
```

A browser window opens automatically.

Complete the authentication process using your organization's identity provider.

Once authenticated, AWS CLI caches temporary credentials locally.

---

# Verify Authentication

```bash
aws sts get-caller-identity
```

Example:

```json
{
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/AdministratorAccess/John"
}
```

Notice that the identity is an **assumed role**, not an IAM User.

---

# Logout

Remove cached credentials:

```bash
aws sso logout
```

Useful when:

- Switching users
- Changing organizations
- Troubleshooting authentication
- Revoking local access

---

# Where Does AWS CLI Store SSO Tokens?

AWS CLI stores cached authentication tokens locally.

Typical location:

Linux/macOS

```text
~/.aws/sso/cache
```

Windows

```text
C:\Users\<username>\.aws\sso\cache
```

The cache contains temporary authentication information.

Do not manually modify these files.

---

# Authentication Methods Comparison

| Method | Long-Term Credentials | Temporary Credentials | Recommended |
|----------|----------------------|-----------------------|-------------|
| IAM User | ✅ | ❌ | Legacy / Limited |
| IAM Role | ❌ | ✅ | ✅ |
| IAM Identity Center | ❌ | ✅ | ✅ |
| Environment Variables | Depends | Depends | Automation |
| Named Profiles | Depends | Depends | Local Development |

---

# Security Best Practices

Authentication is the foundation of AWS security.

Follow these recommendations in production environments.

---

## Prefer IAM Roles

Use IAM Roles whenever possible.

Avoid creating Access Keys for applications running on:

- EC2
- ECS
- Lambda
- EKS

AWS automatically provides temporary credentials.

---

## Prefer IAM Identity Center

For engineers accessing AWS accounts manually:

Use:

```
IAM Identity Center
```

instead of

```
IAM User + Access Keys
```

---

## Rotate Credentials

If long-term Access Keys must be used:

- Rotate them regularly.
- Remove unused keys.
- Disable compromised keys immediately.

---

## Never Use the Root Account

The AWS Root User should never be used for daily administration.

Reserve it for:

- Billing
- Account recovery
- Organization setup
- Emergency operations

---

## Follow the Principle of Least Privilege

Grant only the permissions required.

Avoid:

```text
AdministratorAccess
```

unless absolutely necessary.

---

## Never Commit Credentials

Do not commit:

```text
~/.aws/credentials
```

or

```text
Access Keys
```

or

```text
Secret Keys
```

to Git repositories.

---

## Use Temporary Credentials

Whenever possible:

- IAM Roles
- STS
- IAM Identity Center

instead of permanent Access Keys.

---

# Common Authentication Errors

---

## Unable to Locate Credentials

```text
Unable to locate credentials
```

Cause:

No credentials were found.

Possible solutions:

- Configure AWS CLI.
- Set the correct profile.
- Login using IAM Identity Center.
- Verify environment variables.

---

## AccessDenied

```text
AccessDenied
```

Authentication succeeded.

Authorization failed.

The IAM identity lacks permission.

---

## InvalidClientTokenId

```text
The security token included in the request is invalid.
```

Possible causes:

- Incorrect Access Key
- Incorrect Secret Key
- Disabled Access Key

---

## ExpiredToken

```text
ExpiredToken
```

Temporary credentials have expired.

Solutions:

```bash
aws sso login
```

or

assume the role again.

---

## SignatureDoesNotMatch

Common causes:

- Wrong Secret Key
- Incorrect Region
- System clock drift

---

## RequestTimeTooSkewed

The local system clock differs significantly from AWS.

Synchronize the clock using NTP.

---

# Production Tips

Before making infrastructure changes:

Always execute:

```bash
aws sts get-caller-identity
```

Verify:

- AWS Account
- IAM Identity
- IAM Role
- Active Profile

This simple habit prevents accidental changes to the wrong AWS account.

---

# Architecture Note

Modern AWS environments rarely use long-term credentials.

A typical authentication flow is:

```
Developer

↓

Corporate Identity Provider

↓

AWS IAM Identity Center

↓

Temporary Credentials

↓

AWS CLI

↓

AWS APIs
```

This approach minimizes credential exposure while improving security and operational efficiency.

---

# Interview Questions

### Why are IAM Roles preferred over IAM Users?

Because IAM Roles provide temporary credentials that expire automatically, reducing the risk associated with long-term Access Keys.

---

### Why does AWS recommend IAM Identity Center?

Because it centralizes authentication, integrates with enterprise identity providers, and eliminates the need for permanent Access Keys.

---

### What command verifies the active AWS identity?

```bash
aws sts get-caller-identity
```

---

### What is the Credential Provider Chain?

It is the order AWS CLI follows to locate valid credentials before signing a request.

---

### Does AWS CLI send the Secret Access Key to AWS?

No.

The Secret Access Key remains on the local machine and is used to generate a Signature Version 4 (SigV4) cryptographic signature.

---

# Chapter Summary

In this chapter, you learned:

- Authentication vs Authorization
- IAM Users
- IAM Roles
- Access Keys
- Secret Access Keys
- Temporary Credentials
- AWS STS
- Named Profiles
- Credential Provider Chain
- Environment Variables
- AWS IAM Identity Center (SSO)
- Security Best Practices
- Common Authentication Errors
- Production Authentication Strategies

These concepts form the foundation of secure AWS CLI usage and are essential knowledge for Backend Engineers, DevOps Engineers, Cloud Engineers, and AWS Solutions Architects.

---


# Senior-Level Deep Dives

---

## SigV4 Internals — What Actually Happens When You Sign a Request

Most engineers know "the Secret Key signs the request." Senior engineers know the exact mechanics — which matters for debugging custom SDK integrations, Lambda authorizers, and IAM policy conditions.

### The Four Steps of SigV4

**Step 1 — Create a Canonical Request**

A deterministic string is assembled from:
- HTTP method (`GET`, `POST`, etc.)
- URI path, URI-encoded
- Query string parameters, sorted
- Headers to sign (host, content-type, x-amz-date, etc.)
- Signed headers list
- SHA-256 hash of the request body

```text
GET
/

Action=ListBuckets&Version=2006-03-01
host:s3.amazonaws.com
x-amz-date:20260712T120000Z

host;x-amz-date
e3b0c44298fc1c149...  ← SHA-256 of empty body
```

**Step 2 — Create a String to Sign**

```text
AWS4-HMAC-SHA256
20260712T120000Z
20260712/ap-south-1/s3/aws4_request
<SHA-256 of canonical request>
```

**Step 3 — Derive the Signing Key**

A chain of HMAC-SHA256 operations derives a per-day/region/service signing key:

```
kSecret   = "AWS4" + SecretAccessKey
kDate     = HMAC(kSecret, "20260712")
kRegion   = HMAC(kDate, "ap-south-1")
kService  = HMAC(kRegion, "s3")
kSigning  = HMAC(kService, "aws4_request")
```

**Step 4 — Calculate the Signature**

```
signature = HMAC-SHA256(kSigning, StringToSign)
```

The resulting hex string goes into the `Authorization` header.

### Why This Matters

- The signing key is **scoped**: a key derived for `ap-south-1/s3` cannot sign a request for `us-east-1/iam`. This limits blast radius if a signing key leaks.
- AWS recomputes the same signature server-side. If both match → request authenticated.
- The `x-amz-date` timestamp prevents **replay attacks**: AWS rejects requests older than 15 minutes.
- Debugging `SignatureDoesNotMatch` requires checking: Secret Key value, Region in the scope string, clock skew, and whether the body hash was computed correctly.

---

## The Credential Provider Chain — Full Details

The lookup order matters enormously in production. Understanding it stops an entire class of "wrong account" incidents.

```text
Priority  Source                              Triggered by
────────  ──────────────────────────────────  ────────────────────────────────────
1         CLI option                          --profile, explicit flag
2         AWS_ACCESS_KEY_ID env var           Injected by CI/CD, Docker, shell
3         AWS_PROFILE env var                 Shell session setting
4         ~/.aws/config [profile ...] assume  aws_role_arn + source_profile
5         ~/.aws/credentials [profile]        Long-term or STS creds on disk
6         Container credential endpoint       ECS task role via $AWS_CONTAINER_CREDENTIALS_RELATIVE_URI
7         IMDSv2 on EC2                       Instance profile, fetched from 169.254.169.254
8         SSO cache (~/.aws/sso/cache)        After aws sso login
9         Process credentials                 credential_process = in config
```

### Dangerous Scenario

An engineer ran this months ago:
```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
```

Then configured a new production profile. The environment variable still takes priority. `aws sts get-caller-identity` silently returns the old identity. Adding `--debug` reveals `credentials found in environment variables` in the provider chain output.

**Fix:** `unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN`

### Overriding the Chain in Code (Boto3 Context)

The same chain applies to Boto3 and all AWS SDKs. A Lambda function with an execution role never needs explicit credentials — the SDK resolves the task's IAM role automatically via step 6.

---

## Assume-Role Chaining and Cross-Account Access

A critical pattern in multi-account organizations:

```bash
# Assume a role in another account and capture temporary creds
CREDS=$(aws sts assume-role \
  --role-arn arn:aws:iam::987654321098:role/DeploymentRole \
  --role-session-name my-deploy-session \
  --duration-seconds 3600 \
  --output json)

export AWS_ACCESS_KEY_ID=$(echo $CREDS | jq -r .Credentials.AccessKeyId)
export AWS_SECRET_ACCESS_KEY=$(echo $CREDS | jq -r .Credentials.SecretAccessKey)
export AWS_SESSION_TOKEN=$(echo $CREDS | jq -r .Credentials.SessionToken)

# Verify you are now acting in the target account
aws sts get-caller-identity
```

Or configure it declaratively in `~/.aws/config`:

```ini
[profile production]
role_arn = arn:aws:iam::987654321098:role/DeploymentRole
source_profile = management
role_session_name = engineer-session
duration_seconds = 3600
```

Now `aws s3 ls --profile production` automatically chains the assume-role.

### MFA-Protected Role Assumption

```bash
aws sts assume-role \
  --role-arn arn:aws:iam::987654321098:role/AdminRole \
  --role-session-name mfa-session \
  --serial-number arn:aws:iam::123456789012:mfa/my-device \
  --token-code 123456
```

Add `mfa_serial` to `~/.aws/config` and the CLI prompts for the token automatically.

---

## IMDSv2 — Why IMDSv1 Is Disabled in Modern Infrastructure

The EC2 Instance Metadata Service (IMDS) at `169.254.169.254` is how an instance fetches its own IAM role credentials. IMDSv1 used a simple GET — vulnerable to SSRF attacks.

**IMDSv2 requires a session token:**

```bash
# 1. Get a token (valid for up to 6 hours)
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# 2. Use the token to fetch role credentials
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

AWS CLI automatically uses IMDSv2. When you launch EC2 instances, enforce it:

```bash
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --instance-type t3.micro \
  --metadata-options \
    HttpEndpoint=enabled,HttpTokens=required
```

`HttpTokens=required` means IMDSv1 is blocked. This is the current AWS recommended default.

---

## Session Token Refresh — Operational Patterns

Long-running scripts must handle credential expiry. Patterns used in production:

**Pattern 1 — Pre-check with `aws sts get-caller-identity` at script start**

```bash
if ! aws sts get-caller-identity --profile "$PROFILE" > /dev/null 2>&1; then
  echo "Credentials expired or missing. Run: aws sso login --profile $PROFILE"
  exit 1
fi
```

**Pattern 2 — Credential refresh loop**

```bash
refresh_creds() {
  EXPIRY=$(aws configure get aws_credential_expiry --profile "$PROFILE" 2>/dev/null)
  NOW=$(date -u +%s)
  EXPIRE_TS=$(date -d "$EXPIRY" +%s 2>/dev/null || echo 0)
  if (( EXPIRE_TS - NOW < 300 )); then
    aws sso login --profile "$PROFILE"
  fi
}
```

**Pattern 3 — Lambda credential refresh via environment**

Lambda automatically rotates the execution role credentials. They are available at `$AWS_ACCESS_KEY_ID`, `$AWS_SECRET_ACCESS_KEY`, `$AWS_SESSION_TOKEN` in the function environment. Never cache them beyond the function invocation.

---

## Senior Interview Questions — Authentication Deep Dive

**Q: A CI/CD pipeline runs fine in development but gets `AccessDenied` in production. Both use the same IAM policy. What do you check?**

Strong answer:
1. Verify the execution context — which IAM Role is the pipeline actually assuming in production vs. dev? Trust policies may differ.
2. Check for SCPs (Service Control Policies) at the AWS Organizations level — a policy may restrict actions in the production OU even if the IAM policy allows them.
3. Check Permission Boundaries — the production role might have one attached that limits effective permissions.
4. Check resource-based policies (bucket policy, KMS key policy) — even if identity policy allows, a resource policy may explicitly deny.
5. Run the command with `--debug` in a staging environment to capture the exact API call and compare against the policy.

---

**Q: You rotate an access key. Within an hour you receive alerts that a service is failing. What went wrong and how do you recover quickly?**

Strong answer:
- The new key was not propagated to all consumers. IAM key rotation creates the new key, but any application, container, CI/CD secret, or environment variable still holding the old key starts failing after it is disabled/deleted.
- Recovery: immediately re-enable the old key → identify all consumers → rotate them → verify → disable old key → wait 24h → delete.
- Prevention: audit key usage with IAM credential report and CloudTrail `AssumeRole`/`GetCredentials` events before rotation.

---

**Q: What is the difference between `sts:AssumeRole` and `sts:AssumeRoleWithWebIdentity`?**

- `AssumeRole`: authenticated AWS identity (IAM user or role) assumes another role. Used for cross-account access, least-privilege elevation.
- `AssumeRoleWithWebIdentity`: external OIDC identity (GitHub Actions, Kubernetes service account, Cognito) exchanges a web identity token for temporary AWS credentials. No long-lived AWS credentials needed. The preferred pattern for GitHub Actions CI/CD.

```bash
# GitHub Actions OIDC example (configured, not manually run)
aws sts assume-role-with-web-identity \
  --role-arn arn:aws:iam::123456789012:role/GitHubActionsRole \
  --role-session-name github-deploy \
  --web-identity-token "$GITHUB_OIDC_TOKEN"
```

---
