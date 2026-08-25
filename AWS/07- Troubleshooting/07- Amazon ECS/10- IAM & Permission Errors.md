# IAM & Permission Errors

AWS Identity and Access Management (IAM) is one of the most critical components of Amazon ECS. Incorrect IAM configuration can prevent tasks from pulling container images, accessing AWS services, retrieving secrets, writing logs, or even starting successfully.

IAM-related problems often appear as **AccessDeniedException**, **UnauthorizedOperation**, or **Access Denied** errors. Understanding which IAM role is being used at each stage of the ECS lifecycle is essential for effective troubleshooting.

---

# Typical Symptoms

You may observe one or more of the following:

- Cannot pull Docker image.
- Cannot access Amazon S3.
- Cannot retrieve secrets.
- CloudWatch logs are missing.
- Database credentials cannot be loaded.
- ECS tasks fail during startup.
- AccessDeniedException errors.

Example

```
Application

↓

AccessDeniedException

↓

Request Failed
```

---

# IAM Roles Used by ECS

Amazon ECS commonly uses three IAM roles.

| IAM Role | Purpose |
|----------|---------|
| Task Execution Role | Used by ECS to pull images, retrieve secrets, and send logs |
| Task Role | Used by the application running inside the container |
| ECS Service-Linked Role | Used by ECS to manage AWS resources on your behalf |

Understanding which role is responsible for an operation is the first step in troubleshooting.

---

# Troubleshooting Workflow

```
Permission Error

        │

        ▼

Error Message

        │

        ▼

Identify IAM Role

        │

        ▼

IAM Policy

        │

        ▼

Resource Policy

        │

        ▼

CloudTrail Logs

        │

        ▼

Root Cause
```

---

# Step 1: Identify the Error

Typical IAM errors include:

```
AccessDeniedException
```

```
UnauthorizedOperation
```

```
Access Denied
```

```
User is not authorized
```

Read the full error message carefully.

It usually identifies:

- AWS service
- API operation
- Missing permission

---

# Step 2: Determine Which IAM Role Is Being Used

This is the most important troubleshooting step.

Ask:

Who is making the request?

Possible answers:

- ECS Agent
- ECS Task
- Application
- ECS Service

---

### Example

```
Application

↓

Amazon S3
```

Uses

```
Task Role
```

---

Example

```
Amazon ECS

↓

Amazon ECR
```

Uses

```
Execution Role
```

---

# Step 3: Review IAM Policies

Verify the required actions are allowed.

Example

```
s3:GetObject
```

```
s3:PutObject
```

```
dynamodb:GetItem
```

```
secretsmanager:GetSecretValue
```

Check both:

- Allowed Actions
- Resource ARNs

---

# Step 4: Verify Resource Policies

Some AWS services also use resource-based policies.

Examples

- Amazon S3 Bucket Policy
- Amazon ECR Repository Policy
- AWS KMS Key Policy
- Amazon SNS Topic Policy
- Amazon SQS Queue Policy

Both the IAM policy and the resource policy must allow the operation.

---

# Step 5: Review CloudTrail Logs

CloudTrail records every AWS API call.

Search for:

```
AccessDenied
```

Review:

- API called
- IAM principal
- Resource
- Error message

CloudTrail is often the fastest way to identify permission problems.

---

# Common Permission Problems

---

# Task Cannot Pull Docker Image

Symptoms

```
CannotPullContainerError
```

Possible causes

- Missing Execution Role
- Missing ECR permissions
- Repository policy

Required permissions include

```
ecr:GetAuthorizationToken

ecr:BatchGetImage

ecr:GetDownloadUrlForLayer
```

---

# Application Cannot Access Amazon S3

Symptoms

```
AccessDeniedException
```

Verify

- Task Role
- Bucket Policy
- Object permissions

---

# Application Cannot Access DynamoDB

Verify

```
dynamodb:GetItem
```

```
dynamodb:PutItem
```

```
dynamodb:UpdateItem
```

