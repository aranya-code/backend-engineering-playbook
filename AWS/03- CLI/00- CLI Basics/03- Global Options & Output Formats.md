# Global Options & Output Formats

> Learn how AWS CLI global options modify the behavior of every command and how different output formats make automation, scripting, and troubleshooting easier.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand what global options are.
- Override configuration settings from the command line.
- Work with different output formats.
- Select AWS Regions dynamically.
- Execute commands against different AWS accounts.
- Prepare CLI commands for automation.
- Understand when to use each output format.

---

# What are Global Options?

Global options are command-line arguments that can be used with **almost every AWS CLI command**.

Unlike service-specific options, global options affect the overall behavior of the AWS CLI itself.

For example,

```bash
aws ec2 describe-instances \
    --region ap-south-1
```

The `--region` option is **not** specific to Amazon EC2.

It can also be used with:

```bash
aws s3 ls
```

```bash
aws iam list-users
```

```bash
aws lambda list-functions
```

```bash
aws ecs list-clusters
```

Global options work consistently across nearly every AWS service.

---

# Why Global Options Matter

Although AWS CLI can use the default configuration stored on your computer, there are many situations where you need to override those settings temporarily.

Examples include:

- Working with multiple AWS Regions
- Switching AWS accounts
- Producing JSON output for automation
- Displaying human-readable tables
- Debugging API requests
- Running commands in CI/CD pipelines

Global options allow you to modify command behavior without changing your saved configuration.

---

# General Command Syntax

Most AWS CLI commands follow this structure:

```bash
aws <service> <operation> [parameters] [global-options]
```

Example:

```bash
aws ec2 describe-instances \
    --region ap-south-1 \
    --output table
```

Breaking it down:

| Component | Description |
|----------|-------------|
| `aws` | AWS CLI executable |
| `ec2` | AWS Service |
| `describe-instances` | API Operation |
| `--region` | Global Option |
| `--output` | Global Option |

---

# Frequently Used Global Options

The following options are used regularly by AWS engineers.

| Global Option | Purpose |
|---------------|----------|
| `--region` | Specify AWS Region |
| `--profile` | Select Named Profile |
| `--output` | Select output format |
| `--query` | Filter JSON output |
| `--debug` | Display HTTP requests and responses |
| `--no-cli-pager` | Disable paging |
| `--color` | Enable or disable colored output |
| `--endpoint-url` | Specify a custom endpoint |
| `--no-verify-ssl` | Disable SSL certificate verification *(not recommended in production)* |
| `--cli-auto-prompt` | Interactive command builder |

These options are supported by nearly every AWS CLI command.

---

# Global Options vs Configuration Files

Suppose your configuration file contains:

```ini
region = ap-south-1
output = json
```

Now execute:

```bash
aws s3 ls \
    --region us-east-1 \
    --output table
```

Result:

AWS CLI ignores the configuration file for this command and uses:

- Region → `us-east-1`
- Output → `table`

The configuration file remains unchanged.

Global options affect **only the current command**.

---

# Global Option Precedence

AWS CLI determines configuration values using the following priority:

```text
Command Line Options
        │
        ▼
Environment Variables
        │
        ▼
Configuration Files
```

This means command-line options always have the highest priority.

Example:

Configuration file:

```text
Region

↓

ap-south-1
```

Environment Variable:

```text
AWS_DEFAULT_REGION

↓

eu-west-1
```

Command:

```bash
aws ec2 describe-instances \
--region us-east-1
```

AWS CLI ultimately uses:

```text
us-east-1
```

because command-line arguments override every other source.

---

# Understanding Output Formats

Every AWS CLI command returns structured data.

The CLI can display this information in multiple formats depending on your requirements.

Supported output formats include:

- JSON
- Table
- Text
- YAML
- YAML Stream

Example:

```bash
aws s3 ls \
--output json
```

or

```bash
aws s3 ls \
--output table
```

Choosing the appropriate output format makes commands easier to read or easier to process programmatically.

---

# When Should You Change the Output Format?

Different situations require different output formats.

