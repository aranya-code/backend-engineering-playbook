# CloudFormation Custom Resources

## What are Custom Resources?

Custom Resources allow CloudFormation to perform actions that are not natively supported by CloudFormation resource types.

They extend CloudFormation's capabilities beyond built-in AWS resources.

Think of Custom Resources as:

```text
CloudFormation Extensions
```

that execute custom code during stack operations.

---

# Why Do We Need Custom Resources?

CloudFormation supports hundreds of AWS resource types.

Example:

```text
EC2
S3
RDS
IAM
Lambda
VPC
```

However, sometimes we need tasks such as:

```text
Generate Passwords
Call External APIs
Register DNS Records
Create Third-Party Resources
Run Custom Validation
```

CloudFormation cannot perform these directly.

Custom Resources solve this problem.

---

# Common Use Cases

## Password Generation

Generate secure passwords during deployment.

---

## DNS Registration

Register records in external DNS providers.

---

## Third-Party Integrations

Provision:

```text
Datadog
PagerDuty
MongoDB Atlas
Cloudflare
```

resources.

---

## Custom Configuration

Perform post-deployment configuration.

---

## Dynamic Values

Fetch values from:

```text
External API
Database
Internal Service
```

during deployment.

---

# How Custom Resources Work

```text
CloudFormation
      │
      ▼
Custom Resource
      │
      ▼
Lambda Function
      │
      ▼
Custom Logic
      │
      ▼
Response to CloudFormation
```

---

# Architecture

```text
Stack Operation
       │
       ▼
CloudFormation
       │
       ▼
Custom Resource
       │
       ▼
Lambda Function
       │
       ▼
AWS API
External API
Database
Custom Logic
```

---

# Lifecycle Events

CloudFormation sends events during:

```text
Create
Update
Delete
```

operations.

---

# Event Flow

```text
Stack Create
      │
      ▼
CREATE Event
      │
      ▼
Lambda Executes
      │
      ▼
SUCCESS / FAILED
```

---

# Resource Types

Custom Resources use:

```yaml
Type: Custom::ResourceName
```

or

```yaml
Type: AWS::CloudFormation::CustomResource
```

---

# Example

```yaml
Resources:

  GeneratePassword:

    Type: Custom::PasswordGenerator

    Properties:

      ServiceToken:
        !GetAtt PasswordLambda.Arn
```

---

# ServiceToken

The most important property.

ServiceToken tells CloudFormation which Lambda function should process the request.

Example:

```yaml
ServiceToken:
  !GetAtt MyCustomLambda.Arn
```

---

# Complete Example

## Lambda Function

```python
def lambda_handler(event, context):

    request_type = event['RequestType']

    if request_type == 'Create':
        print("Creating Resource")

    elif request_type == 'Update':
        print("Updating Resource")

    elif request_type == 'Delete':
        print("Deleting Resource")
```

---

## CloudFormation Template

```yaml
Resources:

  CustomTask:

    Type: Custom::DemoTask

    Properties:

      ServiceToken:
        !GetAtt DemoLambda.Arn
```

---

# CloudFormation Events

CloudFormation sends JSON events.

Example:

```json
{
  "RequestType": "Create",
  "ResponseURL": "...",
  "StackId": "...",
  "RequestId": "...",
  "LogicalResourceId": "CustomTask"
}
```

---

# Request Types

CloudFormation sends three request types.

---

## Create

Triggered during:

```text
Stack Creation
```

Event:

```json
{
  "RequestType": "Create"
}
```

---

## Update

Triggered during:

```text
Stack Update
```

Event:

```json
{
  "RequestType": "Update"
}
```

---

## Delete

Triggered during:

```text
Stack Deletion
```

Event:

```json
{
  "RequestType": "Delete"
}
```

---

# Lambda Response Requirement

Lambda must respond back to CloudFormation.

Otherwise:

```text
Stack Hangs
```

and eventually fails.

---

# Response Types

## SUCCESS

```json
{
  "Status": "SUCCESS"
}
```

CloudFormation continues deployment.

---

## FAILED

```json
{
  "Status": "FAILED"
}
```

CloudFormation triggers rollback.

---

# PhysicalResourceId

Custom Resources return:

```text
PhysicalResourceId
```

Example:

```json
{
  "PhysicalResourceId":
  "PasswordGenerator-001"
}
```

CloudFormation tracks the resource using this ID.

---

# Returning Data

Custom Resources can return values.

Example:

```json
{
  "Status": "SUCCESS",

  "Data": {
    "Password": "MySecret123!"
  }
}
```

---

# Accessing Returned Data

Template:

```yaml
Resources:

  GeneratePassword:

    Type: Custom::PasswordGenerator
```

Output:

```yaml
Outputs:

  Password:

    Value:
      !GetAtt GeneratePassword.Password
```

Result:

```text
MySecret123!
```

---

# Example: Random Password Generator

## Lambda

