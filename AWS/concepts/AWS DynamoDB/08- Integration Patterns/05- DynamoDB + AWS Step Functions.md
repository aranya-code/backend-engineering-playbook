# 05 - DynamoDB + AWS Step Functions

## Overview

While Amazon SQS, SNS, and EventBridge help applications communicate asynchronously, they do not orchestrate complex business workflows.

AWS Step Functions solves this problem by coordinating multiple services into a reliable workflow with built-in:

- State management
- Error handling
- Retries
- Timeouts
- Parallel execution
- Conditional branching
- Human approvals
- Long-running processes

When combined with DynamoDB, Step Functions enables resilient business processes where data is stored in DynamoDB and workflow execution is managed by Step Functions.

This combination is widely used for:

- Order processing
- Loan approval systems
- Insurance claims
- User onboarding
- Payment workflows
- Inventory management
- Long-running business processes

---

# Learning Objectives

After completing this chapter, you'll understand:

- Why integrate DynamoDB with Step Functions
- Workflow orchestration
- State machines
- Sequential workflows
- Parallel execution
- Error handling
- Saga Pattern
- Production architectures
- Best practices
- Interview questions

---

# Why Step Functions?

Imagine an e-commerce checkout.

Without orchestration:

```text
Create Order

↓

Reserve Inventory

↓

Charge Payment

↓

Create Shipment

↓

Send Email
```

If payment fails...

Who rolls back inventory?

Who marks the order as failed?

Who retries?

This logic quickly becomes difficult to maintain.

---

With Step Functions:

```text
Start Workflow

↓

Reserve Inventory

↓

Charge Payment

↓

Create Shipment

↓

Notify Customer

↓

Complete
```

The workflow itself manages failures and recovery.

---

# High-Level Architecture

```text
                 Client

                    │

                    ▼

              API Gateway

                    │

                    ▼

                AWS Lambda

                    │

                    ▼

             AWS Step Functions

        ┌───────────┼────────────┐

        ▼           ▼            ▼

   DynamoDB     Payment API   SNS/SQS
```

---

# State Machine

Every Step Functions workflow is a **State Machine**.

```text
Start

↓

Validate Order

↓

Save Order

↓

Charge Customer

↓

Reserve Inventory

↓

Ship Product

↓

Finish
```

Each step is called a **State**.

---

# Common Use Cases

Step Functions + DynamoDB are commonly used for:

- Order management
- Payment workflows
- User onboarding
- Insurance claims
- Loan approval
- Ticket booking
- Multi-step approvals
- Data processing pipelines

---

# Pattern 1 — Order Processing

```text
Order Submitted

↓

Save Order

↓

DynamoDB

↓

Charge Payment

↓

Reserve Inventory

↓

Create Shipment

↓

Update Order Status
```

Each stage executes independently.

---

# Pattern 2 — User Registration

```text
Create User

↓

Save User

↓

Verify Email

↓

Create Profile

↓

Provision Resources

↓

Send Welcome Email
```

Failures automatically stop the workflow.

---

# Pattern 3 — Document Approval

```text
Upload Document

↓

Save Metadata

↓

Human Approval

↓

Approved?

↓

YES

↓

Continue

────────────

NO

↓

Reject
```

Step Functions supports long-running workflows that may pause for hours or days.

---

# DynamoDB Inside Workflows

Step Functions can interact with DynamoDB directly using AWS SDK integrations or invoke Lambda functions that access DynamoDB.

Typical operations:

```text
PutItem

↓

UpdateItem

↓

GetItem

↓

DeleteItem

↓

Query
```

This allows workflows to persist state throughout execution.

---

# Sequential Workflow

```text
State 1

↓

State 2

↓

State 3

↓

State 4
```

Every state waits for the previous one.

---

# Parallel Workflow

Some operations are independent.

```text
Create Order

↓

Parallel

├── Notify Warehouse

├── Generate Invoice

└── Update Analytics
```

Parallel execution reduces total workflow time.

---

# Choice States

Business decisions can be modeled explicitly.

```text
Payment Successful?

↓

YES

↓

Ship Order

────────────

NO

↓

Cancel Order
```

This removes complex branching logic from application code.

---

# Retry Policies

Temporary failures should not immediately terminate the workflow.

```text
Payment API

↓

Timeout

↓

Retry

↓

Retry

↓

Success
```

