# 02 - Fine-Grained Access Control (FGAC)

## Overview

In most production applications, granting access to an entire DynamoDB table is too broad.

For example:

- Customers should only read **their own orders**.
- Employees should only access **their department's records**.
- Sellers should only update **their own products**.
- Tenants in a SaaS application should never access another tenant's data.

This is where **Fine-Grained Access Control (FGAC)** becomes essential.

FGAC allows you to restrict access not only to a table, but also to:

- Individual items
- Specific partition keys
- Selected attributes
- Read-only or write-only operations

Instead of enforcing authorization entirely in application code, IAM policies can enforce these rules before DynamoDB processes the request.

---

# Why FGAC Matters

Imagine an e-commerce application.

Poor design:

```text
Customer

↓

Orders Table

↓

Reads Every Order
```

Secure design:

```text
Customer

↓

IAM Policy

↓

CustomerId = USER123

↓

Only Their Orders
```

Even if the application has a bug, IAM prevents unauthorized access.

---

# Standard IAM vs FGAC

Standard IAM:

```text
Allow

↓

Orders Table
```

FGAC:

```text
Allow

↓

Orders Table

↓

Partition Key = USER123
```

The permission is tied to specific data.

---

# How FGAC Works

FGAC combines:

- IAM Policies
- Policy Variables
- DynamoDB Condition Keys

Architecture:

```text
User

↓

IAM Authentication

↓

IAM Policy

↓

Condition Evaluation

↓

DynamoDB
```

The request is evaluated before any data is returned.

---

# Internal Authorization Flow

```text
Request

↓

Authenticate

↓

Evaluate IAM Policy

↓

Evaluate Conditions

↓

Allow

or

Deny

↓

Execute Request
```

If any condition fails, access is denied.

---

# Restricting Access by Partition Key

Suppose every order is stored using:

```text
Partition Key

↓

CustomerId
```

Table:

```text
CustomerId

OrderId

Amount
```

Each customer should only access their own partition.

Architecture:

```text
Customer

↓

CustomerId = USER123

↓

Orders

↓

Partition USER123
```

No other partition is accessible.

---

# Using Policy Variables

IAM supports variables that are replaced during request evaluation.

Example:

```text
aws:username
```

If:

```text
Username

↓

alice
```

The condition becomes:

```text
CustomerId

↓

alice
```

Policies automatically adapt to each authenticated user.

---

# Restricting Query Operations

Example IAM policy:

```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:Query"
  ],
  "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/Orders",
  "Condition": {
    "ForAllValues:StringEquals": {
      "dynamodb:LeadingKeys": [
        "${aws:username}"
      ]
    }
  }
}
```

Only items whose partition key matches the authenticated user are accessible.

---

# Restricting Attributes

Sometimes users should only see selected fields.

Example item:

```text
CustomerId

OrderId

Amount

InternalNotes

PaymentToken
```

Customer should only receive:

```text
CustomerId

OrderId

Amount
```

Sensitive attributes remain hidden.

---

# Attribute-Level Permissions

IAM supports:

```text
dynamodb:Attributes
```

Example:

```text
Allow

↓

CustomerId

OrderId

Amount
```

Denied:

```text
InternalNotes

PaymentToken
```

Applications receive only the approved attributes.

---

# Read-Only Access

Some workloads should never modify data.

Policy:

```text
Allow

↓

GetItem

Query

Scan
```

Denied:

```text
PutItem

UpdateItem

DeleteItem
```

Useful for:

- Reporting
- Dashboards
- Analytics
- BI tools

---

# Write-Only Access

Some applications only insert records.

Example:

```text
IoT Devices

↓

PutItem
```

Denied:

```text
Query

DeleteItem
```

This minimizes risk.

---

# Multi-Tenant SaaS Example

Table:

```text
TenantId

UserId

Data
```

Architecture:

```text
Tenant A

↓

Tenant A Partition

────────────

Tenant B

↓

Tenant B Partition
```

IAM ensures complete tenant isolation.

---

# Healthcare Example

Hospital:

```text
Doctors

↓

Patient Records
```

Rules:

```text
Doctor A

↓

Only Assigned Patients
```

FGAC helps enforce regulatory requirements such as HIPAA.

---

# Banking Example

Customer:

```text
Account

↓

Transactions
```

IAM Policy:

```text
CustomerID

↓

Own Transactions Only
```

Even direct API calls cannot bypass the policy.

---

# Production Architecture

```text
           User

             │

             ▼

      Amazon Cognito

             │

             ▼

      Temporary IAM Role

             │

             ▼

      IAM Policy Variables

             │

             ▼

          DynamoDB

             │

             ▼

      Authorized Items Only
```

This is a common architecture for serverless applications.

---

# Best Practices

- Design partition keys around authorization boundaries.
- Use IAM Roles instead of IAM Users.
- Restrict both actions and resources.
- Use policy variables whenever possible.
- Hide sensitive attributes.
- Test policies with multiple users.
- Audit access using CloudTrail.

---

# Common Mistakes

## Filtering Instead of Restricting

Poor:

```text
Read All Items

↓

Application Filters Results
```

Better:

```text
IAM

↓

Returns Only Authorized Items
```

Filtering in application code is not a security boundary.

---

## Sharing Partition Keys

Poor:

```text
Partition

↓

CUSTOMERS
```

Better:

```text
Customer123

Customer456

Customer789
```

Partition keys should naturally support authorization.

---

## Using Administrator Permissions

Applications should never receive unrestricted DynamoDB access.

---

## Forgetting Attribute Restrictions

Returning internal fields may expose:

- Payment tokens
- Internal comments
- Audit information
- Personally identifiable information (PII)

Restrict attributes whenever appropriate.

---

# Production Considerations

FGAC is commonly combined with:

```text
Amazon Cognito

↓

IAM Role

↓

Fine-Grained Policy

↓

DynamoDB
```

Large SaaS platforms often build their authorization model around:

- Tenant isolation
- Customer isolation
- Department isolation
- Region-based access
- Role-based access control (RBAC)

FGAC provides an additional security layer beyond application logic.

---

# Interview Notes

A common interview question is:

> **What is Fine-Grained Access Control (FGAC) in DynamoDB?**

FGAC allows IAM policies to restrict access to specific items, partition keys, attributes, and operations instead of granting access to an entire table.

Another common question is:

> **How do you ensure that users can only access their own data in DynamoDB?**

A common approach is to design the partition key around the user or tenant identifier and use IAM condition keys such as `dynamodb:LeadingKeys` with policy variables like `${aws:username}` or identity attributes from Amazon Cognito.

Another common question is:

> **Why is FGAC better than filtering in application code?**

FGAC enforces authorization within AWS before DynamoDB processes the request. Application-level filtering can fail if the application contains bugs or security vulnerabilities.

Another common question is:

> **Can FGAC restrict access to individual attributes?**

Yes. IAM policies can use DynamoDB condition keys such as `dynamodb:Attributes` to allow or deny access to specific attributes within an item.

---

# Key Takeaways

- Fine-Grained Access Control (FGAC) enables item-level and attribute-level authorization in DynamoDB.
- IAM condition keys such as `dynamodb:LeadingKeys` help enforce access based on partition keys.
- Policy variables allow a single IAM policy to adapt dynamically to different authenticated users.
- FGAC is ideal for multi-tenant SaaS platforms, healthcare systems, financial applications, and customer-facing APIs.
- Enforcing authorization in IAM provides stronger security than relying solely on application-level filtering.
- Designing partition keys with authorization boundaries in mind simplifies secure and scalable access control.