```python
import random
import string

password = ''.join(
    random.choice(
        string.ascii_letters
    ) for _ in range(12)
)
```

Returns:

```text
AbC123XyZ789
```

---

## CloudFormation

```yaml
Resources:

  RandomPassword:

    Type: Custom::PasswordGenerator

    Properties:

      ServiceToken:
        !GetAtt PasswordLambda.Arn
```

---

# Example: External API Call

Lambda:

```python
import requests

response = requests.get(
    "https://api.example.com/config"
)
```

Returns configuration to CloudFormation.

---

# Example: Route53 Registration

CloudFormation:

```text
Create EC2
      │
      ▼
Custom Resource
      │
      ▼
Register DNS Entry
```

---

# Custom Resource Lifecycle

```text
Create Stack
      │
      ▼
Create Event
      │
      ▼
Lambda Executes
      │
      ▼
Success
```

Update:

```text
Update Stack
      │
      ▼
Update Event
```

Delete:

```text
Delete Stack
      │
      ▼
Delete Event
```

---

# Failure Handling

If Lambda returns:

```json
{
  "Status": "FAILED"
}
```

CloudFormation:

```text
CREATE_FAILED
```

or

```text
UPDATE_FAILED
```

and may trigger rollback.

---

# Logging

All Lambda execution logs appear in:

```text
CloudWatch Logs
```

Useful for troubleshooting.

---

# Example Troubleshooting Flow

```text
Custom Resource Failed
         │
         ▼
CloudFormation Events
         │
         ▼
Lambda Logs
         │
         ▼
Root Cause
```

---

# Custom Resource vs Lambda-backed Resource

Most Custom Resources today are:

```text
Lambda-backed Custom Resources
```

because Lambda is serverless and easy to integrate.

---

# AWS::CloudFormation::CustomResource

Alternative syntax:

```yaml
Resources:

  DemoResource:

    Type:
      AWS::CloudFormation::CustomResource

    Properties:

      ServiceToken:
        !GetAtt DemoLambda.Arn
```

Functionally identical.

---

# Real-World Enterprise Examples

## Security

```text
Generate Secrets
Rotate Keys
Register Certificates
```

---

## Networking

```text
Register DNS Records
Configure Firewalls
Update IP Whitelists
```

---

## Monitoring

```text
Create Datadog Monitors
Create PagerDuty Alerts
```

---

## SaaS Integration

```text
Cloudflare
MongoDB Atlas
Snowflake
ServiceNow
```

---

# Benefits

## Extends CloudFormation

Not limited to native AWS resources.

---

## Automation

Custom tasks become part of deployment.

---

## Reusability

Can be reused across multiple templates.

---

## Consistency

Custom logic runs consistently during deployments.

---

# Limitations

## Lambda Timeout

Default Lambda timeout may be insufficient.

---

## Additional Complexity

Requires:

```text
Lambda
IAM Roles
Error Handling
Logging
```

---

## Failure Impacts Stack

Custom Resource failures can fail entire deployments.

---

# Best Practices

## Keep Functions Idempotent

Running multiple times should not cause issues.

---

## Handle Create Update Delete Separately

Example:

```python
if request_type == "Create":
```

```python
if request_type == "Update":
```

```python
if request_type == "Delete":
```

---

## Return Proper Responses

Always return:

```text
SUCCESS
```

or

```text
FAILED
```

---

## Use CloudWatch Logs

Log everything.

---

## Implement Error Handling

Prevent unexpected stack failures.

---

# Common Mistakes

## Missing ServiceToken

CloudFormation cannot invoke Lambda.

---

## Not Sending Response

Stack remains stuck until timeout.

---

## Ignoring Delete Events

Resources may remain orphaned.

---

## Hardcoding Values

Use parameters and outputs instead.

---

# Key Takeaways

* Custom Resources extend CloudFormation beyond built-in resource types.
* Usually implemented using Lambda-backed Custom Resources.
* CloudFormation sends:

  * Create
  * Update
  * Delete
    events.
* ServiceToken identifies the Lambda handler.
* Lambda must return SUCCESS or FAILED.
* Custom Resources can return values to CloudFormation.
* Commonly used for external integrations and advanced automation.
* Widely used in enterprise CloudFormation deployments.

---

# Interview Questions

### What is a Custom Resource?

A Custom Resource is a CloudFormation extension that performs actions not supported by native resource types.

---

### What is a ServiceToken?

The ARN of the Lambda function (or service endpoint) that handles the Custom Resource request.

---

### Which request types does CloudFormation send?

* Create
* Update
* Delete

---

### What happens if a Custom Resource returns FAILED?

CloudFormation marks the operation as failed and may trigger rollback.

---

### Can Custom Resources return values?

Yes.

Returned values can be accessed using:

```yaml
!GetAtt
```

---

### Where are Custom Resource logs stored?

```text
CloudWatch Logs
```

---

### What is the most common implementation of a Custom Resource?

```text
Lambda-backed Custom Resource
```