| Use Case | Recommended Output |
|-----------|-------------------|
| Automation | JSON |
| Shell Scripts | Text |
| Human Reading | Table |
| Configuration Files | YAML |
| Large Data Streams | YAML Stream |

There is no universally "best" format.

The appropriate choice depends on how the command output will be consumed.

---

# Best Practices

- Use command-line options for temporary overrides.
- Avoid permanently changing your configuration unless necessary.
- Prefer `json` for automation.
- Use `table` when presenting information to humans.
- Keep commands explicit when working in production.
- Verify the Region and Profile before executing destructive operations.

---

# Architecture Note

Global options are processed **before** the AWS CLI sends the request to AWS.

This means options like `--region`, `--profile`, and `--output` influence how the request is built and how the response is displayed, but they do not change the AWS service itself.

---

# Interview Note

### Question

Why should you prefer command-line options instead of modifying the AWS CLI configuration file?

### Answer

Command-line options apply only to the current command, making them ideal for temporary overrides. This avoids accidentally changing the default configuration and reduces the risk of executing future commands against the wrong Region or AWS account.

---

# Key Takeaways

- Global options work across almost all AWS services.
- They temporarily override saved configuration.
- Command-line options have the highest precedence.
- Different output formats serve different purposes.
- Understanding global options is essential for scripting, automation, and production operations.

---

# Working with Global Options

Global options allow you to override the default AWS CLI configuration for a single command.

Unlike changing the configuration files, global options affect **only the current execution**.

This makes them ideal for:

- Switching Regions
- Switching AWS accounts
- Changing output formats
- Filtering responses
- Running automation scripts

---

# The `--region` Option

The `--region` option specifies which AWS Region should receive the request.

## Syntax

```bash
aws <service> <operation> --region <region>
```

Example:

```bash
aws ec2 describe-instances \
    --region ap-south-1
```

Instead of using the configured default Region, AWS CLI sends the request directly to **Mumbai (ap-south-1)**.

---

## Why Use `--region`?

Common scenarios:

- Working across multiple Regions
- Disaster recovery testing
- Multi-region deployments
- Regional resource verification
- Temporary overrides

Example:

```bash
aws s3api list-buckets \
    --region us-east-1
```

Although S3 buckets are globally visible, many other AWS services are Region-specific.

---

## Common Region Codes

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

## Example

List EC2 instances in Mumbai:

```bash
aws ec2 describe-instances \
--region ap-south-1
```

List EC2 instances in Virginia:

```bash
aws ec2 describe-instances \
--region us-east-1
```

Same command.

Different Region.

Different resources.

---

## Best Practice

Always specify the Region explicitly in:

- Deployment scripts
- CI/CD pipelines
- Production automation

Doing so avoids unexpected behavior caused by incorrect default Regions.

---

# The `--profile` Option

The `--profile` option tells AWS CLI which Named Profile should be used for authentication.

Syntax:

```bash
aws <service> <operation> \
--profile production
```

---

## Example

Development account:

```bash
aws s3 ls \
--profile development
```

Production account:

```bash
aws s3 ls \
--profile production
```

The same command executes against different AWS accounts.

---

## When Should You Use `--profile`?

Recommended when:

- Managing multiple AWS accounts
- Switching environments
- Consulting
- Working across organizations
- Using different IAM identities

---

## Verify Before Production

Always confirm the selected profile.

```bash
aws sts get-caller-identity \
--profile production
```

Example output:

```json
{
  "Account":"123456789012",
  "Arn":"arn:aws:iam::123456789012:user/backend-engineer"
}
```

This simple verification can prevent accidental changes to the wrong AWS account.

---

# The `--output` Option

AWS CLI supports multiple output formats.

Syntax:

```bash
aws <service> <operation> \
--output <format>
```

Supported formats:

- json
- table
- text
- yaml
- yaml-stream

---

## JSON Output

```bash
aws ec2 describe-instances \
--output json
```

Example:

```json
{
    "Reservations":[]
}
```

Recommended for:

- Python
- Shell scripts
- Automation
- APIs

---

## Table Output

```bash
aws ec2 describe-instances \
--output table
```

Example:

