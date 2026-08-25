# Amazon API Gateway — Troubleshooting

This section focuses on diagnosing and resolving real-world problems encountered when running Amazon API Gateway in production. Each chapter covers a specific failure category with structured root-cause analysis and resolution steps.

---

## Quick Navigation

| # | File | Topic |
|---|------|-------|
| 01 | [Common API Gateway Errors](./01-%20Common%20API%20Gateway%20Errors.md) | HTTP error codes (4XX, 5XX), Missing Authentication Token, Bad Gateway, Gateway Timeout |
| 02 | [Lambda Integration Issues](./02-%20Lambda%20Integration%20Issues.md) | Lambda invocation failures, invalid responses, permissions, cold starts, timeouts, and concurrency |
| 03 | [Authorization & Authentication Issues](./03-%20Authorization%20%26%20Authentication%20Issues.md) | IAM, Cognito, JWT Authorizers, Lambda Authorizers, Resource Policies, and API Key failures |
| 04 | [CORS Issues](./04-%20CORS%20Issues.md) | Browser CORS problems, preflight failures, OPTIONS requests, missing headers, and credentials issues |
| 05 | [VPC Link & Private API Issues](./05-%20VPC%20Link%20%26%20Private%20API%20Issues.md) | VPC Links, Private APIs, Interface Endpoints, Load Balancers, Security Groups, and DNS issues |
| 06 | [Deployment & Stage Issues](./06-%20Deployment%20%26%20Stage%20Issues.md) | Stale deployments, incorrect stages, stage variables, API mappings, and custom domain failures |
| 07 | [Performance & Timeout Issues](./07-%20Performance%20%26%20Timeout%20Issues.md) | Latency, throttling, Lambda cold starts, backend bottlenecks, caching, and performance optimization |
| 08 | [CloudWatch & Logging Issues](./08-%20CloudWatch%20%26%20Logging%20Issues.md) | CloudWatch Logs, Metrics, Access Logs, Execution Logs, X-Ray, and production observability |
| 09 | [API Gateway Limits & Quotas](./09-%20API%20Gateway%20Limits%20%26%20Quotas.md) | Service limits, throttling, quotas, payload restrictions, and capacity planning |
| 10 | [Production Troubleshooting Checklist](./10-%20Production%20Troubleshooting%20Checklist.md) | Step-by-step production runbook from client request to backend infrastructure |

---

## Recommended Study Order

1. [Common API Gateway Errors](./01-%20Common%20API%20Gateway%20Errors.md)
2. [Lambda Integration Issues](./02-%20Lambda%20Integration%20Issues.md)
3. [Authorization & Authentication Issues](./03-%20Authorization%20%26%20Authentication%20Issues.md)
4. [CORS Issues](./04-%20CORS%20Issues.md)
5. [VPC Link & Private API Issues](./05-%20VPC%20Link%20%26%20Private%20API%20Issues.md)
6. [Deployment & Stage Issues](./06-%20Deployment%20%26%20Stage%20Issues.md)
7. [Performance & Timeout Issues](./07-%20Performance%20%26%20Timeout%20Issues.md)
8. [CloudWatch & Logging Issues](./08-%20CloudWatch%20%26%20Logging%20Issues.md)
9. [API Gateway Limits & Quotas](./09-%20API%20Gateway%20Limits%20%26%20Quotas.md)
10. [Production Troubleshooting Checklist](./10-%20Production%20Troubleshooting%20Checklist.md)

---

## Related Sections

- [01 - Concepts → Amazon API Gateway](../../01-%20Concepts/07-%20Amazon%20API%20Gateway/README.md)
- [02 - Architecture → Amazon API Gateway](../../02-%20Architecture/07-%20Amazon%20API%20Gateway/README.md)
- [04 - Operations → Amazon API Gateway](../../04-%20Operations/07-%20Amazon%20API%20Gateway/README.md)
- [05 - Security → Amazon API Gateway](../../05-%20Security/06-%20Amazon%20API%20Gateway/README.md)
- [06 - Deployment → Amazon API Gateway](../../06-%20Deployment/01-%20Amazon%20API%20Gateway/README.md)
- [08 - Interview Questions → Amazon API Gateway](../../08-%20Interview%20Questions/07-%20Amazon%20API%20Gateway/README.md)
- [09 - Integrations → Amazon API Gateway](../../09-%20Integrations/01-%20Amazon%20API%20Gateway/README.md)
- [10 - Hands On → Amazon API Gateway](../../10-%20Hands%20On/01-%20Amazon%20API%20Gateway/README.md)
- [11 - Best Practices → Amazon API Gateway](../../11-%20Best%20Practices/01-%20Amazon%20API%20Gateway/README.md)
