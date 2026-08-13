# README

## Overview

This section contains interview-focused questions for **AWS CloudFormation**, progressing from core concepts to senior-level production scenarios.

The questions are designed around the areas commonly expected from backend engineers working with AWS infrastructure, CI/CD, Infrastructure as Code, security, reliability, and production operations.

## Quick Navigation

| Section | Topics |
|---|---|
| [Core CloudFormation Questions](./01-%20Core%20CloudFormation%20Questions.md) | CloudFormation fundamentals, stacks, templates, parameters, outputs, intrinsic functions, and core concepts |
| [Template and Resource Questions](./02-%20Template%20and%20Resource%20Questions.md) | Template structure, resources, properties, dependencies, intrinsic functions, and resource behavior |
| [Stack Lifecycle and Operations Questions](./03-%20Stack%20Lifecycle%20and%20Operations%20Questions.md) | Stack creation, updates, deletion, lifecycle states, operations, and deployment behavior |
| [Architecture Scenario Questions](./04-%20Architecture%20Scenario%20Questions.md) | Production architecture, stack design, dependencies, scalability, reliability, and infrastructure patterns |
| [Security Questions](./05-%20Security%20Questions.md) | IAM, least privilege, secrets, permissions, encryption, policies, and secure CloudFormation deployments |
| [Troubleshooting Scenario Questions](./06-%20Troubleshooting%20Scenario%20Questions.md) | Failed deployments, rollbacks, drift, resource failures, dependency issues, and operational troubleshooting |
| [Comparison Questions](./07-%20Comparison%20Questions.md) | CloudFormation comparisons, trade-offs, alternative approaches, and architectural decisions |
| [Senior Level and Production Questions](./08-%20Senior%20Level%20and%20Production%20Questions.md) | Senior engineering scenarios, production operations, governance, multi-account deployments, DR, and advanced design |

## Interview Progression

```text
Core Concepts
      |
      v
Template & Resources
      |
      v
Stack Lifecycle
      |
      v
Architecture Scenarios
      |
      v
Security
      |
      v
Troubleshooting
      |
      v
Comparisons
      |
      v
Senior & Production
```

## Recommended Order

### Core Foundation

Start with:

- [Core CloudFormation Questions](./01-%20Core%20CloudFormation%20Questions.md)
- [Template and Resource Questions](./02-%20Template%20and%20Resource%20Questions.md)

Focus on understanding how CloudFormation represents infrastructure and manages resources.

### Operations

Continue with:

- [Stack Lifecycle and Operations Questions](./03-%20Stack%20Lifecycle%20and%20Operations%20Questions.md)
- [Troubleshooting Scenario Questions](./06-%20Troubleshooting%20Scenario%20Questions.md)

Focus on stack states, updates, failures, rollbacks, drift, and operational recovery.

### Architecture and Security

Then study:

- [Architecture Scenario Questions](./04-%20Architecture%20Scenario%20Questions.md)
- [Security Questions](./05-%20Security%20Questions.md)

Focus on production architecture, IAM, deployment boundaries, resource protection, and infrastructure governance.

### Senior-Level Preparation

Finish with:

- [Comparison Questions](./07-%20Comparison%20Questions.md)
- [Senior Level and Production Questions](./08-%20Senior%20Level%20and%20Production%20Questions.md)

Focus on trade-offs, failure domains, scalability, multi-account architecture, CI/CD, governance, and production decision-making.

## Key Interview Areas

A strong CloudFormation interview preparation should cover:

- CloudFormation architecture
- Templates and resources
- Parameters, mappings, conditions, and outputs
- Intrinsic functions
- Stack lifecycle
- Change sets
- Resource replacement
- Rollbacks and recovery
- Nested stacks
- Cross-stack references
- Stack policies
- Termination protection
- Drift detection
- Custom resources
- StackSets
- IAM and deployment roles
- Secrets management
- CloudFormation Guard
- CloudFormation Hooks
- CI/CD integration
- Multi-account and multi-region deployments
- High availability
- Disaster recovery
- Cost and operational considerations
- Production troubleshooting
- Infrastructure ownership and governance

## Senior Interview Framework

For scenario-based questions, evaluate the problem through these dimensions:

| Dimension | Question to Ask |
|---|---|
| Blast Radius | What infrastructure can this change affect? |
| State | Is the resource stateful or ephemeral? |
| Replacement | Could this change replace the resource? |
| Rollback | Can the operation actually be reversed? |
| Dependencies | Which resources or stacks depend on it? |
| Security | Which identity is authorized to perform the change? |
| Observability | How will failure or degradation be detected? |
| Recovery | How will the system be restored? |
| Ownership | Which team or stack owns the resource? |
| Automation | How can the process become repeatable and controlled? |

## Key Takeaways

- Learn CloudFormation fundamentals before moving into production scenarios.
- Understand the difference between template changes and actual resource lifecycle operations.
- Treat resource replacement as a high-risk production event.
- Understand rollback limitations, especially for stateful resources and external side effects.
- Use change sets as part of a broader deployment-safety process.
- Understand stack boundaries, nested stacks, and cross-stack dependencies.
- Treat IAM and CloudFormation deployment roles as critical security boundaries.
- Understand drift as a configuration-governance problem rather than simply an error state.
- Be prepared to reason about multi-account, multi-region, and StackSet deployments.
- For senior interviews, emphasize **blast radius, state, replacement, rollback, security, dependencies, observability, recovery, ownership, and automation**.