```text
---------------------------------------------
|            DescribeInstances              |
+----------------------+--------------------+
| InstanceId           | State              |
+----------------------+--------------------+
| i-0123456789abcdef0  | running            |
+----------------------+--------------------+
```

Ideal for human-readable reports.

---

## Text Output

```bash
aws ec2 describe-instances \
--output text
```

Example:

```text
i-0123456789abcdef0
```

Useful for shell scripting where only specific values are needed.

---

## YAML Output

```bash
aws ec2 describe-instances \
--output yaml
```

Useful when working with configuration-driven workflows.

---

# Choosing the Right Output

| Scenario | Recommended Output |
|----------|--------------------|
| Automation | json |
| Bash Scripts | text |
| Human Reading | table |
| Documentation | yaml |

---

# The `--query` Option

One of the most powerful AWS CLI features.

Instead of returning an entire JSON document, `--query` filters the response using **JMESPath**.

Example:

```bash
aws ec2 describe-instances \
--query "Reservations[*].Instances[*].InstanceId"
```

Output:

```json
[
  [
    "i-0123456789abcdef0"
  ]
]
```

Instead of hundreds of lines of JSON, only the required value is returned.

---

## Why Use `--query`?

Benefits:

- Smaller responses
- Faster automation
- Easier scripting
- Cleaner output
- Less post-processing

Almost every production automation script uses `--query`.

---

## Another Example

Retrieve only bucket names:

```bash
aws s3api list-buckets \
--query "Buckets[*].Name"
```

Result:

```json
[
    "production-backups",
    "images",
    "logs"
]
```

No unnecessary metadata is returned.

---

# Combining Global Options

Global options work together.

Example:

```bash
aws ec2 describe-instances \
--region ap-south-1 \
--profile production \
--output table \
--query "Reservations[*].Instances[*].[InstanceId,State.Name]"
```

This command:

- Uses the Production profile
- Queries the Mumbai Region
- Filters the response
- Displays it as a table

All without changing the saved AWS CLI configuration.

---

# Production Tips

- Always specify `--profile` when managing multiple AWS accounts.
- Specify `--region` in deployment scripts.
- Prefer JSON for automation.
- Use `--query` to minimize response size.
- Use `table` only for interactive human-readable output.

---

# Architecture Note

Global options are processed locally by the AWS CLI before the request is sent to AWS.

For example:

- `--profile` determines which credentials are used.
- `--region` determines which endpoint receives the request.
- `--query` filters the response **after** AWS returns it.
- `--output` controls how the response is displayed.

Understanding this execution order makes troubleshooting much easier.

---

# Interview Note

### Question

Which global options do you use most frequently in production?

### Sample Answer

The four options I use most often are:

- `--profile` to switch AWS accounts.
- `--region` to target the correct Region.
- `--output json` for automation.
- `--query` to extract only the required fields from large API responses.

These options make scripts cleaner, more reliable, and easier to maintain.

---

# Key Takeaways

- `--region` selects the target AWS Region.
- `--profile` selects the AWS identity.
- `--output` controls how results are displayed.
- `--query` filters API responses using JMESPath.
- These four options are the foundation of effective AWS CLI usage.

# Advanced Global Options

The AWS CLI provides several advanced global options that can simplify debugging, improve usability, and support development workflows.

Although these options are used less frequently than `--region` or `--profile`, they are invaluable when troubleshooting production issues or integrating with local AWS-compatible services.

---

# The `--debug` Option

One of the most powerful troubleshooting tools in AWS CLI.

## Purpose

Displays detailed debugging information for every request.

Syntax:

```bash
aws <service> <operation> --debug
```

Example:

```bash
aws s3 ls --debug
```

The CLI displays:

- Credential provider chain
- Request signing
- HTTP request
- HTTP response
- API endpoint
- Retry attempts
- Response headers
- Error details

---

## When Should You Use It?

- Authentication failures
- AccessDenied errors
- Invalid credentials
- Region issues
- API troubleshooting
- SDK development

---

## Example Output

```text
Loading credentials...

Signing request...

Sending HTTPS request...

Receiving response...

HTTP Status Code: 200
```

Real output is significantly more detailed.

---

## Production Tip

Avoid enabling `--debug` in production automation unless troubleshooting.

