# AWS CloudFormation

A deep-dive study guide into **AWS CloudFormation** — AWS's Infrastructure as Code (IaC) service for modeling, provisioning, and managing AWS resources using declarative YAML or JSON templates.

---

## 📚 Table of Contents

- [What is CloudFormation?](#what-is-cloudformation)
- [Topics Covered](#topics-covered)
- [Module Structure](#module-structure)
- [Key Concepts at a Glance](#key-concepts-at-a-glance)
- [Architecture Overview](#architecture-overview)
- [Template Anatomy](#template-anatomy)
- [Navigation](#navigation)

---

## What is CloudFormation?

AWS CloudFormation is an **Infrastructure as Code (IaC)** service that allows you to model, provision, and manage AWS resources using code instead of manual console configuration.

You define your infrastructure in a **template file** (YAML or JSON), and CloudFormation automatically creates, updates, and deletes resources as a single unit called a **Stack** — enabling version-controlled, repeatable, and automated infrastructure deployments.

---

## Topics Covered

| # | Topic | Focus Area |
|---|-------|------------|
| 01 | [Introduction](./01-%20Introduction.md) | What CloudFormation is, IaC concepts, benefits, lifecycle |
| 02 | [CloudFormation Templates](./02-%20CloudFormation%20Templates.md) | Template structure, sections, YAML vs JSON |
| 03 | [Resources](./03-%20Resources.md) | Defining AWS resources, resource types, dependencies |
| 04 | [Parameters](./04-%20Parameters.md) | User inputs, types, constraints, default values |
| 05 | [Pseudo Parameters](./05-%20Pseudo%20Parameters.md) | AWS-provided runtime values (`AWS::Region`, `AWS::StackName`, etc.) |
| 06 | [Mappings](./06-%20Mappings.md) | Static lookup tables for region/environment-based values |
| 07 | [Conditions](./07-%20Conditions.md) | Conditional resource creation and configuration |
| 08 | [Intrinsic Functions](./08-%20Intrinsic%20Functions.md) | `!Ref`, `!Sub`, `!GetAtt`, `!Join`, `!Select`, `!If`, and more |
| 09 | [Outputs and Cross Stack References](./09-%20Outputs%20and%20Cross%20Stack%20References.md) | Exporting values and sharing across stacks |
| 10 | [Stack Lifecycle](./10-%20Stack%20Lifecycle.md) | Create, update, delete operations and state management |
| 11 | [Change Sets](./11-%20Change%20Sets.md) | Previewing stack changes before applying them |
| 12 | [Rollbacks](./12-%20Rollbacks.md) | Automatic and manual rollback behavior |
| 13 | [Deletion Policies](./13-%20Deletion%20Policies.md) | `Retain`, `Snapshot`, `Delete` — controlling resource cleanup |
| 14 | [CloudFormation Service Role](./14-%20CloudFormation%20Service%20Role.md) | IAM roles for CloudFormation stack operations |
| 15 | [Capabilities](./15-%20Capabilities.md) | `CAPABILITY_IAM`, `CAPABILITY_NAMED_IAM`, `CAPABILITY_AUTO_EXPAND` |
| 16 | [Custom Resources](./16-%20Custom%20Resources.md) | Extending CloudFormation with Lambda-backed custom logic |
| 17 | [Best Practices](./17-%20Best%20Practices.md) | Production guidelines, template design, and operational patterns |
| 18 | [Common Interview Questions](./18-%20Common%20Interview%20Questions.md) | Interview prep with detailed answers |

---

## Module Structure

This module is organized into progressive learning sections:

```
AWS CloudFormation/
│
├── Fundamentals (01–02)
│   └── Introduction, Template Structure
│
├── Template Sections Deep-Dive (03–09)
│   └── Resources, Parameters, Pseudo Parameters,
│       Mappings, Conditions, Intrinsic Functions,
│       Outputs & Cross Stack References
│
├── Stack Operations (10–12)
│   └── Stack Lifecycle, Change Sets, Rollbacks
│
├── Advanced Features (13–16)
│   └── Deletion Policies, Service Roles,
│       Capabilities, Custom Resources
│
└── Production & Interview Prep (17–18)
    └── Best Practices, Interview Questions
```

---

## Key Concepts at a Glance

| Concept | Description |
|---------|-------------|
| **Template** | A YAML or JSON file that declares infrastructure (the blueprint) |
| **Stack** | A running collection of AWS resources managed as a single unit |
| **Resources** | The only required section — defines AWS services to create |
| **Parameters** | User-supplied inputs that make templates reusable |
| **Pseudo Parameters** | AWS-provided values like `AWS::Region` and `AWS::AccountId` |
| **Mappings** | Static key-value lookup tables (e.g., AMI IDs per region) |
| **Conditions** | Logic to conditionally create or configure resources |
| **Intrinsic Functions** | Built-in functions (`!Ref`, `!Sub`, `!GetAtt`, `!Join`, etc.) |
| **Outputs** | Values exported from a stack for cross-stack references |
| **Change Sets** | Preview of proposed changes before updating a stack |
| **Rollback** | Automatic revert to the previous state on failure |
| **Deletion Policy** | Controls what happens to a resource when the stack is deleted |
| **Custom Resources** | Lambda-backed extensions for unsupported or custom provisioning |

---

## Architecture Overview

```
  Developer / CI-CD Pipeline
              │
              ▼
   ┌─────────────────────┐
   │  CloudFormation      │
   │  Template (YAML/JSON)│
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │  CloudFormation      │
   │  Service             │
   │                      │
   │  ┌── Change Set ──┐  │
   │  │  (Preview)     │  │
   │  └────────────────┘  │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │  Stack               │
   │                      │
   │  ├── VPC             │
   │  ├── EC2             │
   │  ├── RDS             │
   │  ├── IAM Roles       │
   │  └── S3 Buckets      │
   └─────────────────────┘
```

---

## Template Anatomy

A CloudFormation template can contain these sections:

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: "Template description"

Parameters:       # User inputs
Mappings:         # Static lookup tables
Conditions:       # Conditional logic
Resources:        # AWS resources (REQUIRED)
Outputs:          # Exported values
```

> **Note:** Only the `Resources` section is mandatory.

---

## Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [AWS Concepts](../README.md) |

---

> **Part of the [Backend Engineering Playbook](../../../) — a structured learning resource for backend engineers.**
