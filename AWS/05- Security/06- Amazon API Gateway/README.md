# Amazon API Gateway — Security

This section provides a comprehensive guide to securing APIs using the native security features of Amazon API Gateway — covering authentication mechanisms, authorization models, traffic protection, certificate management, and production security best practices.

---

## Quick Navigation

| # | File | Topic |
|---|------|-------|
| 01 | [API Security Overview](./01-%20API%20Security%20Overview.md) | Security architecture of API Gateway, authentication vs authorization, layered security model |
| 02 | [IAM Authorization](./02-%20IAM%20Authorization.md) | IAM policies and AWS Signature Version 4 (SigV4) for service-to-service communication |
| 03 | [Resource Policies](./03-%20Resource%20Policies.md) | Control who can invoke APIs using resource-based IAM policies, IP restrictions, and cross-account access |
| 04 | [Lambda Authorizers](./04-%20Lambda%20Authorizers.md) | Custom authentication and authorization logic using AWS Lambda |
| 05 | [Amazon Cognito Authorizers](./05-%20Amazon%20Cognito%20Authorizers.md) | Integration with Amazon Cognito User Pools for managed JWT-based authentication |
| 06 | [JWT Authorizers (HTTP API)](./06-%20JWT%20Authorizers%20(HTTP%20API).md) | Native JWT validation for HTTP APIs using OIDC providers such as Cognito, Auth0, and Okta |
| 07 | [API Keys & Usage Plans](./07-%20API%20Keys%20%26%20Usage%20Plans.md) | Consumer identification, request quotas, rate limiting, and subscription plans |
| 08 | [Mutual TLS (mTLS)](./08-%20Mutual%20TLS%20(mTLS).md) | Strong client authentication using X.509 certificates for enterprise and B2B APIs |
| 09 | [AWS WAF Integration](./09-%20AWS%20WAF%20Integration.md) | Protect APIs from SQL Injection, XSS, bots, and malicious IPs using AWS WAF |
| 10 | [Custom Domain Names & ACM](./10-%20Custom%20Domain%20Names%20%26%20ACM.md) | Branded API endpoints, HTTPS certificates with ACM, Base Path Mapping, and custom domains |
| 11 | [Security Best Practices](./11-%20Security%20Best%20Practices.md) | Defense-in-depth, production security recommendations, and common mistakes to avoid |
| 12 | [CORS](./12-%20CORS.md) | Configuring Cross-Origin Resource Sharing for browser-based clients |

---

## Recommended Study Order

1. [API Security Overview](./01-%20API%20Security%20Overview.md)
2. [IAM Authorization](./02-%20IAM%20Authorization.md)
3. [Resource Policies](./03-%20Resource%20Policies.md)
4. [Lambda Authorizers](./04-%20Lambda%20Authorizers.md)
5. [Amazon Cognito Authorizers](./05-%20Amazon%20Cognito%20Authorizers.md)
6. [JWT Authorizers (HTTP API)](./06-%20JWT%20Authorizers%20(HTTP%20API).md)
7. [API Keys & Usage Plans](./07-%20API%20Keys%20%26%20Usage%20Plans.md)
8. [Mutual TLS (mTLS)](./08-%20Mutual%20TLS%20(mTLS).md)
9. [AWS WAF Integration](./09-%20AWS%20WAF%20Integration.md)
10. [Custom Domain Names & ACM](./10-%20Custom%20Domain%20Names%20%26%20ACM.md)
11. [Security Best Practices](./11-%20Security%20Best%20Practices.md)
12. [CORS](./12-%20CORS.md)

---

## Related Sections

- [01 - Concepts → Amazon API Gateway](../../01-%20Concepts/07-%20Amazon%20API%20Gateway/README.md)
- [02 - Architecture → Amazon API Gateway](../../02-%20Architecture/07-%20Amazon%20API%20Gateway/README.md)
- [04 - Operations → Amazon API Gateway](../../04-%20Operations/07-%20Amazon%20API%20Gateway/README.md)
- [06 - Deployment → Amazon API Gateway](../../06-%20Deployment/01-%20Amazon%20API%20Gateway/README.md)
- [07 - Troubleshooting → Amazon API Gateway](../../07-%20Troubleshooting/06-%20Amazon%20API%20Gateway/README.md)
- [08 - Interview Questions → Amazon API Gateway](../../08-%20Interview%20Questions/07-%20Amazon%20API%20Gateway/README.md)
- [09 - Integrations → Amazon API Gateway](../../09-%20Integrations/01-%20Amazon%20API%20Gateway/README.md)
- [10 - Hands On → Amazon API Gateway](../../10-%20Hands%20On/01-%20Amazon%20API%20Gateway/README.md)
- [11 - Best Practices → Amazon API Gateway](../../11-%20Best%20Practices/01-%20Amazon%20API%20Gateway/README.md)
