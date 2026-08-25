# CORS Issues

## Overview

**Cross-Origin Resource Sharing (CORS)** is one of the most common causes of API Gateway issues during frontend development.

Interestingly, most CORS problems are **not API Gateway problems**—they are browser security restrictions.

A common symptom is:

```text
The API works perfectly in Postman,

but fails in Chrome or Firefox.
```

This guide explains the most common CORS issues, how to identify them, and how to resolve them in Amazon API Gateway.

---

# What is CORS?

Browsers enforce the **Same-Origin Policy**.

Example:

```text
Frontend

https://app.company.com

↓

API

https://api.company.com
```

Since these are different origins, the browser requires CORS headers before allowing JavaScript to access the response.

---

# CORS Request Flow

```text
Browser

↓

OPTIONS Request

↓

API Gateway

↓

Allowed?

↓

Yes

↓

Actual Request

↓

Backend
```

If the preflight request fails, the browser never sends the actual request.

---

# Common CORS Errors

| Browser Error | Typical Cause |
|---------------|---------------|
| No 'Access-Control-Allow-Origin' | CORS disabled |
| CORS Preflight Failed | OPTIONS not configured |
| Method Not Allowed | Missing HTTP method |
| Request Header Not Allowed | Missing allowed header |
| Credentials Error | Invalid credentials configuration |

---

# No Access-Control-Allow-Origin Header

## Browser Error

```text
Access to fetch has been blocked by CORS policy.

No 'Access-Control-Allow-Origin' header is present.
```

---

## Common Causes

- CORS Disabled
- Backend Missing Header
- API Gateway Missing Header

---

## Diagnose

Inspect:

Browser

↓

Developer Tools

↓

Network

↓

Response Headers

Verify:

```http
Access-Control-Allow-Origin
```

---

## Solution

Enable CORS.

Return:

```http
Access-Control-Allow-Origin:
https://app.company.com
```

---

# OPTIONS Request Returns 403

## Browser Error

```text
Response to preflight request doesn't pass access control check.
```

---

## Common Causes

- OPTIONS Route Missing
- OPTIONS Unauthorized
- OPTIONS Blocked

---

## Diagnose

Network Tab

↓

OPTIONS Request

↓

Status Code

---

## Solution

Create:

```text
OPTIONS
```

method.

Allow anonymous access.

---

# OPTIONS Request Returns 404

## Symptoms

```text
OPTIONS

↓

404
```

---

## Common Causes

- Route Missing
- Resource Missing

---

## Solution

Configure:

```text
OPTIONS

↓

Resource

↓

Method
```

or enable automatic CORS support.

---

# Access-Control-Allow-Headers Missing

## Browser Error

```text
Request header is not allowed.
```

---

## Example

Frontend sends:

```http
Authorization
```

Server allows:

```http
Content-Type
```

Only.

---

## Solution

Add:

```http
Access-Control-Allow-Headers:

Authorization

Content-Type

Accept
```

---

# Access-Control-Allow-Methods Missing

## Browser Error

```text
Method PUT is not allowed.
```

---

## Example

Browser:

```http
PUT
```

Allowed:

```http
GET

POST
```

---

## Solution

Return:

```http
Access-Control-Allow-Methods

GET

POST

PUT

DELETE

OPTIONS
```

---

# Credentials Error

Browser Error

```text
Credentials flag is true,

but Access-Control-Allow-Origin is '*'
```

---

## Cause

Cannot combine:

```http
Allow-Credentials: true
```

with

```http
Access-Control-Allow-Origin: *
```

---

## Solution

Specify the exact origin.

Example:

```http
Access-Control-Allow-Origin:

https://app.company.com
```

---

# Authorization Header Blocked

Example

Frontend:

```http
Authorization:
Bearer eyJ...
```

Browser:

```text
Blocked
```

---

## Cause

Missing:

```http
Access-Control-Allow-Headers

Authorization
```

---

## Solution

Add:

```http
Authorization
```

to allowed headers.

---

# Custom Header Blocked

Example:

```http
X-Request-ID
```

---

## Cause

Custom header not allowed.

---

## Solution

Return:

```http
Access-Control-Allow-Headers

X-Request-ID
```

---

# CORS Works in Postman

Symptoms

