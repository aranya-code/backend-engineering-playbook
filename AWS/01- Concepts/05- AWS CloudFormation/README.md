# AWS CloudFormation

## Overview

AWS CloudFormation is Amazon's Infrastructure as Code (IaC) service that enables modeling, provisioning, and managing AWS resources through declarative templates. This folder provides a structured deep-dive into CloudFormation concepts, from foundational topics to advanced features.

The documentation is organized sequentially to build knowledge progressively, covering template anatomy, resource management, stack operations, and extension mechanisms.

---

## Folder Structure

```text
AWS CloudFormation/
├── 01- Introduction.md
├── 02- CloudFormation Templates.md
├── 03- Resources.md
├── 04- Parameters.md
├── 05- Pseudo Parameters.md
├── 06- Mappings.md
├── 07- Conditions.md
├── 08- Intrinsic Functions.md
├── 09- Outputs and Cross Stack References.md
├── 10- Deletion Policies.md
├── 11- Capabilities.md
├── 12- Custom Resources.md
└── README.md
```

---

## Quick Navigation

| #  | Topic                   | Coverage                                   |
| -- | ----------------------- | ------------------------------------------ |
| 01 | [Introduction](01-%20Introduction.md) | Fundamentals of CloudFormation, IaC concepts, benefits, and lifecycle. |
| 02 | [CloudFormation Templates](02-%20CloudFormation%20Templates.md) | Template structure, sections, YAML vs JSON, and syntax basics. |
| 03 | [Resources](03-%20Resources.md) | Defining AWS resources, resource types, properties, and dependencies. |
| 04 | [Parameters](04-%20Parameters.md) | User inputs, types, constraints, default values, and dynamic template behavior. |
| 05 | [Pseudo Parameters](05-%20Pseudo%20Parameters.md) | AWS-provided runtime values like region, account ID, and stack name. |
| 06 | [Mappings](06-%20Mappings.md) | Static lookup tables for region/environment-specific values (e.g., AMIs). |
| 07 | [Conditions](07-%20Conditions.md) | Conditional logic for resource creation and configuration based on parameters. |
| 08 | [Intrinsic Functions](08-%20Intrinsic%20Functions.md) | Built-in functions (!Ref, !Sub, !GetAtt, !Join, !Select, !If, etc.) for template manipulation. |
| 09 | [Outputs and Cross Stack References](09-%20Outputs%20and%20Cross%20Stack%20References.md) | Exporting stack values and importing them in other stacks for modularity. |
| 10 | [Deletion Policies](10-%20Deletion%20Policies.md) | Controlling resource behavior during stack deletion (Retain, Snapshot, Delete). |
| 11 | [Capabilities](11-%20Capabilities.md) | Security acknowledgments required for IAM resources, macros, and transforms. |
| 12 | [Custom Resources](12-%20Custom%20Resources.md) | Extending CloudFormation with Lambda-backed logic for custom provisioning. |

---

## Learning Path

```text
Introduction
   │
    ▼
CloudFormation Templates
   │
    ▼
Resources
   │
    ▼
Parameters
   │
    ▼
Pseudo Parameters
   │
    ▼
Mappings
   │
    ▼
Conditions
   │
    ▼
Intrinsic Functions
   │
    ▼
Outputs and Cross Stack References
   │
    ▼
Deletion Policies
   │
    ▼
Capabilities
   │
    ▼
Custom Resources
```

---

## Key Areas

### Fundamentals

Introduction and template basics establish what CloudFormation is and how to write templates.

### Template Configuration

Parameters, pseudo parameters, mappings, and conditions enable dynamic and reusable templates.

### Resource Management

Defining AWS resources, intrinsic functions, and outputs covers core provisioning and referencing.

### Advanced Controls

Deletion policies, capabilities, and custom resources provide safety, security, and extensibility.

---

## Recommended Study Order

Follow the files in numerical order. Each topic should build on the concepts introduced previously.

```text
01 → Introduction
02 → CloudFormation Templates
03 → Resources
04 → Parameters
05 → Pseudo Parameters
06 → Mappings
07 → Conditions
08 → Intrinsic Functions
09 → Outputs and Cross Stack References
10 → Deletion Policies
11 → Capabilities
12 → Custom Resources
```

---

## Key Takeaways

* CloudFormation enables repeatable, version-controlled infrastructure deployments.
* Templates consist of sections like Resources, Parameters, and Outputs, with intrinsic functions for dynamic behavior.
* Deletion policies and capabilities provide critical safeguards for production environments.
* Custom resources extend CloudFormation to support any AWS or third-party service via Lambda.