Debug logs may contain sensitive information such as:

- Account IDs
- Request IDs
- Resource ARNs
- API parameters

---

# The `--no-cli-pager` Option

AWS CLI Version 2 uses a pager by default.

Large outputs are displayed page by page.

Example:

```bash
aws iam list-users
```

The output opens inside a pager such as:

```
less
```

---

Disable the pager:

```bash
aws iam list-users \
--no-cli-pager
```

Now the output is printed directly to the terminal.

---

## When Should You Use It?

Recommended for:

- Automation
- Shell scripts
- CI/CD
- Redirecting output
- Pipe operations

Example:

```bash
aws s3 ls \
--no-cli-pager > buckets.txt
```

---

# The `--cli-auto-prompt` Option

Introduced in AWS CLI Version 2.

Instead of memorizing commands, AWS CLI provides an interactive command builder.

Example:

```bash
aws --cli-auto-prompt
```

or

```bash
aws ec2 run-instances \
--cli-auto-prompt
```

The CLI interactively asks for required parameters.

Example:

```text
AMI ID:

Instance Type:

Security Group:

Subnet:
```

This feature is excellent for:

- Beginners
- Learning AWS CLI
- Exploring unfamiliar services

---

# The `--endpoint-url` Option

Normally AWS CLI communicates with AWS endpoints.

Example:

```
https://ec2.ap-south-1.amazonaws.com
```

Sometimes developers need to connect to alternative endpoints.

Example:

- LocalStack
- MinIO
- AWS-compatible services
- Internal testing environments

Syntax:

```bash
aws s3 ls \
--endpoint-url http://localhost:4566
```

AWS CLI sends requests to the specified endpoint instead of AWS.

---

## Typical Use Cases

- LocalStack
- MinIO
- Development environments
- Integration testing
- Offline development

---

# The `--color` Option

Controls colored output.

Syntax:

```bash
aws ec2 describe-instances \
--color on
```

Supported values:

```text
on

off

auto
```

---

## When to Disable Colors?

Recommended when:

- Saving output to files
- Logging
- Automation
- CI/CD

Example:

```bash
aws s3 ls \
--color off
```

---

# The `--no-verify-ssl` Option

Disables SSL certificate verification.

Example:

```bash
aws s3 ls \
--no-verify-ssl
```

---

## When Is It Used?

Mostly for:

- Local development
- Testing environments
- Self-signed certificates

---

## Security Warning

Never use this option in production.

Disabling SSL verification increases the risk of man-in-the-middle attacks and should only be used in controlled development or testing environments.

---

# The `--cli-read-timeout` Option

Controls how long AWS CLI waits for a server response.

Example:

```bash
aws s3 sync . s3://my-bucket \
--cli-read-timeout 300
```

Default timeout:

```
60 seconds
```

Increase this value when working with:

- Large uploads
- Slow networks
- Cross-region transfers

---

# The `--cli-connect-timeout` Option

Controls how long AWS CLI waits while establishing a connection.

Example:

```bash
aws ec2 describe-instances \
--cli-connect-timeout 120
```

Useful for:

- High latency networks
- VPN connections
- Hybrid cloud environments

---

# Combining Multiple Global Options

Global options can be combined to suit different workflows.

Example:

```bash
aws s3 sync ./backup s3://company-backups \
    --profile production \
    --region ap-south-1 \
    --output json \
    --no-cli-pager
```

This command:

- Uses the Production profile.
- Targets the Mumbai Region.
- Produces JSON output.
- Disables the pager.

---

# Choosing the Right Option

| Situation | Recommended Option |
|-----------|--------------------|
| Debug authentication | `--debug` |
| Automation | `--no-cli-pager` |
| Learn commands | `--cli-auto-prompt` |
| LocalStack | `--endpoint-url` |
| Disable colors | `--color off` |
| Slow network | `--cli-read-timeout` |
| High latency | `--cli-connect-timeout` |

---

# Production Best Practices

- Enable `--debug` only while troubleshooting.
- Disable the pager in scripts and CI/CD pipelines.
- Use `--endpoint-url` only for local testing or AWS-compatible services.
- Never use `--no-verify-ssl` in production.
- Increase timeouts only when necessary.
- Prefer explicit command-line options instead of modifying global configuration for temporary tasks.

