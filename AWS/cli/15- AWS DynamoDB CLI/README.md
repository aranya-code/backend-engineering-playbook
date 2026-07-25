# DynamoDB CLI

The AWS Command Line Interface (AWS CLI) is an indispensable tool for backend engineers, DevOps engineers, SREs, and cloud engineers working with Amazon DynamoDB. While SDKs such as **Boto3** are used inside applications, the CLI excels at infrastructure management, automation, production troubleshooting, CI/CD, disaster recovery, and operational maintenance.

This section provides a production-focused guide to managing DynamoDB entirely from the command line. Every chapter includes practical examples, real-world workflows, operational best practices, and interview-focused discussions.

---

# Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Introduction to DynamoDB CLI](./01-%20Introduction%20to%20DynamoDB%20CLI.md) | AWS CLI fundamentals, authentication, profiles, regions, output formats, JMESPath, and command structure |
| [02 - CRUD Operations](./02-%20CRUD%20Operations.md) | Create, Read, Update, Delete operations using the AWS CLI with production examples |
| [03 - Querying & Scanning](./03-%20Querying%20%26%20Scanning.md) | Query, Scan, filters, projections, pagination, sorting, and efficient data retrieval |
| [04 - Table Management](./04-%20Table%20Management.md) | Create tables, update configuration, billing modes, TTL, Streams, PITR, and lifecycle management |
| [05 - Backup, Restore & Export](./05-%20Backup,%20Restore%20%26%20Export.md) | On-demand backups, Point-in-Time Recovery, exports to Amazon S3, imports, and disaster recovery |
| [06 - Monitoring & Troubleshooting](./06-%20Monitoring%20%26%20Troubleshooting.md) | Health checks, capacity inspection, CloudWatch integration, debugging, and production troubleshooting |
| [07 - Automation & Scripting](./07-%20Automation%20%26%20Scripting.md) | Shell scripting, PowerShell, environment variables, CI/CD integration, and operational automation |
| [08 - Production CLI Recipes](./08-%20Production%20CLI%20Recipes.md) | Production-ready runbooks, deployment validation, operational scripts, and disaster recovery workflows |
| [09 - Interview Questions](./09-%20Interview%20Questions.md) | Senior-level interview questions covering DynamoDB CLI administration and production operations |

---

# Learning Path

```text
                    DynamoDB CLI

                           │

          ┌────────────────┼────────────────┐

          ▼                ▼                ▼

     CLI Basics       CRUD Operations     Querying

          │                │                │

          └────────────────┼────────────────┘

                           ▼

                  Table Management

                           │

          ┌────────────────┼────────────────┐

          ▼                ▼                ▼

     Backup & Restore   Monitoring     Automation

                           │

                           ▼

                Production Runbooks

                           │

                           ▼

                  Interview Preparation
```

---

# Skills You'll Gain

After completing this section, you'll be able to:

- Configure and authenticate the AWS CLI securely.
- Perform CRUD operations directly against DynamoDB.
- Query and scan tables efficiently.
- Create and manage DynamoDB tables.
- Configure billing modes, TTL, Streams, and Point-in-Time Recovery.
- Create and restore backups.
- Export and import DynamoDB data.
- Troubleshoot production issues using the CLI.
- Automate operational tasks using shell scripts and CI/CD pipelines.
- Build reusable operational runbooks for production environments.
- Answer senior-level DynamoDB CLI interview questions confidently.

---

# Production Topics Covered

This section emphasizes practical production workflows rather than isolated commands.

Topics include:

- AWS CLI authentication
- IAM profiles
- DynamoDB administration
- Table lifecycle management
- Billing mode configuration
- Global Secondary Index verification
- Time To Live (TTL)
- DynamoDB Streams
- Point-in-Time Recovery (PITR)
- Backup and restore automation
- Export to Amazon S3
- Infrastructure validation
- Deployment verification
- Health check automation
- CloudWatch-assisted troubleshooting
- Shell scripting
- GitHub Actions integration
- Disaster recovery runbooks
- Operational best practices

---

# Recommended Prerequisites

Before studying this section, you should already be familiar with:

- DynamoDB fundamentals
- Primary keys and data modeling
- Secondary indexes (GSIs and LSIs)
- Query and Scan concepts
- AWS Identity and Access Management (IAM)
- Basic terminal or command-line usage

Completing the **Python SDK (Boto3)** section first is recommended, as it explains the underlying DynamoDB APIs that the CLI invokes.

---

# Who Should Read This?

This section is intended for:

- Backend Engineers
- Python Developers
- Cloud Engineers
- DevOps Engineers
- Site Reliability Engineers (SREs)
- Platform Engineers
- AWS Solution Architects
- Engineers preparing for AWS or backend interviews

---

# Estimated Completion Time

| Experience | Estimated Time |
|------------|---------------:|
| Beginner | 8–10 hours |
| Intermediate | 5–6 hours |
| Experienced AWS Engineer | 2–3 hours |
| Interview Revision | 60–90 minutes |

---

# How to Use This Section

For the best learning experience:

1. Read each chapter sequentially.
2. Execute every CLI command in a sandbox or development AWS account.
3. Practice creating and deleting resources safely.
4. Build reusable shell scripts from the examples.
5. Integrate CLI commands into a sample CI/CD pipeline.
6. Review the production recipes before working on real AWS environments.
7. Finish with the interview questions to reinforce operational knowledge.

---

# Best Practices

- Use named AWS CLI profiles instead of hardcoded credentials.
- Prefer IAM Roles whenever possible.
- Test commands in development before production.
- Use JSON input files for complex requests.
- Validate table status before running administrative operations.
- Automate repetitive tasks using scripts and CI/CD.
- Keep operational scripts under version control.
- Enable Point-in-Time Recovery for production tables.
- Regularly test backup and restore procedures.

---
