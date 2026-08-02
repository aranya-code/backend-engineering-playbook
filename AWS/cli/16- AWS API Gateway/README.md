# AWS CLI

The **AWS CLI** section provides a practical reference for managing **Amazon API Gateway** directly from the command line.

While the AWS Management Console is convenient for learning and manual configuration, production environments typically rely on **automation** through the AWS CLI, Infrastructure as Code (CloudFormation, CDK, Terraform), and CI/CD pipelines.

These notes focus on the AWS CLI commands that backend engineers and DevOps teams commonly use to create, configure, secure, deploy, and maintain APIs at scale.

By the end of this section, you'll be comfortable performing most day-to-day API Gateway administrative tasks without opening the AWS Console.

---

# Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - AWS CLI Basics](./01-%20AWS%20CLI%20Basics.md) | Install, configure, and use the AWS CLI with API Gateway. Learn profiles, regions, output formats, and the differences between `apigateway` and `apigatewayv2`. |
| [02 - Creating APIs](./02-%20Creating%20APIs.md) | Create REST APIs, HTTP APIs, WebSocket APIs, routes, resources, and integrations using AWS CLI commands. |
| [03 - Managing Resources](./03-%20Managing%20Resources.md) | Manage API resources, methods, Lambda integrations, models, request validation, and resource hierarchies. |
| [04 - Deployments & Stages](./04-%20Deployments%20%26%20Stages.md) | Automate deployments, manage stages, enable logging, tracing, throttling, caching, and stage variables. |
| [05 - Security & Authorizers](./05-%20Security%20%26%20Authorizers.md) | Configure IAM, Cognito, JWT Authorizers, Lambda Authorizers, Resource Policies, and API security using the CLI. |
| [06 - Usage Plans & API Keys](./06-%20Usage%20Plans%20%26%20API%20Keys.md) | Create API Keys, Usage Plans, quotas, throttling rules, and manage API consumers. |
| [07 - Exporting & Importing APIs](./07-%20Exporting%20%26%20Importing%20APIs.md) | Export APIs as OpenAPI specifications, import APIs, migrate environments, and automate deployments. |

---

# Learning Path

```text
AWS CLI Setup

        │

        ▼

Create APIs

        │

        ▼

Manage Resources

        │

        ▼

Deploy APIs

        │

        ▼

Secure APIs

        │

        ▼

Manage Consumers

        │

        ▼

Export & Import APIs
```

This progression reflects the typical lifecycle of administering API Gateway using the AWS CLI.

---

# CLI Workflow

```text
AWS CLI

      │

      ▼

Create API

      │

      ▼

Configure Resources

      │

      ▼

Configure Security

      │

      ▼

Deploy

      │

      ▼

Manage Usage

      │

      ▼

Export / Import
```

The CLI enables complete automation of API Gateway operations.

---

# AWS CLI Namespaces

Amazon API Gateway provides two CLI namespaces.

| Namespace | Purpose |
|-----------|---------|
| `aws apigateway` | REST APIs |
| `aws apigatewayv2` | HTTP APIs and WebSocket APIs |

Knowing which namespace to use is essential when writing scripts or automation.

---

# What You'll Learn

After completing this section, you'll be able to:

## Configure AWS CLI

- Install AWS CLI
- Configure credentials
- Manage multiple AWS profiles
- Work with AWS regions
- Use JMESPath queries
- Generate CLI skeletons

---

## Create APIs

Build APIs directly from the command line.

You'll learn how to:

- Create REST APIs
- Create HTTP APIs
- Create WebSocket APIs
- Create routes
- Create resources
- Configure integrations

---

## Manage API Resources

Perform operations such as:

- Create resources
- Configure HTTP methods
- Attach Lambda integrations
- Configure request models
- Enable request validation
- Delete resources

---

## Deploy APIs

Automate deployments by:

- Creating deployments
- Managing stages
- Configuring stage variables
- Enabling CloudWatch Logs
- Enabling CloudWatch Metrics
- Enabling AWS X-Ray
- Configuring throttling and caching

---

## Secure APIs

Configure production security using:

- IAM Authorization
- Cognito User Pools
- JWT Authorizers
- Lambda Authorizers
- Resource Policies
- Lambda Permissions

---

## Manage API Consumers

Implement client management through:

- API Keys
- Usage Plans
- Request Quotas
- Rate Limiting
- Usage Reporting

---

## Migrate APIs

Learn how to:

- Export OpenAPI definitions
- Import APIs
- Update existing APIs
- Backup APIs
- Restore APIs
- Promote APIs across environments

---

# Automation Workflow

```text
Developer

      │

      ▼

GitHub Actions

      │

      ▼

AWS CLI

      │

      ▼

API Gateway

      │

      ▼

Production
```

The AWS CLI plays an important role in deployment automation and operational tooling.

---

# Typical Production Workflow

```text
Create API

      │

      ▼

Configure Resources

      │

      ▼

Configure Security

      │

      ▼

Deploy

      │

      ▼

Test

      │

      ▼

Promote

      │

      ▼

Production
```

This workflow is commonly automated using CI/CD pipelines.

---

# Best Practices

When using the AWS CLI with API Gateway:

- Use named AWS profiles for multiple environments.
- Store credentials securely.
- Prefer OpenAPI for API definitions.
- Automate repetitive tasks using shell scripts or PowerShell.
- Enable logging and monitoring during deployments.
- Use Infrastructure as Code for long-term infrastructure management.
- Validate API definitions before importing.
- Version API specifications in Git.
- Test commands in non-production environments first.

---

# CLI vs Infrastructure as Code

| AWS CLI | Infrastructure as Code |
|----------|------------------------|
| Operational tasks | Resource provisioning |
| Quick automation | Repeatable deployments |
| Troubleshooting | Version-controlled infrastructure |
| Scripting | Long-term infrastructure management |
| Day-to-day administration | Environment consistency |

In practice, engineering teams use **both** together:

- Infrastructure as Code provisions the infrastructure.
- AWS CLI performs operational and automation tasks.

---

# Where the CLI Fits

```text
Infrastructure as Code

        │

        ▼

AWS CLI

        │

        ▼

Amazon API Gateway

        │

        ▼

Applications
```

The CLI complements Infrastructure as Code rather than replacing it.

---

# Final Outcome

After completing this section, you'll be able to confidently manage Amazon API Gateway entirely from the command line.

You'll understand how to automate API creation, deployments, security configuration, client management, and API migration, making the AWS CLI a powerful addition to your backend engineering and DevOps toolkit.