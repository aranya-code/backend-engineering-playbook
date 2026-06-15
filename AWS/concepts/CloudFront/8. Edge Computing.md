# AWS CloudFront - Section 08: Edge Computing

# What is Edge Computing?

Traditionally, requests travel to the backend before any processing occurs.

Example:

```text
User
  |
CloudFront
  |
Origin
```

All logic executes at:

```text
Origin
```

Problems:

- Increased latency
- More origin load
- Higher costs
- Slower user experience

---

## Edge Computing Solution

Move logic closer to users.

```text
User
  |
Edge Location
  |
Origin
```

Processing occurs at AWS Edge Locations.

Benefits:

- Lower latency
- Faster response times
- Reduced origin traffic
- Better scalability

---

# Why Edge Computing Matters

Suppose a user requests:

```text
/company
```

Requirement:

```text
Redirect to:

/about-us
```

Without Edge Computing:

```text
User
  |
Origin
  |
Redirect
```

Origin must process request.

---

With Edge Computing:

```text
User
  |
Edge Location
  |
Redirect
```

Origin never contacted.

Much faster.

---

# CloudFront Edge Compute Services

CloudFront provides:

```text
1. CloudFront Functions
2. Lambda@Edge
```

Both run code at edge locations.

However, they solve different problems.

---

# CloudFront Functions

## What are CloudFront Functions?

A lightweight serverless compute service designed for:

```text
High Scale
Low Latency
Simple Logic
```

Runs directly at Edge Locations.

---

# Purpose

Designed for:

```text
Request Manipulation
Response Manipulation
```

Very fast execution.

---

# Architecture

```text
User
  |
CloudFront Function
  |
CloudFront Cache
  |
Origin
```

---

# Supported Events

CloudFront Functions support:

```text
Viewer Request
Viewer Response
```

Only.

---

# Viewer Request

Triggered before CloudFront processes request.

Flow:

```text
User
  |
Viewer Request
  |
CloudFront
```

---

# Viewer Response

Triggered before response is returned.

Flow:

```text
CloudFront
  |
Viewer Response
  |
User
```

---

# Common Use Cases

## URL Rewriting

Example:

```text
/index
```

Convert to:

```text
/index.html
```

---

## Redirects

Example:

```text
/company
```

Redirect:

```text
/about-us
```

---

## Header Manipulation

Add:

```http
X-Company: ABC
```

---

## Authentication Checks

Simple token validation.

---

# CloudFront Function Example

Request:

```text
/company
```

Function:

```javascript
if (request.uri === "/company") {
  request.uri = "/about-us";
}
```

No origin interaction required.

---

# Benefits

## Extremely Fast

Runs in milliseconds.

---

## Low Cost

Cheaper than Lambda@Edge.

---

## Massive Scale

Handles millions of requests.

---

## Global Execution

Runs at every Edge Location.

---

# Limitations

CloudFront Functions:

```text
Cannot Access Network
Cannot Call APIs
Cannot Access Databases
```

Designed for lightweight logic only.

---

# Lambda@Edge

## What is Lambda@Edge?

Lambda@Edge extends AWS Lambda to CloudFront.

Allows execution of Lambda functions at Edge Locations.

---

# Architecture

```text
User
  |
Lambda@Edge
  |
CloudFront
  |
Origin
```

---

# Why Lambda@Edge Exists

Some workloads require more advanced logic.

Examples:

```text
Authentication
Personalization
Dynamic Content
API Calls
```

CloudFront Functions are too limited.

Lambda@Edge solves this.

---

# Lambda@Edge Triggers

Supports four events:

```text
Viewer Request
Viewer Response
Origin Request
Origin Response
```

---

# Viewer Request

Runs before cache lookup.

Flow:

```text
User
  |
Viewer Request
  |
CloudFront
```

---

# Viewer Response

Runs before response reaches user.

Flow:

```text
CloudFront
  |
Viewer Response
  |
User
```

---

# Origin Request

Runs before CloudFront contacts origin.

Flow:

```text
CloudFront
  |
Origin Request
  |
Origin
```

---

# Origin Response

Runs when origin responds.

Flow:

```text
Origin
  |
Origin Response
  |
CloudFront
```

---

# Lambda@Edge Use Cases

## Authentication

Validate JWT tokens.

Example:

```text
User
  |
Lambda@Edge
  |
Origin
```