```text
Postman

↓

Success

Browser

↓

Failure
```

---

## Explanation

Postman does **not** enforce browser CORS rules.

Only browsers perform CORS validation.

---

## Solution

Test using:

- Chrome
- Firefox
- Edge

when validating CORS.

---

# Lambda Missing CORS Headers

Example:

```json
{
    "statusCode":200,
    "body":"{}"
}
```

Missing:

```http
Access-Control-Allow-Origin
```

---

## Solution

Return:

```json
{
    "statusCode":200,
    "headers":{
        "Access-Control-Allow-Origin":"https://app.company.com"
    },
    "body":"{}"
}
```

---

# API Gateway CORS Disabled

Symptoms

```text
Everything Works

↓

Browser Rejects Response
```

---

## Diagnose

Review:

API Gateway

↓

CORS Configuration

---

## Solution

Enable:

- Allowed Origins
- Allowed Methods
- Allowed Headers

---

# Wrong Allowed Origin

Example

Configured:

```text
https://company.com
```

Browser:

```text
https://app.company.com
```

---

## Solution

Configure the exact origin.

---

# Wildcard Origin Used

Example:

```http
Access-Control-Allow-Origin: *
```

---

## Problems

- Credentials unsupported
- Poor security
- Production risk

---

## Recommendation

Production:

```http
https://app.company.com
```

Development:

```http
http://localhost:3000
```

---

# Preflight Never Reaches Lambda

Flow

```text
Browser

↓

OPTIONS

↓

API Gateway

↓

Rejected
```

Lambda is never invoked.

---

## Solution

Configure CORS correctly in API Gateway.

---

# Missing Exposed Headers

Example

Backend returns:

```http
X-Request-ID
```

Browser cannot read it.

---

## Solution

Return:

```http
Access-Control-Expose-Headers

X-Request-ID
```

---

# Debugging Workflow

```text
Browser Error

↓

Network Tab

↓

OPTIONS

↓

Headers

↓

API Gateway

↓

Backend

↓

Fixed
```

---

# Browser Developer Tools

Check:

Network

↓

OPTIONS

↓

Response Headers

Verify:

- Access-Control-Allow-Origin
- Access-Control-Allow-Headers
- Access-Control-Allow-Methods
- Status Code

---

# Production Checklist

Verify:

- OPTIONS enabled
- CORS enabled
- Correct Origin
- Correct Headers
- Correct Methods
- Authorization allowed
- Credentials configured
- Browser tested
- Lambda headers returned
- CloudWatch logs enabled

---

# Best Practices

- Allow only trusted origins.
- Avoid using `*` in production.
- Include only required HTTP methods.
- Explicitly allow required request headers.
- Test with real browsers instead of only Postman.
- Let API Gateway manage CORS where possible for HTTP APIs.
- Review CORS settings whenever frontend domains change.

---

# Common Interview Questions

### Why does an API work in Postman but fail in the browser?

Postman does not enforce the browser Same-Origin Policy. Browsers perform CORS validation and reject responses that do not include the required CORS headers.

---

### What is a preflight request?

A preflight request is an HTTP `OPTIONS` request sent by the browser before certain cross-origin requests to verify that the server allows the requested origin, method, and headers.

---

### Why shouldn't `Access-Control-Allow-Origin: *` be used in production?

Using `*` allows any origin to access the API and cannot be combined with credentialed requests. Production APIs should explicitly allow only trusted origins.

---

### Why is the `Authorization` header commonly blocked?

If `Authorization` is not included in `Access-Control-Allow-Headers`, the browser prevents the request from being sent, even though the backend may support authentication.

---

### How do you troubleshoot CORS issues?

Use the browser's Developer Tools to inspect the `OPTIONS` preflight request, verify the response headers, review API Gateway CORS configuration, and confirm that the backend returns the necessary CORS headers.

---

# Key Takeaways

- CORS is a browser security feature, not an API Gateway security mechanism.
- Most CORS issues are caused by missing or incorrect response headers, especially during preflight (`OPTIONS`) requests.
- API Gateway and Lambda must work together to return the appropriate CORS headers when required.
- Postman and curl do not validate CORS, so browser testing is essential.
- Correctly configuring origins, methods, headers, and credentials ensures secure and reliable communication between frontend applications and API Gateway.