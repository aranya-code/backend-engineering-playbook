# README

## Overview

This directory contains the AWS Lambda CLI reference for managing serverless functions throughout their lifecycle, from initial creation and deployment to production operations, troubleshooting, scaling, and cleanup.

The documentation focuses on practical AWS CLI v2 workflows for backend engineers working with Python services, event-driven architectures, asynchronous processing, and production serverless workloads.

Use these notes alongside the AWS Lambda concepts, architecture, security, deployment, and operations documentation in the broader `backend-engineering-playbook`.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Introduction to Lambda CLI](./01-%20Introduction%20to%20Lambda%20CLI.md) | Overview of AWS Lambda CLI capabilities, use cases, and foundational CLI configuration for serverless management. |
| 02 | [02- Function Inspection and Management](./02-%20Function%20Inspection%20and%20Management.md) | Commands for listing, describing, and inspecting Lambda functions, configurations, and metadata. |
| 03 | [03- Function Creation and Deployment](./03-%20Function%20Creation%20and%20Deployment.md) | Create, update, and deploy Lambda functions using AWS CLI with deployment packages and configurations. |
| 04 | [04- Function Configuration and Environment Variables](./04-%20Function%20Configuration%20and%20Environment%20Variables.md) | Configure function settings, environment variables, memory, timeout, and runtime options. |
| 05 | [05- Versions and Aliases Management](./05-%20Versions%20and%20Aliases%20Management.md) | Publish versions, manage aliases, configure traffic shifting, and control deployment targets. |
| 06 | [06- Event Source Mapping Management](./06-%20Event%20Source%20Mapping%20Management.md) | Create and manage event source mappings for SQS, Kinesis, DynamoDB Streams, and other poll-based sources. |
| 07 | [07- IAM Permissions and Resource Policies](./07-%20IAM%20Permissions%20and%20Resource%20Policies.md) | Manage execution roles, resource-based policies, and invocation permissions using the CLI. |
| 08 | [08- Lambda Layers Management](./08-%20Lambda%20Layers%20Management.md) | Create, publish, and manage Lambda layers and shared dependency packages. |
| 09 | [09- Function Invocation and Payloads](./09-%20Function%20Invocation%20and%20Payloads.md) | Invoke Lambda functions synchronously and asynchronously with event payloads and response handling. |
| 10 | [10- Monitoring, Logging and Performance Commands](./10-%20Monitoring%2C%20Logging%20and%20Performance%20Commands.md) | Use CLI commands to retrieve CloudWatch logs, metrics, and performance data. |
| 11 | [11- Concurrency and Scaling Management](./11-%20Concurrency%20and%20Scaling%20Management.md) | Manage Lambda concurrency, reserved concurrency, provisioned concurrency, scaling behavior, and capacity constraints. |
| 12 | [12- Querying, Filtering and Output Formatting](./12-%20Querying%2C%20Filtering%20and%20Output%20Formatting.md) | Use AWS CLI queries, JMESPath expressions, output formats, filtering, and command combinations for operational inspection and automation. |
| 13 | [13- Operational CLI Workflows](./13-%20Operational%20CLI%20Workflows.md) | Apply repeatable CLI workflows for common Lambda administration and operational tasks. |
| 14 | [14- Troubleshooting Commands and Best Practices](./14-%20Troubleshooting%20Commands%20and%20Best%20Practices.md) | Diagnose Lambda runtime, invocation, permission, networking, event processing, deployment, observability, and cost issues. |
| 15 | [15- AWS Lambda CLI Cheat Sheet](./15-%20AWS%20Lambda%20CLI%20Cheat%20Sheet.md) | Quickly reference frequently used commands for function inspection, invocation, configuration, versions, aliases, event source mappings, logs, and permissions. |

## Prerequisites

Before using these commands, ensure that you have:

- AWS CLI v2 installed and available in your terminal.
- A configured AWS profile or an approved IAM role obtained through your organization's authentication workflow.
- Access to the target AWS account and Region.
- The required IAM permissions for the operation being performed.
- An understanding of the target function's dependencies, event sources, and production impact.

Verify the active identity before performing mutating operations:

```bash
aws sts get-caller-identity \
  --profile dev \
  --region ap-south-1
```

Replace `dev` and `ap-south-1` with the intended profile and Region.

## Recommended Learning Order

1. **Operational CLI workflows:** Learn the standard sequence for inspecting, changing, and verifying Lambda resources.
2. **Querying and output formatting:** Build efficient inspection commands and reusable shell automation.
3. **Concurrency and scaling:** Understand the operational controls that influence throughput and downstream capacity.
4. **Troubleshooting:** Diagnose failures using configuration, logs, metrics, and event source mapping state.
5. **CLI cheat sheet:** Use the consolidated reference during implementation and production support.

## Operational Safety

- Prefer read-only inspection commands before making changes.
- Specify `--profile` and `--region` explicitly in operational scripts.
- Verify account identity before deploying, deleting, or changing production resources.
- Wait for asynchronous configuration updates to complete and inspect the resulting state.
- Review the impact of changing concurrency, environment variables, resource policies, and event source mappings.
- Protect deployment artifacts, temporary function download URLs, environment values, and command output.
- Confirm dependent resources before deleting a function or integration.
- Use infrastructure as code for repeatable environment provisioning and configuration management wherever practical.

## Key Takeaways

- This directory is the operational CLI reference for AWS Lambda, complementing the broader engineering documentation.
- Read-only inspection, explicit account targeting, and post-change verification should be standard operational practices.
- Concurrency, event source mappings, invocation permissions, and deployment changes can affect application reliability and downstream systems.
- Use the cheat sheet for quick reference and the focused notes for deeper operational workflows and troubleshooting.