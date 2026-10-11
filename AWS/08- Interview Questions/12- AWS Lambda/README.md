# README

## Overview

This directory contains interview preparation material for **AWS Lambda**, covering foundational concepts, serverless architecture, security, deployment, CLI operations, troubleshooting, and senior-level engineering scenarios.

The documentation is designed for backend engineers progressing from intermediate AWS knowledge to production-level serverless engineering. It emphasizes Python-based implementations, event-driven systems, distributed processing, operational reliability, and practical AWS CLI usage.

The material is organized to help you understand Lambda's execution model, build serverless applications, make architecture decisions, diagnose production failures, and explain engineering trade-offs confidently during technical interviews.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Lambda Fundamentals Questions](./01-%20Lambda%20Fundamentals%20Questions.md) | Core Lambda concepts, execution environments, handlers, invocation models, runtime behavior, configuration, and concurrency. |
| 02 | [02- Invocation and Event Source Questions](./02-%20Invocation%20and%20Event%20Source%20Questions.md) | Questions on synchronous and asynchronous invocation, event source mapping, retries, and delivery semantics. |
| 03 | [03- Architecture and Integration Questions](./03-%20Architecture%20and%20Integration%20Questions.md) | Serverless architecture patterns, API integrations, event-driven processing, asynchronous workloads, and system design. |
| 04 | [04- Security and IAM Questions](./04-%20Security%20and%20IAM%20Questions.md) | Execution roles, resource-based policies, IAM permissions, secrets management, VPC security, and secure deployment practices. |
| 05 | [05- Performance and Concurrency Questions](./05-%20Performance%20and%20Concurrency%20Questions.md) | Performance optimization, cold starts, concurrency, memory configuration, and scaling behavior questions. |
| 06 | [06- Advanced Features Questions](./06-%20Advanced%20Features%20Questions.md) | Provisioned concurrency, SnapStart, layers, extensions, custom runtimes, container images, and advanced capabilities. |
| 07 | [07- Deployment and Operations Questions](./07-%20Deployment%20and%20Operations%20Questions.md) | Deployment strategies, CI/CD, versioning, aliases, traffic shifting, and operational management questions. |
| 08 | [08- Troubleshooting Scenarios](./08-%20Troubleshooting%20Scenarios.md) | Diagnostic procedures for runtime failures, timeouts, throttling, IAM errors, networking, and deployment issues. |
| 09 | [09- Scenario-Based Questions](./09-%20Scenario-Based%20Questions.md) | Real-world production scenarios, architecture decisions, and practical engineering trade-offs. |
| 10 | [10- Production Architecture Scenarios](./10-%20Production%20Architecture%20Scenarios.md) | Senior-level production architecture scenario questions and system design discussions. |
| 11 | [11- Comparison Questions and Common Interview Traps](./11-%20Comparison%20Questions%20and%20Common%20Interview%20Traps.md) | Comparing Lambda with other compute services, common misconceptions, and interview trap questions. |
| 12 | [12- Senior-Level Questions](./12-%20Senior-Level%20Questions.md) | Senior-level and principal engineer questions on architecture, distributed systems, and engineering judgment. |
| 13 | [13- Hands-On Coding and Debugging Questions](./13-%20Hands-On%20Coding%20and%20Debugging%20Questions.md) | Coding challenges, debugging exercises, and hands-on implementation questions. |
| 14 | [14- Mock Interview](./14-%20Mock%20Interview.md) | Full mock interview simulation with technical questions, system design, and evaluation criteria. |
| 15 | [15- Lambda CLI Interview Guide](./15-%20Lambda%20CLI%20Interview%20Guide.md) | CLI-focused interview preparation for Lambda function management and operational commands. |

## Recommended Study Order

Follow this sequence to build knowledge progressively rather than memorizing isolated AWS CLI commands or service definitions.

| Stage | Focus | Expected competency |
|---|---|---|
| Foundations | Execution model, handlers, invocation, runtimes, configuration | Explain how Lambda executes code and handles requests. |
| Architecture | API Gateway, SQS, S3, EventBridge, DynamoDB Streams, Step Functions | Select appropriate synchronous and asynchronous processing patterns. |
| Security | IAM, resource policies, secrets, networking | Design least-privilege execution and invocation permissions. |
| Advanced features | Concurrency, SnapStart, layers, extensions, container images | Evaluate performance, operational complexity, and cost trade-offs. |
| Hands-on projects | APIs, event processing, persistence, monitoring, CI/CD | Implement and verify working serverless applications. |
| CLI and deployment | Function management, versions, aliases, event source mappings | Automate deployments and perform controlled operational changes. |
| Troubleshooting and operations | Logs, metrics, throttling, failures, quotas, recovery | Diagnose incidents systematically and improve production reliability. |
| Interview preparation | Scenarios, coding, architecture, and senior-level trade-offs | Justify technical decisions and reason through real-world failures. |

## How to Use This Reference

- **For learning:** Study the concepts first, then implement the corresponding hands-on projects.
- **For interview preparation:** Practice explaining execution behavior, retries, idempotency, concurrency, IAM, and architecture trade-offs without relying on memorized definitions.
- **For practical operations:** Use the CLI and troubleshooting notes as references, verifying the target account, Region, and resource configuration before making changes.
- **For production readiness:** Review security, observability, deployment, cost, and failure-recovery requirements before deploying a workload.
- **For long-term maintenance:** Keep focused topic documents, use relative links to existing files, and avoid duplicating detailed explanations across multiple sections.

## Key Takeaways

- Learn Lambda's execution and event-processing semantics before choosing serverless architecture patterns.
- Treat IAM, idempotency, retries, concurrency, and downstream capacity as core production design concerns.
- Use hands-on projects to validate concepts through deployment, testing, monitoring, and cleanup.
- Use AWS CLI commands with explicit profiles and Regions, and verify changes rather than assuming successful execution guarantees application health.
- Keep navigation links synchronized with the actual repository structure so the playbook remains a reliable engineering reference.