Unauthorized users blocked.

---

## Personalization

Serve content based on:

```text
Country
Language
User Type
```

---

## A/B Testing

Route users:

```text
50% -> Version A
50% -> Version B
```

---

## Dynamic Origin Selection

Route requests to different origins.

Example:

```text
US Users -> Origin A
EU Users -> Origin B
```

---

## Security Processing

Advanced request validation.

---

# Lambda@Edge Example

Request:

```text
/login
```

Lambda:

```javascript
Validate JWT
```

If valid:

```text
Allow
```

If invalid:

```text
403 Forbidden
```

---

# CloudFront Functions vs Lambda@Edge

| Feature | CloudFront Functions | Lambda@Edge |
|----------|---------------------|-------------|
| Complexity | Simple | Advanced |
| Cost | Lower | Higher |
| Performance | Faster | Slower |
| Network Access | No | Limited AWS Integration |
| Execution Time | Very Short | Longer |
| Use Cases | URL Rewrite | Authentication |
| Triggers | 2 | 4 |

---

# When to Use CloudFront Functions

Choose CloudFront Functions when:

```text
Simple Logic
Low Latency
Massive Scale
```

Examples:

- URL rewrites
- Redirects
- Header updates
- Lightweight validation

---

# When to Use Lambda@Edge

Choose Lambda@Edge when:

```text
Advanced Logic
Authentication
Personalization
Origin Control
```

Examples:

- JWT validation
- Dynamic routing
- User personalization
- A/B testing

---

# Real-World Architecture

## Redirect Architecture

```text
User
  |
CloudFront Function
  |
CloudFront
  |
Origin
```

---

## Authentication Architecture

```text
User
  |
Lambda@Edge
  |
CloudFront
  |
Origin
```

---

## Geo-Based Routing

```text
US User
   |
Lambda@Edge
   |
US Origin

EU User
   |
Lambda@Edge
   |
EU Origin
```

---

# Edge Computing Benefits

## Lower Latency

Processing closer to users.

---

## Reduced Origin Load

Many requests never reach backend.

---

## Improved Scalability

Distributed processing.

---

## Better User Experience

Faster responses.

---

# Common Mistakes

## Using Lambda@Edge for Simple Redirects

Bad:

```text
Higher Cost
```

Better:

```text
CloudFront Functions
```

---

## Using CloudFront Functions for Authentication

Bad:

```text
Limited Capability
```

Better:

```text
Lambda@Edge
```

---

## Running Excessive Logic

Keep edge processing lightweight.

---

# Troubleshooting

## Function Not Triggering

Check:

```text
Associated Event
Distribution Deployment
```

---

## High Costs

Possible Causes:

```text
Excessive Lambda Executions
```

Review architecture.

---

## Slow Performance

Possible Causes:

```text
Complex Lambda Logic
```

Optimize execution.

---

# Interview Questions

## Q1. What is Edge Computing?

Running application logic closer to users instead of at the origin.

---

## Q2. What is CloudFront Functions?

A lightweight edge compute service used for request and response manipulation.

---

## Q3. What is Lambda@Edge?

A serverless compute service that runs Lambda functions at CloudFront Edge Locations.

---

## Q4. Difference Between CloudFront Functions and Lambda@Edge?

CloudFront Functions:

```text
Fast
Cheap
Simple
```

Lambda@Edge:

```text
Powerful
Flexible
More Expensive
```

---

## Q5. When would you use CloudFront Functions?

For:

- Redirects
- URL Rewrites
- Header Manipulation

---

## Q6. When would you use Lambda@Edge?

For:

- Authentication
- Personalization
- Dynamic Routing
- A/B Testing

---

## Q7. Which service should be used for JWT validation?

```text
Lambda@Edge
```

because authentication logic is more complex.

---

## Q8. Which service should be used for URL rewrites?

```text
CloudFront Functions
```

because it is faster and cheaper.

---

# Summary

Key Takeaways:

- Edge Computing moves logic closer to users.
- CloudFront Functions provide lightweight edge processing.
- Lambda@Edge provides advanced edge processing.
- CloudFront Functions support Viewer Request and Viewer Response.
- Lambda@Edge supports all four CloudFront events.
- CloudFront Functions are ideal for simple logic.
- Lambda@Edge is ideal for authentication, personalization, and advanced routing.
- Choosing the correct edge compute service improves performance and reduces cost.