---

# Architecture Note

Global options influence different stages of command execution.

```text
AWS CLI Command
        │
        ▼
Read Configuration
        │
        ▼
Apply Global Options
        │
        ▼
Authenticate Request
        │
        ▼
Send HTTPS Request
        │
        ▼
Receive Response
        │
        ▼
Format Output
```

Understanding where each option is applied helps diagnose configuration and runtime issues.

---

# Interview Note

### Question

Which advanced global options have you used in production?

### Sample Answer

I frequently use:

- `--debug` for troubleshooting authentication and API errors.
- `--no-cli-pager` in automation and CI/CD pipelines.
- `--endpoint-url` when testing with LocalStack.
- `--cli-auto-prompt` to explore unfamiliar services and commands.

Each option improves productivity in different scenarios.

---

# Key Takeaways

- `--debug` provides detailed request and response information.
- `--no-cli-pager` is ideal for scripts and automation.
- `--cli-auto-prompt` simplifies command discovery.
- `--endpoint-url` enables testing against local or custom endpoints.
- `--color`, `--cli-read-timeout`, and `--cli-connect-timeout` provide additional control over CLI behavior.
- Advanced global options are especially valuable for troubleshooting and development workflows.

# Filtering Output with `--query` (JMESPath)

One of the biggest advantages of AWS CLI is that you don't have to process huge JSON responses manually.

Using the **`--query`** option, you can extract exactly the information you need directly from the AWS API response.

AWS CLI uses the **JMESPath** query language to filter JSON data.

Instead of processing hundreds of lines of JSON, you can retrieve only the required values.

---

# Why Use `--query`?

Suppose you execute:

```bash
aws ec2 describe-instances
```

The response may contain thousands of lines of JSON.

Most of the time, you only need:

- Instance IDs
- Public IP addresses
- State
- Tags
- Instance Type

Using `--query`, AWS CLI filters the response before displaying it.

This makes:

- Scripts simpler
- Output smaller
- Commands easier to read
- Automation faster

---

# Basic Syntax

```bash
aws <service> <operation> \
    --query "<JMESPath Expression>"
```

Example:

```bash
aws s3api list-buckets \
    --query "Buckets[*].Name"
```

Output

```json
[
    "company-backups",
    "images",
    "logs"
]
```

Only bucket names are returned.

---

# Selecting Individual Fields

Retrieve EC2 Instance IDs:

```bash
aws ec2 describe-instances \
    --query "Reservations[*].Instances[*].InstanceId"
```

Output

```json
[
    [
        "i-0123456789abcdef0"
    ]
]
```

---

Retrieve Instance Types:

```bash
aws ec2 describe-instances \
    --query "Reservations[*].Instances[*].InstanceType"
```

Output

```json
[
    [
        "t3.micro"
    ]
]
```

---

Retrieve Public IP Addresses:

```bash
aws ec2 describe-instances \
    --query "Reservations[*].Instances[*].PublicIpAddress"
```

---

# Returning Multiple Columns

Retrieve:

- Instance ID
- Instance Type
- State

```bash
aws ec2 describe-instances \
--query "Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name]"
```

Example output:

```json
[
    [
        [
            "i-0123456789abcdef0",
            "t3.micro",
            "running"
        ]
    ]
]
```

---

# Combining with Table Output

The real power comes from combining `--query` with `--output table`.

Example:

```bash
aws ec2 describe-instances \
--query "Reservations[*].Instances[*].[InstanceId,State.Name]" \
--output table
```

Output

```text
------------------------------------------
|       DescribeInstances                |
+----------------------+-----------------+
| i-0123456789abcdef0  | running         |
| i-0456789abcdef0123  | stopped         |
+----------------------+-----------------+
```

This is significantly easier to read than raw JSON.

---

# Filtering Specific Objects

Retrieve only bucket names:

```bash
aws s3api list-buckets \
--query "Buckets[*].Name"
```

Retrieve Lambda function names:

```bash
aws lambda list-functions \
--query "Functions[*].FunctionName"
```