Review:

- IAM policy
- Table ARN
- Region

---

# Application Cannot Retrieve Secrets

Example

```
AccessDeniedException

Secrets Manager
```

Verify

```
secretsmanager:GetSecretValue
```

Also verify the KMS permissions if the secret is encrypted with a customer-managed key.

---

# CloudWatch Logs Missing

CloudWatch logging requires the Execution Role.

Typical permissions include

```
logs:CreateLogStream
```

```
logs:PutLogEvents
```

Without these permissions, logs are never written.

---

# KMS Permission Errors

Applications may fail while decrypting:

- Secrets
- Parameters
- Encrypted S3 objects

Verify

```
kms:Decrypt
```

Also verify the KMS Key Policy.

---

# Cross-Account Access

If ECS accesses resources in another AWS account, verify:

- IAM Role
- Trust Relationship
- Resource Policy

Cross-account access requires permissions on both sides.

---

# Least Privilege

Follow the Principle of Least Privilege.

Avoid

```
Action

*

Resource

*
```

Instead grant only the required permissions.

Example

```
s3:GetObject

Specific Bucket
```

---

# Common Root Causes

| Problem | Solution |
|----------|----------|
| Missing Task Role | Attach correct Task Role |
| Missing Execution Role | Configure Execution Role |
| Missing IAM Action | Update IAM policy |
| Incorrect Resource ARN | Correct the ARN |
| Missing Bucket Policy | Update S3 policy |
| Missing Repository Policy | Update ECR policy |
| Missing KMS permission | Add `kms:Decrypt` |
| Cross-account access denied | Configure trust relationship and resource policy |

---

# Diagnostic Checklist

Before changing IAM policies, verify:

- Correct IAM role identified.
- IAM policy reviewed.
- Resource policy reviewed.
- Resource ARN correct.
- AWS Region correct.
- CloudTrail reviewed.
- Execution Role configured.
- Task Role configured.
- Required API actions allowed.
- KMS permissions verified.

---

# Best Practices

- Follow the Principle of Least Privilege.
- Separate Task Role and Execution Role responsibilities.
- Never use AdministratorAccess for ECS tasks.
- Use IAM roles instead of long-lived AWS credentials.
- Store secrets in AWS Secrets Manager.
- Enable CloudTrail for auditing.
- Review IAM policies regularly.
- Use IAM Access Analyzer to identify overly permissive policies.

---

# Interview Questions

### What is the difference between the Task Role and the Task Execution Role?

| Task Role | Execution Role |
|------------|----------------|
| Used by the application | Used by Amazon ECS |
| Runtime AWS access | Startup AWS access |
| Accesses S3, DynamoDB, SNS, SQS | Pulls images, retrieves secrets, sends logs |

---

### Why would an ECS task receive an AccessDeniedException?

Possible reasons include:

- Missing IAM permissions
- Incorrect Resource ARN
- Bucket Policy
- KMS permissions
- Cross-account access
- Wrong IAM role

---

### Which IAM role pulls images from Amazon ECR?

The **Task Execution Role**.

---

### Which IAM role should access Amazon S3?

The **Task Role**.

---

### How would you troubleshoot an IAM issue?

Recommended order:

1. Read the complete error message.
2. Identify which IAM role is being used.
3. Review the IAM policy.
4. Review the resource policy.
5. Check CloudTrail logs.
6. Verify the requested API action.
7. Confirm the Resource ARN.

---

# Key Takeaways

- IAM permission errors are one of the most common causes of ECS deployment and runtime failures.
- Correctly identifying whether the Task Role or Task Execution Role is responsible for the operation is the most important troubleshooting step.
- IAM policies, resource-based policies, and KMS permissions must all be considered when diagnosing access issues.
- CloudTrail provides valuable visibility into failed API calls and should be part of every IAM troubleshooting workflow.
- Applying the Principle of Least Privilege improves security while ensuring ECS applications have only the permissions they require.