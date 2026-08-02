# Stage Variables

## Overview

Amazon API Gateway supports **Stage Variables**, which are key-value pairs associated with an API stage. They allow you to parameterize API configurations without modifying the API definition itself.

Stage Variables are commonly used to:

- Switch backend endpoints
- Select different Lambda functions
- Configure environment-specific values
- Avoid duplicating API definitions
- Simplify deployments across environments

Think of Stage Variables as **environment variables for an API Gateway stage**.

Instead of hardcoding backend URLs or resource names, API Gateway can dynamically resolve them using Stage Variables.

---

# Why Stage Variables?

Suppose you have three environments:

```text
Development

↓

https://dev-api.example.com

----------------------

Testing

↓

https://test-api.example.com

----------------------

Production

↓

https://api.example.com
```

Without Stage Variables, you might create separate API configurations for each environment.

With Stage Variables:

```text
Single API

↓

Stage Variable

↓

Correct Backend
```

The same API configuration works across all environments.

---

# Architecture

```text
              Client

                 │

                 ▼

         Amazon API Gateway

                 │

          Stage Variable

                 │

      ┌──────────┼──────────┐

      ▼          ▼          ▼

    Dev URL   Test URL   Prod URL
```

Each stage resolves its own variable values.

---

# How Stage Variables Work

Example stage:

```text
Development
```

Variable:

```text
backendUrl

↓

https://dev.example.com
```

Production stage:

```text
backendUrl

↓

https://api.example.com
```

The API uses the same configuration but resolves different values.

---

# Creating Stage Variables

Each variable consists of:

```text
Key

↓

backendUrl

---------------------

Value

↓

https://api.example.com
```

Variables are stored per stage.

---

# Example

Development stage:

| Variable | Value |
|----------|-------|
| backendUrl | https://dev.example.com |

Production stage:

| Variable | Value |
|----------|-------|
| backendUrl | https://api.example.com |

The backend changes automatically depending on the stage.

---

# Referencing Stage Variables

Stage Variables are referenced using:

```text
${stageVariables.variableName}
```

Example:

```text
${stageVariables.backendUrl}
```

API Gateway substitutes the actual value during request processing.

---

# HTTP Integration Example

Instead of:

```text
https://api.example.com/orders
```

Configure:

```text
${stageVariables.backendUrl}/orders
```

Development:

```text
https://dev.example.com/orders
```

Production:

```text
https://api.example.com/orders
```

---

# Lambda Integration Example

Development:

```text
OrderService-Dev
```

Production:

```text
OrderService-Prod
```

Stage Variable:

```text
lambdaFunction

↓

OrderService-Dev
```

or

```text
lambdaFunction

↓

OrderService-Prod
```

The integration changes automatically.

---

# Environment Configuration

```text
             API Gateway

                  │

          Stage Variables

                  │

     ┌────────────┼────────────┐

     ▼            ▼            ▼

 Development   Testing   Production
```

Each environment has independent configuration.

---

# Common Use Cases

Stage Variables are commonly used for:

- Environment-specific endpoints
- Lambda aliases
- Different databases
- Feature toggles
- External service URLs
- Version selection

---

# Feature Toggle Example

Development:

```text
newCheckout

↓

true
```

Production:

```text
newCheckout

↓

false
```

The backend can behave differently based on the stage.

---

# Lambda Alias Example

Development:

```text
Alias

↓

dev
```

Production:

```text
Alias

↓

prod
```

Stage Variable:

```text
lambdaAlias
```

API Gateway invokes the correct Lambda alias.

---

# Stage Variables vs Environment Variables

| Stage Variables | Lambda Environment Variables |
|-----------------|------------------------------|
| API Gateway | Lambda Function |
| Configure Integrations | Configure Application |
| Per Stage | Per Function |
| Routing Configuration | Business Configuration |

Stage Variables affect API Gateway configuration, while environment variables configure application behavior.

---

# Stage Variables vs API Parameters

| Stage Variables | Request Parameters |
|-----------------|-------------------|
| Defined by API Gateway | Supplied by Client |
| Environment Configuration | Request Data |
| Static per Stage | Dynamic per Request |

Stage Variables are not sent by clients.

---

# Advantages

## Single API Definition

One API can serve multiple environments.

---

## Easier Deployments

No need to duplicate APIs for different stages.

---

## Flexible Configuration

Backend URLs and integrations can change without modifying resources.

---

## Cleaner Architecture

Environment-specific values remain outside API definitions.

---

# Limitations

Stage Variables:

- Are not encrypted
- Should not store secrets
- Are visible to API Gateway configuration
- Are intended for configuration only

Sensitive values should be stored in:

- AWS Secrets Manager
- Systems Manager Parameter Store

---

# Security Considerations

Never store:

- Database passwords
- API Keys
- AWS Credentials
- JWT Secrets

inside Stage Variables.

Instead:

```text
Stage Variable

↓

Secret Name

↓

Secrets Manager

↓

Actual Secret
```

---

# Real-World Example

An application has three environments.

```text
Customer

↓

API Gateway

↓

Stage Variable

↓

Production Backend
```

Developers deploy the same API to Development and Testing without changing integration definitions.

---

# Best Practices

- Use Stage Variables only for configuration.
- Keep the same variable names across all environments.
- Do not store secrets in Stage Variables.
- Use Lambda aliases with Stage Variables for safer deployments.
- Document all Stage Variables used by an API.
- Use meaningful names such as `backendUrl`, `lambdaAlias`, and `apiVersion`.

---

# Common Interview Questions

### What are Stage Variables?

Stage Variables are key-value pairs associated with an API Gateway stage that allow environment-specific configuration without modifying the API definition.

---

### What are Stage Variables commonly used for?

They are commonly used to configure backend URLs, Lambda aliases, API versions, feature flags, and environment-specific settings.

---

### Are Stage Variables encrypted?

No.

Stage Variables should not contain sensitive information. Use AWS Secrets Manager or Systems Manager Parameter Store for secrets.

---

### Can Stage Variables change backend integrations?

Yes.

Stage Variables are frequently used to dynamically select different backend endpoints or Lambda aliases for different deployment stages.

---

### What is the difference between Stage Variables and Lambda Environment Variables?

Stage Variables configure API Gateway behavior, while Lambda Environment Variables configure the Lambda function itself.

---

# Key Takeaways

- Stage Variables allow API Gateway to store environment-specific configuration as key-value pairs.
- They enable a single API definition to work across development, testing, and production environments.
- Common uses include backend URLs, Lambda aliases, feature flags, and API version selection.
- Stage Variables should never store sensitive information such as passwords or API keys.
- Using Stage Variables simplifies deployments, reduces duplication, and improves maintainability across multiple environments.