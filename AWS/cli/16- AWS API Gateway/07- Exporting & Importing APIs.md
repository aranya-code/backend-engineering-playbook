# Exporting & Importing APIs

## Overview

As APIs grow in complexity, manually recreating them across environments becomes impractical.

Amazon API Gateway supports exporting and importing APIs using the **OpenAPI Specification**, allowing teams to:

- Backup APIs
- Version API definitions
- Move APIs between AWS accounts
- Promote APIs between environments
- Integrate APIs with CI/CD pipelines
- Manage APIs using Infrastructure as Code

Using the AWS CLI, these operations can be fully automated.

---

# Export & Import Workflow

```text
Development API

↓

Export OpenAPI

↓

Git Repository

↓

CI/CD

↓

Import

↓

Staging

↓

Production
```

This workflow ensures consistent API deployments across environments.

---

# Supported Formats

API Gateway supports:

```text
OpenAPI 2.0 (Swagger)
```

and

```text
OpenAPI 3.x
```

Export formats:

- JSON
- YAML

---

# Export a REST API (OpenAPI)

```bash
aws apigateway get-export \
    --rest-api-id abc123 \
    --stage-name prod \
    --export-type oas30 \
    api.json
```

This exports the deployed API to:

```text
api.json
```

---

# Export as YAML

```bash
aws apigateway get-export \
    --rest-api-id abc123 \
    --stage-name prod \
    --export-type oas30 \
    api.yaml
```

---

# Export Swagger 2.0

```bash
aws apigateway get-export \
    --rest-api-id abc123 \
    --stage-name prod \
    --export-type swagger \
    swagger.json
```

---

# Include Extensions

Include API Gateway extensions.

```bash
aws apigateway get-export \
    --rest-api-id abc123 \
    --stage-name prod \
    --export-type oas30 \
    --parameters extensions='integrations' \
    api.json
```

Extensions preserve:

- Lambda Integrations
- Authorizers
- API Gateway-specific configuration

---

# Import a New REST API

```bash
aws apigateway import-rest-api \
    --body file://api.json
```

Example output:

```json
{
    "id":"abc123",
    "name":"ProductAPI"
}
```

---

# Import from YAML

```bash
aws apigateway import-rest-api \
    --body file://api.yaml
```

---

# Overwrite an Existing API

Replace the existing API definition.

```bash
aws apigateway put-rest-api \
    --rest-api-id abc123 \
    --mode overwrite \
    --body file://api.json
```

---

# Merge with Existing API

Instead of replacing everything:

```bash
aws apigateway put-rest-api \
    --rest-api-id abc123 \
    --mode merge \
    --body file://api.json
```

Useful when adding new resources.

---

# Create Deployment After Import

Imported APIs are not immediately available.

Deploy:

```bash
aws apigateway create-deployment \
    --rest-api-id abc123 \
    --stage-name prod
```

---

# Verify Import

List resources.

```bash
aws apigateway get-resources \
    --rest-api-id abc123
```

Example:

```text
/

↓

/products

↓

/orders
```

---

# View API Details

```bash
aws apigateway get-rest-api \
    --rest-api-id abc123
```

---

# Backup API

Export the API before major changes.

```bash
aws apigateway get-export \
    --rest-api-id abc123 \
    --stage-name prod \
    --export-type oas30 \
    backup.json
```

Store backups in:

- Git
- Amazon S3
- Artifact Repository

---

# Restore from Backup

```bash
aws apigateway put-rest-api \
    --rest-api-id abc123 \
    --mode overwrite \
    --body file://backup.json
```

Redeploy:

```bash
aws apigateway create-deployment \
    --rest-api-id abc123 \
    --stage-name prod
```

---

# Migrate Between AWS Accounts

Workflow:

```text
Account A

↓

Export API

↓

OpenAPI File

↓

Import

↓

Account B
```

No manual recreation is required.

---

# CI/CD Workflow

```text
Developer

↓

Git Commit

↓

OpenAPI

↓

GitHub Actions

↓

AWS CLI

↓

Import API

↓

Deploy

↓

Production
```

The API definition becomes version-controlled.

---

# Version Control

Store:

```text
api-v1.yaml

api-v2.yaml

api-v3.yaml
```

This enables:

- Rollbacks
- Code Reviews
- Change Tracking

---

# Export Architecture

```text
REST API

↓

OpenAPI File

↓

Git Repository

↓

Pipeline

↓

AWS
```

---

# Import Architecture

```text
OpenAPI

↓

API Gateway

↓

Deployment

↓

Stage

↓

Clients
```

---

# Automation Example

Export:

```bash
API_ID=abc123

aws apigateway get-export \
--rest-api-id $API_ID \
--stage-name prod \
--export-type oas30 \
api.yaml
```

Import:

```bash
aws apigateway import-rest-api \
--body file://api.yaml
```

---

# Common Errors

## Invalid OpenAPI File

Verify:

- JSON syntax
- YAML syntax
- OpenAPI version

Use an OpenAPI validator before importing.

---

## Unsupported Extension

Some API Gateway extensions are only valid for REST APIs.

Review:

```text
x-amazon-apigateway-*
```

extensions.

---

## Import Failed

Verify:

- File path
- IAM permissions
- OpenAPI specification

---

## Changes Not Visible

Always create a deployment after importing or updating an API.

```bash
aws apigateway create-deployment \
--rest-api-id abc123 \
--stage-name prod
```

---

# CLI Best Practices

- Store API definitions in Git.
- Export APIs before making production changes.
- Use OpenAPI 3 whenever possible.
- Validate specifications before importing.
- Automate exports and imports in CI/CD pipelines.
- Deploy immediately after a successful import.
- Treat API definitions as source code.

---

# Common Interview Questions

### Why export an API?

Exporting creates a portable OpenAPI definition that can be backed up, version-controlled, reviewed, or deployed to another environment.

---

### What is the difference between `import-rest-api` and `put-rest-api`?

`import-rest-api` creates a **new API** from an OpenAPI definition.

`put-rest-api` updates an **existing API**, either by replacing it (`overwrite`) or merging changes (`merge`).

---

### Why use OpenAPI with API Gateway?

OpenAPI provides a standard, language-independent way to describe APIs, making documentation, automation, testing, and deployment significantly easier.

---

### Why deploy after importing an API?

Importing updates the API configuration but does not automatically publish it. A deployment is required before clients can access the updated API.

---

### Why store OpenAPI files in Git?

Version control enables code reviews, rollback, auditing, collaboration, and automated deployments, treating API definitions like application source code.

---

# Key Takeaways

- API Gateway supports exporting and importing APIs using the OpenAPI Specification.
- Exported API definitions can be version-controlled, backed up, and reused across environments.
- `import-rest-api` creates new APIs, while `put-rest-api` updates existing ones.
- OpenAPI enables consistent CI/CD workflows and Infrastructure as Code practices.
- Treating API definitions as source code improves maintainability, collaboration, and deployment reliability.