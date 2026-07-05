# API Destinations

Amazon EventBridge API Destinations allow EventBridge to send events directly to external HTTP APIs. This enables AWS applications to integrate with third-party services without writing custom integration code.

API Destinations extend EventBridge beyond AWS by allowing events to trigger REST APIs hosted anywhere on the internet.

------------------------------------------------------------------------

# What are API Destinations?

An API Destination is an HTTP endpoint that receives events from EventBridge.

Instead of sending events only to AWS services, EventBridge can invoke external applications.

Examples:

- Slack
- Jira
- GitHub
- ServiceNow
- PagerDuty
- Custom REST APIs

------------------------------------------------------------------------

# Why Use API Destinations?

API Destinations help you:

- Integrate SaaS applications
- Automate notifications
- Trigger external workflows
- Reduce custom integration code
- Build hybrid cloud solutions

------------------------------------------------------------------------

# How API Destinations Work

```text
AWS Event

      |

      v

Amazon EventBridge

      |

      v

Connection

      |

      v

API Destination

      |

      v

External REST API
```

------------------------------------------------------------------------

# Components

API Destinations consist of:

- Connection
- API Destination
- Rule
- Target

Each component plays a specific role.

------------------------------------------------------------------------

# Connections

A Connection stores authentication information.

Supported authentication methods:

- API Key
- Basic Authentication
- OAuth 2.0

Connections allow EventBridge to authenticate securely with external services.

------------------------------------------------------------------------

# API Key Authentication

Example:

```text
API Key

↓

EventBridge Connection

↓

REST API
```

Used by many third-party APIs.

------------------------------------------------------------------------

# Basic Authentication

Uses:

- Username
- Password

Suitable for legacy REST APIs.

------------------------------------------------------------------------

# OAuth Authentication

Supports OAuth 2.0.

Useful for:

- GitHub
- Slack
- Microsoft APIs
- Google APIs

Tokens are managed securely by EventBridge.

------------------------------------------------------------------------

# Rate Limits

API Destinations support invocation rate limits.

Benefits:

- Prevent API throttling
- Protect external services
- Improve reliability

------------------------------------------------------------------------

# Retry Behavior

If an API call fails:

- EventBridge retries automatically.
- Retry policies can be configured.
- Failed events can be sent to a Dead-Letter Queue.

------------------------------------------------------------------------

# Common Use Cases

- Send Slack notifications
- Create Jira tickets
- Trigger ServiceNow incidents
- Update CRM systems
- Call external microservices

------------------------------------------------------------------------

# Real-World Example

A security event occurs in AWS.

```text
CloudTrail

↓

EventBridge

↓

API Destination

↓

Slack
```

The security team immediately receives a Slack notification.

------------------------------------------------------------------------

# Best Practices

- Store credentials using Connections.
- Configure retry policies.
- Configure DLQs.
- Secure external APIs with OAuth where possible.
- Monitor failures using CloudWatch.

------------------------------------------------------------------------

# Key Takeaways

- API Destinations connect EventBridge to external REST APIs.
- Connections securely manage authentication.
- Supports API Key, Basic Authentication, and OAuth.
- Enables serverless integration with SaaS platforms.