Retrieve IAM user names:

```bash
aws iam list-users \
--query "Users[*].UserName"
```

Retrieve VPC IDs:

```bash
aws ec2 describe-vpcs \
--query "Vpcs[*].VpcId"
```

---

# Counting Results

Suppose you want to know how many buckets exist.

```bash
aws s3api list-buckets \
--query "length(Buckets)"
```

Example:

```text
5
```

---

Count EC2 instances:

```bash
aws ec2 describe-instances \
--query "length(Reservations)"
```

---

# Selecting the First Result

Example:

```bash
aws s3api list-buckets \
--query "Buckets[0].Name"
```

Output

```text
company-backups
```

---

# Sorting Results

Example:

```bash
aws s3api list-buckets \
--query "sort_by(Buckets,&CreationDate)"
```

Sort EC2 instances:

```bash
aws ec2 describe-instances \
--query "sort_by(Reservations[].Instances[],&LaunchTime)"
```

---

# Filtering by Value

Example:

Return only running instances.

```bash
aws ec2 describe-instances \
--query "Reservations[].Instances[?State.Name=='running']"
```

Retrieve only stopped instances:

```bash
aws ec2 describe-instances \
--query "Reservations[].Instances[?State.Name=='stopped']"
```

---

# Common JMESPath Functions

| Function | Description |
|-----------|-------------|
| length() | Count items |
| sort_by() | Sort objects |
| contains() | Search values |
| keys() | Return object keys |
| values() | Return object values |
| join() | Join strings |
| reverse() | Reverse a list |

---

# Using `--query` with Automation

Instead of parsing JSON manually:

```bash
INSTANCE_ID=$(aws ec2 describe-instances \
--query "Reservations[0].Instances[0].InstanceId" \
--output text)
```

Now use:

```bash
aws ec2 stop-instances \
--instance-ids $INSTANCE_ID
```

This approach is common in:

- Bash scripts
- GitHub Actions
- Jenkins
- GitLab CI
- Deployment automation

---

# Common Mistakes

## Forgetting Quotes

Incorrect

```bash
--query Reservations[*]
```

Correct

```bash
--query "Reservations[*]"
```

---

## Forgetting `--output text`

Sometimes the query returns JSON.

Example:

```bash
aws ec2 describe-instances \
--query "Reservations[*].Instances[*].InstanceId"
```

Better for scripting:

```bash
aws ec2 describe-instances \
--query "Reservations[*].Instances[*].InstanceId" \
--output text
```

---

## Using the Wrong JSON Path

Many users assume the response begins with:

```text
Instances
```

It actually begins with:

```text
Reservations
```

Understanding the JSON structure is essential before writing queries.

---

# Production Tips

- Always use `--query` in automation to reduce unnecessary output.
- Combine `--query` with `--output text` for shell scripting.
- Use `--output table` when presenting filtered data to humans.
- Test complex queries before integrating them into production scripts.
- Keep queries simple and readable for easier maintenance.

---

# Architecture Note

The `--query` option is applied **after** AWS returns the response.

```text
AWS Service
      │
      ▼
JSON Response
      │
      ▼
AWS CLI
      │
      ▼
Apply JMESPath Query
      │
      ▼
Format Output
```

This means `--query` does **not** reduce the amount of data transferred from AWS—it filters the response locally after it has been received.

---

# Interview Note

### Question

Why should you use `--query` instead of parsing JSON manually?

### Sample Answer

`--query` uses JMESPath to filter AWS API responses directly within the AWS CLI. It simplifies scripts, reduces post-processing, improves readability, and allows automation tools to work with only the required data instead of processing large JSON documents.

---

# Quick Reference

| Option | Purpose |
|---------|----------|
| `--region` | Override AWS Region |
| `--profile` | Select Named Profile |
| `--output` | Select output format |
| `--query` | Filter JSON output |
| `--debug` | Enable detailed logging |
| `--no-cli-pager` | Disable pager |
| `--cli-auto-prompt` | Interactive command builder |
| `--endpoint-url` | Use a custom endpoint |
| `--cli-read-timeout` | Read timeout |
| `--cli-connect-timeout` | Connection timeout |