Step Functions supports configurable retry strategies.

---

# Error Handling

```text
Inventory Failed

↓

Catch Error

↓

Rollback Payment

↓

Update Order

↓

Notify Customer
```

Failures are handled declaratively rather than with deeply nested application code.

---

# Saga Pattern

Distributed transactions are difficult across multiple services.

Instead of ACID transactions, use compensating actions.

```text
Reserve Inventory

↓

Charge Payment

↓

Shipment Failed

↓

Refund Payment

↓

Release Inventory
```

This is known as the **Saga Pattern**.

---

# Workflow Monitoring

Monitor:

- Execution success
- Failed executions
- Retry count
- State duration
- Total execution time

CloudWatch automatically publishes workflow metrics.

---

# Production Architecture

```text
                  Users

                     │

               API Gateway

                     │

                     ▼

                 AWS Lambda

                     │

                     ▼

              Step Functions

        ┌────────────┼────────────┐

        ▼            ▼            ▼

   DynamoDB     Payment API    SNS

        │

        ▼

   CloudWatch Logs
```

---

# Performance Considerations

For production systems:

- Keep workflows focused on business logic.
- Minimize unnecessary state transitions.
- Execute independent tasks in parallel.
- Store workflow data in DynamoDB.
- Design workflows to resume safely after retries.

---

# Security Best Practices

- Apply least-privilege IAM roles.
- Encrypt DynamoDB using AWS KMS.
- Restrict Step Functions permissions.
- Enable CloudTrail auditing.
- Avoid storing secrets in workflow input.
- Use AWS Secrets Manager for credentials.

---

# Best Practices

- Keep workflows small and modular.
- Store workflow state in DynamoDB where appropriate.
- Use Choice states instead of application branching.
- Configure retries for transient failures.
- Use Catch blocks for recovery.
- Prefer parallel execution for independent tasks.
- Design compensating actions for distributed workflows.
- Monitor execution metrics continuously.

---

# Common Mistakes

## Putting Business Logic Inside Lambda

Poor:

```text
Lambda

↓

2000 Lines

↓

Workflow Logic
```

Better:

```text
Step Functions

↓

Workflow

↓

Small Lambda Functions
```

---

## No Retry Strategy

Transient failures are common.

Always configure retries for network calls and external services.

---

## Ignoring Compensation

Distributed systems require rollback strategies.

Use Saga instead of assuming distributed transactions.

---

## Long-Running Lambda Functions

Do not keep Lambda functions running while waiting for external events.

Use Step Functions to coordinate long-running workflows.

---

# Production Considerations

Enterprise architectures commonly integrate:

```text
DynamoDB

↓

Step Functions

↓

Lambda

↓

SNS

↓

SQS

↓

EventBridge

↓

CloudWatch

↓

AWS X-Ray
```

This enables scalable orchestration with full observability and fault tolerance.

---

# Interview Notes

A common interview question is:

> **Why use Step Functions with DynamoDB?**

Step Functions orchestrate multi-step business workflows while DynamoDB stores application state. Together they enable reliable, fault-tolerant workflows without embedding orchestration logic inside application code.

---

Another common question is:

> **When should you use Step Functions instead of Lambda alone?**

Use Step Functions when a business process involves multiple steps, branching, retries, parallel execution, human approvals, or long-running operations. Lambda alone is better suited for short, stateless tasks.

---

Another common question is:

> **What is the Saga Pattern?**

The Saga Pattern manages distributed transactions using a sequence of local transactions and compensating actions. If one step fails, previous successful steps are undone through business-specific rollback operations.

---

Another common question is:

> **Can Step Functions access DynamoDB directly?**

Yes. Step Functions supports direct AWS SDK integrations with DynamoDB, allowing workflows to perform operations such as `PutItem`, `GetItem`, `UpdateItem`, and `DeleteItem` without requiring a Lambda function for every database interaction.

---

# Key Takeaways

- AWS Step Functions orchestrate complex workflows, while DynamoDB provides durable application state.
- State Machines simplify multi-step business processes with built-in retries, branching, and error handling.
- Parallel execution and Choice states improve performance and maintainability.
- The Saga Pattern is the preferred approach for handling distributed transactions across multiple services.
- Combining Step Functions with DynamoDB, Lambda, SNS, and EventBridge enables resilient, production-grade workflow orchestration.