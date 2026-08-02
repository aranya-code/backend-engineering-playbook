# Troubleshooting

Building an API is only half the job—keeping it reliable in production is equally important.

The **Troubleshooting** section focuses on diagnosing and resolving real-world problems encountered when running Amazon API Gateway in production. Rather than introducing new features, these notes teach you how to systematically identify failures, isolate root causes, and restore service quickly.

The topics covered here mirror the types of incidents backend engineers and DevOps teams face daily, including integration failures, authentication issues, CORS problems, networking errors, deployment mistakes, performance bottlenecks, and production outages.

By following these guides, you'll develop a structured troubleshooting methodology that significantly reduces Mean Time to Resolution (MTTR) during production incidents.

---

# Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Common API Gateway Errors](./01-%20Common%20API%20Gateway%20Errors.md) | Understand common HTTP error codes (4XX, 5XX), Missing Authentication Token, Bad Gateway, Gateway Timeout, and how to diagnose them. |
| [02 - Lambda Integration Issues](./02-%20Lambda%20Integration%20Issues.md) | Troubleshoot Lambda invocation failures, invalid responses, permissions, cold starts, timeouts, concurrency, and deployment issues. |
| [03 - Authorization & Authentication Issues](./03-%20Authorization%20%26%20Authentication%20Issues.md) | Diagnose IAM, Cognito, JWT Authorizers, Lambda Authorizers, Resource Policies, API Keys, and authentication failures. |
| [04 - CORS Issues](./04-%20CORS%20Issues.md) | Resolve browser CORS problems, preflight failures, OPTIONS requests, missing headers, credentials issues, and frontend integration problems. |
| [05 - VPC Link & Private API Issues](./05-%20VPC%20Link%20%26%20Private%20API%20Issues.md) | Troubleshoot VPC Links, Private APIs, Interface Endpoints, Load Balancers, Security Groups, DNS, and networking issues. |
| [06 - Deployment & Stage Issues](./06-%20Deployment%20%26%20Stage%20Issues.md) | Fix stale deployments, incorrect stages, stage variables, API mappings, custom domains, and deployment automation failures. |
| [07 - Performance & Timeout Issues](./07-%20Performance%20%26%20Timeout%20Issues.md) | Diagnose latency, throttling, Lambda cold starts, backend bottlenecks, database issues, caching, and performance optimization. |
| [08 - CloudWatch & Logging Issues](./08-%20CloudWatch%20%26%20Logging%20Issues.md) | Configure and troubleshoot CloudWatch Logs, Metrics, Access Logs, Execution Logs, X-Ray, and production observability. |
| [09 - API Gateway Limits & Quotas](./09-%20API%20Gateway%20Limits%20%26%20Quotas.md) | Understand service limits, throttling, quotas, payload restrictions, request limits, and capacity planning. |
| [10 - Production Troubleshooting Checklist](./10-%20Production%20Troubleshooting%20Checklist.md) | A step-by-step production runbook for diagnosing incidents from client request to backend infrastructure. |

---

# Learning Path

```text
Understand Errors

        │

        ▼

Investigate Integrations

        │

        ▼

Verify Authentication

        │

        ▼

Resolve CORS

        │

        ▼

Debug Networking

        │

        ▼

Validate Deployments

        │

        ▼

Optimize Performance

        │

        ▼

Inspect Logs & Metrics

        │

        ▼

Review Limits

        │

        ▼

Follow Production Runbook
```

Each chapter builds on the previous one to create a complete troubleshooting methodology.

---

# Production Troubleshooting Workflow

```text
Client Request

        │

        ▼

HTTP Status Code

        │

        ▼

Authentication

        │

        ▼

Authorization

        │

        ▼

API Gateway

        │

        ▼

Integration

        │

        ▼

Backend

        │

        ▼

Database

        │

        ▼

Logs & Metrics

        │

        ▼

Root Cause

        │

        ▼

Resolution
```

This layered approach helps isolate failures efficiently.

---

# What You'll Learn

## Error Diagnosis

Understand how to identify and resolve:

- Client errors (4XX)
- Server errors (5XX)
- Integration failures
- Gateway timeouts
- Invalid requests

---

## Integration Troubleshooting

Debug integrations with:

- AWS Lambda
- Amazon ECS
- EC2
- Application Load Balancer
- HTTP Backends

---

## Security Troubleshooting

Investigate issues involving:

- IAM Authorization
- JWT Authorizers
- Lambda Authorizers
- Cognito User Pools
- API Keys
- Usage Plans
- Resource Policies

---

## Network Troubleshooting

Learn to diagnose:

- VPC Links
- Interface VPC Endpoints
- Private APIs
- Security Groups
- Route Tables
- DNS Resolution

---

## Deployment Problems

Resolve:

- Missing deployments
- Incorrect stages
- API mappings
- Custom domains
- Stage variables
- Deployment automation failures

---

## Performance Analysis

Improve API performance by identifying:

- High latency
- Slow integrations
- Database bottlenecks
- Lambda cold starts
- Cache misses
- Request throttling

---

## Observability

Use AWS monitoring tools effectively:

- CloudWatch Metrics
- CloudWatch Logs
- Access Logs
- Execution Logs
- CloudWatch Insights
- AWS X-Ray

---

## Capacity Planning

Understand:

- Service quotas
- Rate limits
- Burst limits
- Payload limits
- Scaling considerations

---

# Recommended Troubleshooting Order

When investigating production issues, follow this order:

```text
1. HTTP Status Code

        │

        ▼

2. CloudWatch Metrics

        │

        ▼

3. CloudWatch Logs

        │

        ▼

4. Authentication

        │

        ▼

5. Authorization

        │

        ▼

6. API Gateway Configuration

        │

        ▼

7. Backend

        │

        ▼

8. Database

        │

        ▼

9. Networking
```

Avoid making configuration changes before identifying the root cause.

---

# AWS Services You'll Use

Throughout this section, you'll work with:

- Amazon API Gateway
- Amazon CloudWatch
- AWS X-Ray
- AWS Lambda
- Amazon ECS
- Amazon EC2
- Elastic Load Balancing (ALB/NLB)
- Amazon VPC
- AWS WAF
- Amazon Route 53
- AWS IAM
- Amazon Cognito
- AWS Service Quotas

Together, these services provide the visibility needed to diagnose production systems.

---

# Troubleshooting Principles

Effective troubleshooting follows these principles:

- Reproduce the issue before making changes.
- Start with the HTTP status code.
- Check metrics before logs.
- Correlate requests using Request IDs.
- Verify infrastructure before modifying application code.
- Fix the root cause, not just the symptoms.
- Validate the solution before closing the incident.
- Document recurring problems and resolutions.

---

# Real-World Production Workflow

```text
Monitoring Alert

        │

        ▼

CloudWatch Alarm

        │

        ▼

CloudWatch Metrics

        │

        ▼

CloudWatch Logs

        │

        ▼

AWS X-Ray

        │

        ▼

Backend Logs

        │

        ▼

Root Cause Analysis

        │

        ▼

Fix

        │

        ▼

Validation

        │

        ▼

Production Monitoring
```

This workflow is commonly used by backend engineering, SRE, and DevOps teams.

---

# Best Practices

When troubleshooting API Gateway:

- Enable execution and access logging.
- Configure CloudWatch alarms before production.
- Use Request IDs to correlate distributed logs.
- Enable AWS X-Ray for distributed tracing.
- Monitor latency trends, not just failures.
- Keep backend health endpoints simple and reliable.
- Use structured logging instead of free-form messages.
- Test fixes in lower environments before production.
- Automate deployments to reduce configuration drift.
- Maintain an incident runbook for recurring issues.

---

# Final Outcome

After completing this section, you'll be able to confidently troubleshoot Amazon API Gateway in production.

You'll understand how to identify failures across the entire request lifecycle—from client requests and authentication through API Gateway, integrations, backend services, networking, and databases—using CloudWatch, X-Ray, and a structured troubleshooting workflow.

Instead of reacting to symptoms, you'll be equipped to perform efficient root cause analysis and resolve production incidents with confidence.