---

# Chapter Summary

In this chapter, you learned:

- What global options are.
- How command-line options override configuration.
- When to use `--region`, `--profile`, and `--output`.
- How to use `--query` with JMESPath.
- Advanced options such as `--debug`, `--no-cli-pager`, and `--cli-auto-prompt`.
- Practical techniques for automation and troubleshooting.

These global options form the foundation of efficient AWS CLI usage and are applicable across nearly every AWS service.

---


# Senior-Level Deep Dives

---

## Pagination — The Hidden Trap in AWS CLI Automation

Many AWS APIs return paginated results. A junior engineer's script works fine with 5 buckets but silently misses 50 in production because the first page has a limit of 50 items by default.

### How Pagination Works

AWS APIs return a `NextToken` (or `NextMarker`, `Marker`, `ContinuationToken`) when more results exist. You must loop until no token is returned.

**Manual pagination — dangerous pattern**
```bash
# Only returns the first page — silently wrong in production
aws ec2 describe-instances \
  --query "Reservations[].Instances[].[InstanceId,State.Name]"
```

**Correct: use `--no-paginate` or the paginator**

`--no-paginate` tells the CLI to automatically iterate all pages and concatenate results:

```bash
aws ec2 describe-instances \
  --no-paginate \
  --query "Reservations[].Instances[].[InstanceId,State.Name]"
```

**Manual page loop (when you need per-page control)**
```bash
next_token=""
while true; do
  if [ -z "$next_token" ]; then
    result=$(aws ec2 describe-instances --output json)
  else
    result=$(aws ec2 describe-instances \
      --starting-token "$next_token" \
      --output json)
  fi

  echo "$result" | jq '.Reservations[].Instances[].InstanceId'

  next_token=$(echo "$result" | jq -r '.NextToken // empty')
  [ -z "$next_token" ] && break
done
```

### Page Size Control

```bash
aws ec2 describe-instances \
  --page-size 20 \
  --no-paginate
```

Reducing `--page-size` lowers API call latency per page (useful for services with aggressive throttling) while `--no-paginate` still fetches all results.

### Services That Commonly Trip Engineers

| Service | Paginator Token | Default Limit |
|---------|----------------|---------------|
| EC2 describe-instances | NextToken | 100 per page |
| S3 list-objects-v2 | ContinuationToken | 1000 per page |
| CloudWatch get-metric-data | NextToken | varies |
| IAM list-users | Marker | 100 per page |
| Lambda list-functions | Marker | 50 per page |
| CloudFormation list-stacks | NextToken | 100 per page |

---

## Advanced JMESPath — Production Patterns

### Flattening Nested Arrays

`Reservations[].Instances[]` (double `[]`) flattens nested arrays, while `Reservations[*].Instances[*]` preserves nesting:

```bash
# Returns [[["i-abc"]], [["i-def"]]] — nested
aws ec2 describe-instances \
  --query "Reservations[*].Instances[*].InstanceId"

# Returns ["i-abc", "i-def"] — flat array — better for scripting
aws ec2 describe-instances \
  --query "Reservations[].Instances[].InstanceId" \
  --output text
```

### Conditional Filtering

```bash
# Only running instances
aws ec2 describe-instances \
  --query "Reservations[].Instances[?State.Name=='running'].[InstanceId,InstanceType]" \
  --output table

# Only t3.micro instances
aws ec2 describe-instances \
  --query "Reservations[].Instances[?InstanceType=='t3.micro'].InstanceId" \
  --output text

# Instances with a specific tag value
aws ec2 describe-instances \
  --query "Reservations[].Instances[?Tags[?Key=='Environment' && Value=='production']].InstanceId" \
  --output text
```

### Multi-Field Extraction with Hash Projection

```bash
# Return objects (not arrays) with named keys
aws lambda list-functions \
  --query "Functions[*].{Name: FunctionName, Runtime: Runtime, Memory: MemorySize}" \
  --output table
```

### Sorting and Length

