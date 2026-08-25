# Amazon API Gateway — Integrations

API Gateway integrations define **how Amazon API Gateway communicates with backend services** — where requests are sent, whether transformations occur, and how backends process incoming requests. This section covers every major integration type from modern serverless Lambda integrations to direct AWS service integrations.

---

## Quick Navigation

| # | File | Topic |
|---|------|-------|
| 01 | [Integration Types Overview](./01-%20Integration%20Types%20Overview.md) | All API Gateway integration types, their architecture, and when to choose each one |
| 02 | [Lambda Proxy Integration](./02-%20Lambda%20Proxy%20Integration.md) | Recommended integration for modern serverless apps — API Gateway forwards requests directly to Lambda |
| 03 | [Lambda Non-Proxy Integration](./03-%20Lambda%20Non-Proxy%20Integration.md) | Using Mapping Templates to transform requests and responses before communicating with Lambda |
| 04 | [HTTP Proxy Integration](./04-%20HTTP%20Proxy%20Integration.md) | API Gateway as a reverse proxy for existing HTTP services (FastAPI, Django, Spring Boot, Express.js) |
| 05 | [HTTP Custom Integration](./05-%20HTTP%20Custom%20Integration.md) | Transforming requests and responses when integrating with HTTP backends using Mapping Templates (VTL) |
| 06 | [AWS Service Integrations](./06-%20AWS%20Service%20Integrations.md) | Direct integration with SQS, SNS, Step Functions, DynamoDB, EventBridge, and Kinesis without Lambda |
| 07 | [Mock Integrations](./07-%20Mock%20Integrations.md) | API prototyping, frontend development, testing, and static responses without any backend service |
| 08 | [Mapping Templates (VTL)](./08-%20Mapping%20Templates%20(VTL).md) | Velocity Template Language for request/response transformation, legacy system support, and payload customization |
| 09 | [Request Transformation](./09-%20Request%20Transformation.md) | Transforming incoming requests before they reach the backend |
| 10 | [Response Transformation](./10-%20Response%20Transformation.md) | Transforming backend responses before returning them to clients |
| 11 | [OpenAPI Integration](./11-%20OpenAPI%20Integration.md) | Importing and exporting API Gateway configurations using OpenAPI/Swagger specs |

---

## Recommended Study Order

1. [Integration Types Overview](./01-%20Integration%20Types%20Overview.md)
2. [Lambda Proxy Integration](./02-%20Lambda%20Proxy%20Integration.md)
3. [Lambda Non-Proxy Integration](./03-%20Lambda%20Non-Proxy%20Integration.md)
4. [HTTP Proxy Integration](./04-%20HTTP%20Proxy%20Integration.md)
5. [HTTP Custom Integration](./05-%20HTTP%20Custom%20Integration.md)
6. [AWS Service Integrations](./06-%20AWS%20Service%20Integrations.md)
7. [Mock Integrations](./07-%20Mock%20Integrations.md)
8. [Mapping Templates (VTL)](./08-%20Mapping%20Templates%20(VTL).md)
9. [Request Transformation](./09-%20Request%20Transformation.md)
10. [Response Transformation](./10-%20Response%20Transformation.md)
11. [OpenAPI Integration](./11-%20OpenAPI%20Integration.md)

---

## Related Sections

- [01 - Concepts → Amazon API Gateway](../../01-%20Concepts/07-%20Amazon%20API%20Gateway/README.md)
- [02 - Architecture → Amazon API Gateway](../../02-%20Architecture/07-%20Amazon%20API%20Gateway/README.md)
- [04 - Operations → Amazon API Gateway](../../04-%20Operations/07-%20Amazon%20API%20Gateway/README.md)
- [05 - Security → Amazon API Gateway](../../05-%20Security/06-%20Amazon%20API%20Gateway/README.md)
- [06 - Deployment → Amazon API Gateway](../../06-%20Deployment/01-%20Amazon%20API%20Gateway/README.md)
- [07 - Troubleshooting → Amazon API Gateway](../../07-%20Troubleshooting/06-%20Amazon%20API%20Gateway/README.md)
- [08 - Interview Questions → Amazon API Gateway](../../08-%20Interview%20Questions/07-%20Amazon%20API%20Gateway/README.md)
- [10 - Hands On → Amazon API Gateway](../../10-%20Hands%20On/01-%20Amazon%20API%20Gateway/README.md)
- [11 - Best Practices → Amazon API Gateway](../../11-%20Best%20Practices/01-%20Amazon%20API%20Gateway/README.md)
