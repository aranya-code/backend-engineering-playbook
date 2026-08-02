# Security & Authorizers

## Overview

Security is one of the most important aspects of API Gateway. Before a request reaches your backend service, API Gateway can authenticate the caller, authorize access, and reject unauthorized requests.

Using the AWS CLI, you can automate the creation and management of:

- IAM Authorization
- Lambda Authorizers
- Cognito Authorizers
- JWT Authorizers
- Resource Policies

These operations are commonly automated in CI/CD pipelines and infrastructure provisioning scripts.

---

# Authentication Flow

```text
Client

↓

API Gateway

↓

Authorizer

↓

Authorized?

↓

Yes

↓

Backend

-------------------

No

↓

401 / 403
```

Authorization happens before your backend is invoked.

---

# Authorization Types

| Authorization Type | Supported By |
|--------------------|--------------|
| NONE | REST & HTTP APIs |
| AWS IAM | REST & HTTP APIs |
| Cognito User Pools | REST APIs |
| Lambda Authorizer | REST & HTTP APIs |
| JWT Authorizer | HTTP APIs |

---

# Create a Lambda Authorizer (REST API)

```bash
aws apigateway create-authorizer \
    --rest-api-id abc123 \
    --name ProductAuthorizer \
    --type TOKEN \
    --authorizer-uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:AuthFunction/invocations \
    --identity-source method.request.header.Authorization
```

Example output:

```json
{
    "id": "auth123",
    "name": "ProductAuthorizer"
}
```

---

# Lambda Authorizer Types

REST APIs support:

```text
TOKEN
```

and

```text
REQUEST
```

### TOKEN

```text
Authorization Header

↓

Lambda
```

### REQUEST

Can validate:

- Headers
- Query Parameters
- Path Parameters
- Stage Variables

---

# List Authorizers

```bash
aws apigateway get-authorizers \
    --rest-api-id abc123
```

---

# View Authorizer

```bash
aws apigateway get-authorizer \
    --rest-api-id abc123 \
    --authorizer-id auth123
```

---

# Delete Authorizer

```bash
aws apigateway delete-authorizer \
    --rest-api-id abc123 \
    --authorizer-id auth123
```

---

# Attach Authorizer to a Method

```bash
aws apigateway update-method \
    --rest-api-id abc123 \
    --resource-id resource123 \
    --http-method GET \
    --patch-operations \
    op=replace,path=/authorizationType,value=CUSTOM \
    op=replace,path=/authorizerId,value=auth123
```

Now every request to this method is validated by the Lambda Authorizer.

---

# Configure IAM Authorization

Replace:

```text
NONE
```

with:

```text
AWS_IAM
```

```bash
aws apigateway update-method \
    --rest-api-id abc123 \
    --resource-id resource123 \
    --http-method GET \
    --patch-operations \
    op=replace,path=/authorizationType,value=AWS_IAM
```

Clients must sign requests using AWS Signature Version 4 (SigV4).

---

# Configure Cognito Authorization (REST API)

Create an authorizer.

```bash
aws apigateway create-authorizer \
    --rest-api-id abc123 \
    --name CognitoAuth \
    --type COGNITO_USER_POOLS \
    --provider-arns arn:aws:cognito-idp:us-east-1:123456789012:userpool/us-east-1_xxxxx \
    --identity-source method.request.header.Authorization
```

---

# JWT Authorizer (HTTP API)

Create:

```bash
aws apigatewayv2 create-authorizer \
    --api-id xyz789 \
    --authorizer-type JWT \
    --name JwtAuthorizer \
    --identity-source '$request.header.Authorization' \
    --jwt-configuration Audience=client-id,Issuer=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_xxxxx
```

Example output:

```json
{
    "AuthorizerId":"jwt123"
}
```

---

# List HTTP API Authorizers

```bash
aws apigatewayv2 get-authorizers \
    --api-id xyz789
```

---

# View JWT Authorizer

```bash
aws apigatewayv2 get-authorizer \
    --api-id xyz789 \
    --authorizer-id jwt123
```

---

# Delete JWT Authorizer

```bash
aws apigatewayv2 delete-authorizer \
    --api-id xyz789 \
    --authorizer-id jwt123
```

---

# Attach JWT Authorizer to a Route

```bash
aws apigatewayv2 update-route \
    --api-id xyz789 \
    --route-id route123 \
    --authorization-type JWT \
    --authorizer-id jwt123
```

Now the route requires a valid JWT.

---

# Remove Authorization

REST API:

```bash
aws apigateway update-method \
    --rest-api-id abc123 \
    --resource-id resource123 \
    --http-method GET \
    --patch-operations \
    op=replace,path=/authorizationType,value=NONE
```

HTTP API:

```bash
aws apigatewayv2 update-route \
    --api-id xyz789 \
    --route-id route123 \
    --authorization-type NONE
```

---

# View Route Authorization

```bash
aws apigatewayv2 get-routes \
    --api-id xyz789
```

Example:

```text
GET /products

↓

JWT
```

---

# Resource Policies

Retrieve the REST API configuration.

```bash
aws apigateway get-rest-api \
    --rest-api-id abc123
```

Update the resource policy:

```bash
aws apigateway update-rest-api \
    --rest-api-id abc123 \
    --patch-operations \
    op=replace,path=/policy,value=file://policy.json
```

Example use cases:

- Restrict by AWS Account
- Restrict by VPC
- Restrict by VPC Endpoint
- Restrict by IP Address

---

# Lambda Permission

Allow API Gateway to invoke Lambda.

```bash
aws lambda add-permission \
    --function-name ProductAPI \
    --statement-id apigateway \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com
```

Without this permission, API Gateway returns:

```text
500 Internal Server Error
```

---

# Verify Authorization

REST API:

```bash
aws apigateway get-method \
    --rest-api-id abc123 \
    --resource-id resource123 \
    --http-method GET
```

HTTP API:

```bash
aws apigatewayv2 get-route \
    --api-id xyz789 \
    --route-id route123
```

---

# Security Architecture

```text
Client

↓

JWT / IAM

↓

API Gateway

↓

Authorizer

↓

Lambda

↓

Backend
```

Unauthorized requests never reach the backend.

---

# Automation Example

```bash
API_ID=xyz789

aws apigatewayv2 create-authorizer \
--api-id $API_ID \
--authorizer-type JWT \
--name JwtAuthorizer \
--identity-source '$request.header.Authorization'
```

---

# Common Errors

## 401 Unauthorized

Cause:

```text
Missing or Invalid Token
```

Verify:

- Authorization Header
- JWT Token
- Cognito Configuration

---

## 403 Forbidden

Cause:

```text
IAM Policy Denied
```

Review:

- IAM Permissions
- Resource Policies

---

## Invalid Authorizer

Verify:

```bash
aws apigateway get-authorizers \
--rest-api-id abc123
```

or

```bash
aws apigatewayv2 get-authorizers \
--api-id xyz789
```

---

## Lambda Invocation Failed

Verify:

```bash
aws lambda get-policy \
--function-name ProductAPI
```

Ensure API Gateway has invoke permission.

---

# CLI Best Practices

- Prefer JWT Authorizers for HTTP APIs.
- Use Cognito for managed user authentication.
- Use IAM authorization for AWS-to-AWS communication.
- Use Lambda Authorizers only when custom authorization logic is required.
- Apply least-privilege IAM policies.
- Restrict Private APIs using Resource Policies.
- Automate authorizer creation using Infrastructure as Code.

---

# Common Interview Questions

### What is the difference between authentication and authorization?

Authentication verifies **who** the caller is, while authorization determines **what** the authenticated caller is allowed to do.

---

### When should you use a JWT Authorizer?

JWT Authorizers are the preferred choice for HTTP APIs when using OpenID Connect (OIDC) providers or Amazon Cognito because API Gateway validates tokens without invoking a Lambda function.

---

### When should you use a Lambda Authorizer?

Lambda Authorizers are appropriate when authorization requires custom business logic, external identity providers, or dynamic permission evaluation that cannot be handled by standard JWT validation.

---

### Why use IAM authorization?

IAM authorization is ideal for service-to-service communication within AWS, allowing requests signed with AWS Signature Version 4 (SigV4) to be authenticated using IAM identities and policies.

---

### What are Resource Policies used for?

Resource Policies control **who can invoke an API** by restricting access based on AWS accounts, VPCs, VPC Endpoints, or IP addresses, providing an additional layer of security beyond authentication.

---

# Key Takeaways

- API Gateway supports multiple authorization mechanisms, including IAM, Cognito, Lambda Authorizers, and JWT Authorizers.
- REST APIs use `aws apigateway`, while HTTP APIs use `aws apigatewayv2` for managing authorizers.
- JWT Authorizers are generally the preferred choice for HTTP APIs because they eliminate the need for custom authorization code.
- Lambda Authorizers provide flexibility for custom authentication and authorization requirements.
- Combining authentication, authorization, Resource Policies, and least-privilege IAM creates a robust, production-grade API security model.