```bash
# Count running instances
aws ec2 describe-instances \
  --filters Name=instance-state-name,Values=running \
  --query "length(Reservations[].Instances[])"

# Sort S3 buckets by creation date
aws s3api list-buckets \
  --query "sort_by(Buckets, &CreationDate)[].Name" \
  --output text

# Get the newest bucket
aws s3api list-buckets \
  --query "sort_by(Buckets, &CreationDate)[-1].Name" \
  --output text
```

### Nested Attribute Access

```bash
# Get the root device name for all instances
aws ec2 describe-instances \
  --query "Reservations[].Instances[].RootDeviceName" \
  --output text

# Get security group names for all instances
aws ec2 describe-instances \
  --query "Reservations[].Instances[].SecurityGroups[].GroupName" \
  --output text
```

### Using `--query` in Shell Variable Assignment

This pattern appears throughout production deployment scripts:

```bash
# Single value assignment
LATEST_AMI=$(aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
  --query "sort_by(Images, &CreationDate)[-1].ImageId" \
  --output text)

# Multiple values in a loop
while IFS=$'\t' read -r id state; do
  echo "Instance: $id is $state"
done < <(aws ec2 describe-instances \
  --query "Reservations[].Instances[].[InstanceId,State.Name]" \
  --output text)
```

---

## Output Format Decision Matrix — Senior Engineer Perspective

| Scenario | Format | Why |
|----------|--------|-----|
| Shell variable assignment | `text` | No JSON parsing needed, direct assignment |
| Bash loop over resource IDs | `text` | One value per line, works with `while read` |
| Python/jq post-processing | `json` | Structured, composable |
| Human dashboard / terminal review | `table` | Scannable at a glance |
| IaC parameter file generation | `yaml` | Native YAML output |
| Audit log (append to file) | `json` | Complete, structured, searchable |
| API response debugging | `json` with `--debug` | Full response body visible |

---

## The `--cli-input-json` and `--generate-cli-skeleton` Pattern

For complex API calls, embedding parameters inline becomes unmanageable. The professional approach:

```bash
# Generate the skeleton
aws ec2 run-instances --generate-cli-skeleton input > launch-config.json
```

Edit `launch-config.json` with your values, then:

```bash
# Execute from file — version-controllable, reviewable
aws ec2 run-instances --cli-input-json file://launch-config.json
```

This pattern is essential for:
- Lambda function creation (30+ parameters)
- ECS task definitions
- CodeBuild project definitions
- Any operation with complex nested JSON

---

## `--dry-run` — Available for Destructive EC2 Operations

Many EC2 operations support `--dry-run`, which checks permissions without actually executing:

```bash
aws ec2 terminate-instances \
  --instance-ids i-0abc123 \
  --dry-run
```

Output if permissions are correct:
```
An error occurred (DryRunOperation): Request would have succeeded...
```

Output if missing permission:
```
An error occurred (UnauthorizedOperation): ...
```

Use this pattern in CI/CD preflight checks.

---

## Senior Interview Questions — Global Options & Output

**Q: In a CI/CD pipeline, your `aws ec2 describe-instances` command only returns 50 instances but you know there are 200. How do you fix this?**

The API is returning a paginated first page. Fix: add `--no-paginate` to the command, or implement a loop using `--starting-token` with the `NextToken` from each response. Note that `--no-paginate` with `--query` applies the JMESPath expression across all pages' merged results.

---

**Q: What is the difference between `--query "Reservations[*].Instances[*].InstanceId"` and `--query "Reservations[].Instances[].InstanceId"`?**

`[*]` is a wildcard projection that preserves list structure. `[]` is a flatten projection that collapses nested arrays. In practice:
- `[*]...[*]` returns `[["i-abc"], ["i-def"]]` — nested
- `[]...[]` returns `["i-abc", "i-def"]` — flat

For shell scripting and piping, the flat form combined with `--output text` is almost always what you want.

---

**Q: How do you use `--query` to extract a tag value when tags are represented as a list of key-value objects?**

```bash
aws ec2 describe-instances \
  --instance-ids i-0abc123 \
  --query "Reservations[].Instances[].Tags[?Key=='Name'].Value | [0]" \
  --output text
```

The `?` filter on the array finds the matching key, `.Value` extracts the value, and `| [0]` unwraps the single-element array.

---
