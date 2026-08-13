# Secure API with Cognito

## Overview

In this hands-on project, you'll secure your REST API using **Amazon Cognito**.

So far, anyone with the API URL could invoke the endpoints. In production, APIs should only be accessible to authenticated users.

In this lab, you'll:

- Create a Cognito User Pool
- Create a test user
- Generate a JWT token
- Configure API Gateway JWT Authorization
- Protect API endpoints
- Test authenticated API requests

By the end, your API will only allow requests containing a valid JWT Access Token.

---

# What You'll Build

```text
                User

                  │

                  ▼

          Amazon Cognito

                  │

            JWT Access Token

                  │

                  ▼

          Amazon API Gateway

                  │

          JWT Authorizer

                  │

                  ▼

             AWS Lambda

                  │

                  ▼

             DynamoDB
```

---

# Prerequisites

Complete:

- Build Your First HTTP API
- Build a CRUD REST API

You should already have:

- API Gateway
- Lambda
- DynamoDB

---

# Step 1 — Create a Cognito User Pool

Open:

```text
AWS Console

↓

Amazon Cognito

↓

Create User Pool
```

Configuration:

| Setting | Value |
|----------|-------|
| Name | ProductAPIUsers |

Click:

```text
Create User Pool
```

---

# Step 2 — Configure Sign-in

Choose:

```text
Email
```

Users will log in using:

```text
user@example.com
```

---

# Step 3 — Configure Password Policy

Example:

```text
Minimum Length

↓

8 Characters
```

Require:

- Uppercase
- Lowercase
- Number
- Special Character

---

# Step 4 — Create an App Client

Navigate:

```text
User Pool

↓

App Clients

↓

Create App Client
```

Example:

```text
ProductAPIClient
```

No client secret is required for this lab.

---

# Step 5 — Create a Test User

Navigate:

```text
Users

↓

Create User
```

Example:

```text
Email

↓

john@example.com

Password

↓

Password@123
```

---

# Step 6 — Verify the User

Complete the initial login process.

Result:

```text
User

↓

Confirmed
```

---

# Step 7 — Generate an Access Token

Authenticate using the Cognito Hosted UI or an OAuth flow.

Successful authentication returns:

```json
{
  "access_token": "...",
  "id_token": "...",
  "refresh_token": "..."
}
```

The Access Token is used to call the API.

---

# Step 8 — Configure API Gateway

Open:

```text
API Gateway

↓

Authorizers

↓

Create Authorizer
```

Select:

```text
JWT Authorizer
```

---

# Step 9 — Configure JWT Authorizer

Provide:

| Setting | Value |
|----------|-------|
| Issuer | Cognito User Pool URL |
| Audience | App Client ID |

Save the authorizer.

---

# Step 10 — Protect Routes

Attach the authorizer to routes.

Example:

```text
GET /products

↓

JWT Required
```

Repeat for:

- POST /products
- PUT /products/{id}
- DELETE /products/{id}

---

# Request Flow

```text
Client

↓

JWT Token

↓

API Gateway

↓

JWT Validation

↓

Lambda

↓

DynamoDB
```

Unauthorized requests never reach Lambda.

---

# Calling the API

Example:

```http
GET /products
```

Headers:

```http
Authorization: Bearer eyJhbGci...
```

---

# Missing Token

Request:

```http
GET /products
```

Without:

```http
Authorization Header
```

Response:

```http
401 Unauthorized
```

---

# Invalid Token

Example:

```http
Authorization: Bearer invalid-token
```

Response:

```http
401 Unauthorized
```

---

# Expired Token

Example:

```text
JWT Expired
```

Response:

```http
401 Unauthorized
```

Obtain a new Access Token using the Refresh Token.

---

# Valid Token

Request:

```http
Authorization: Bearer eyJhb...
```

Response:

```http
200 OK
```

The Lambda function executes normally.

---

# Read JWT Claims

Lambda receives user information through the request context.

Typical claims include:

```text
User ID

↓

Email

↓

Groups

↓

Scopes
```

Applications can use these claims for authorization decisions.

---

# Test Using Postman

Method:

```text
GET
```

Headers:

```http
Authorization: Bearer <Access Token>
```

Expected:

```http
200 OK
```

---

# Test Without Authentication

Remove:

```http
Authorization Header
```

Expected:

```http
401 Unauthorized
```

This confirms that authentication is working.

---

# Authorization Example

Example policy:

```text
Admin

↓

Create Product

↓

Allowed

---------------------

Viewer

↓

Read Products

↓

Allowed

---------------------

Viewer

↓

Delete Product

↓

Denied
```

Authentication verifies identity.

Authorization determines permissions.

---

# Logging

Monitor:

- Authentication failures
- Successful requests
- JWT validation failures

Logs appear in:

```text
CloudWatch Logs
```

---

# Monitoring

Track:

- 401 responses
- 403 responses
- Request Count
- Latency
- Lambda Invocations

CloudWatch provides operational visibility.

---

# Production Improvements

A production implementation should additionally include:

- Multi-Factor Authentication (MFA)
- Password reset
- Email verification
- Refresh token rotation
- AWS WAF
- CloudFront
- Custom domain
- Rate limiting
- CloudWatch alarms
- CI/CD automation

---

# Production Architecture

```text
                  User

                    │

                    ▼

             Amazon Cognito

                    │

             Access Token

                    │

                    ▼

             Amazon API Gateway

                    │

            JWT Authorizer

                    │

                    ▼

               AWS Lambda

                    │

                    ▼

             Amazon DynamoDB
```

This architecture is widely used for secure serverless APIs.

---

# Cleanup

Delete:

- Cognito User Pool
- App Client
- Test User

if the resources are no longer required.

---

# What You Learned

In this project, you learned how to:

- Create a Cognito User Pool.
- Create an App Client.
- Register users.
- Generate JWT Access Tokens.
- Configure a JWT Authorizer.
- Secure API Gateway endpoints.
- Test authenticated API requests.

---

# Common Interview Questions

### Why use Cognito with API Gateway?

Cognito provides managed user authentication and issues JWT tokens that API Gateway can validate before forwarding requests to backend services.

---

### Which token should be sent to API Gateway?

The **Access Token** is typically used to authorize API requests.

---

### What happens if a JWT token is invalid?

API Gateway rejects the request and returns:

```http
401 Unauthorized
```

The backend service is never invoked.

---

### What is the advantage of validating JWTs in API Gateway?

Authentication is centralized, reducing duplicate code in backend services and preventing unauthorized requests from consuming backend resources.

---

### Can backend services still perform authorization?

Yes.

API Gateway authenticates the user, while backend services can use JWT claims (such as roles or groups) to implement fine-grained authorization.

---

# Key Takeaways

- Amazon Cognito provides a fully managed authentication solution for API Gateway.
- JWT Authorizers validate Access Tokens before requests reach backend services.
- Authentication is centralized in API Gateway, reducing backend complexity.
- Unauthorized or expired tokens are rejected automatically with HTTP 401 responses.
- Combining Cognito, API Gateway, Lambda, and DynamoDB creates a secure, scalable, and production-ready serverless API architecture.