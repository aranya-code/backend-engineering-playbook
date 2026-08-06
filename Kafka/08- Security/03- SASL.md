# SASL (Simple Authentication and Security Layer)

## Overview

While SSL/TLS encrypts communication and can authenticate clients using certificates, many organizations prefer authenticating users with usernames, passwords, OAuth tokens, or enterprise identity providers. Apache Kafka supports these authentication mechanisms through **SASL (Simple Authentication and Security Layer)**.

SASL is an authentication framework that allows Kafka clients to prove their identity before accessing the cluster. It does **not** provide encryption by itself. Instead, SASL is commonly combined with SSL/TLS to provide both authentication and encrypted communication.

Together:

- SSL/TLS → Encrypts communication
- SASL → Authenticates users

Modern production Kafka clusters frequently use **SASL_SSL**, which combines both technologies.

---

# Why SASL?

Without authentication:

```text
Anyone

↓

Kafka Broker

↓

Access Granted
```

Anyone who can reach the broker may attempt to connect.

With SASL:

```text
Client

↓

Username / Password

↓

Broker

↓

Identity Verified

↓

Access Granted
```

Only authenticated clients are allowed to connect.

---

# What SASL Provides

SASL focuses on:

- Client authentication
- User identity verification
- Integration with enterprise authentication systems

Unlike SSL, SASL does not encrypt traffic.

---

# SASL Architecture

```text
Producer

↓

Authentication

↓

Kafka Broker

↓

Consumer
```

Authentication occurs before any Kafka operations.

---

# Authentication Workflow

```text
Client

↓

Connect

↓

Send Credentials

↓

Broker Verifies

↓

Authenticated

↓

Produce / Consume
```

If authentication fails:

```text
Connection Rejected
```

---

# SASL Mechanisms

Kafka supports multiple SASL mechanisms.

| Mechanism | Description | Common Usage |
|-----------|-------------|--------------|
| PLAIN | Username & Password | Development |
| SCRAM | Salted Password Authentication | Production |
| GSSAPI | Kerberos | Enterprise |
| OAUTHBEARER | OAuth 2.0 Tokens | Cloud Platforms |
| AWS_MSK_IAM* | IAM Authentication | Amazon MSK |

\*Available in Amazon MSK, not standard Apache Kafka.

---

# SASL/PLAIN

The simplest mechanism.

Authentication:

```text
Username

↓

Password

↓

Kafka
```

Advantages:

- Easy to configure
- Good for development

Disadvantages:

- Password travels to the broker
- Must always be used with SSL

Never use SASL/PLAIN over plaintext connections.

---

# SASL/SCRAM

SCRAM stands for:

```text
Salted Challenge Response Authentication Mechanism
```

Instead of sending passwords directly:

```text
Password

↓

Hash

↓

Challenge

↓

Verification
```

Benefits:

- More secure
- Password not transmitted in plain form
- Recommended for production

---

# SASL/GSSAPI

Uses Kerberos authentication.

```text
User

↓

Kerberos Ticket

↓

Kafka
```

Common in:

- Large enterprises
- Active Directory environments
- Corporate data centers

---

# SASL/OAUTHBEARER

Authentication uses OAuth tokens.

```text
OAuth Provider

↓

Access Token

↓

Kafka
```

Often used with:

- Identity Providers
- Single Sign-On (SSO)
- Cloud-native platforms

---

# SASL_SSL

Most production deployments combine SASL with SSL.

```text
Producer

↓

SSL Encryption

↓

SASL Authentication

↓

Kafka Broker
```

This provides:

- Authentication
- Encryption

---

# Security Comparison

```text
SSL

↓

Encryption

----------------

SASL

↓

Authentication

----------------

SASL_SSL

↓

Authentication

+

Encryption
```

---

# Connection Flow

```text
Client

↓

SSL Handshake

↓

SASL Authentication

↓

Broker Verification

↓

Connection Established
```

Only authenticated clients proceed.

---

# Broker Configuration

Example broker configuration:

```properties
listeners=SASL_SSL://:9094

security.inter.broker.protocol=SASL_SSL

sasl.enabled.mechanisms=SCRAM-SHA-256
```

These settings enable SASL authentication over SSL.

---

# Client Configuration

Example client properties:

```properties
security.protocol=SASL_SSL

sasl.mechanism=SCRAM-SHA-256
```

Additional JAAS configuration provides authentication credentials.

---

# JAAS Configuration

Clients typically specify credentials using JAAS.

Example:

```properties
sasl.jaas.config=...
```

The configuration contains:

- Username
- Password
- Login Module

The exact format depends on the SASL mechanism.

---

# Broker-to-Broker Authentication

Kafka brokers can also authenticate each other.

```text
Broker 1

↓

SASL

↓

Broker 2

↓

Replication
```

This prevents unauthorized brokers from joining the cluster.

---

# Authentication Failure

Suppose:

```text
Wrong Password
```

Result:

```text
Authentication Failed

↓

Connection Closed
```

The client cannot access Kafka.

---

# SASL Workflow

```text
Client Starts

↓

SSL Connection

↓

SASL Authentication

↓

Identity Verified

↓

Produce / Consume
```

Authentication occurs before any Kafka operations.

---

# Choosing a Mechanism

| Scenario | Recommended Mechanism |
|----------|-----------------------|
| Local Development | SASL/PLAIN + SSL |
| Production | SASL/SCRAM + SSL |
| Enterprise Kerberos | GSSAPI |
| Cloud Identity | OAUTHBEARER |
| Amazon MSK | IAM Authentication |

---

# Advantages

SASL provides:

- Strong authentication
- Multiple authentication methods
- Enterprise integration
- Flexible deployment options
- Support for cloud identity providers

---

# Limitations

- Does not encrypt traffic by itself.
- Requires SSL for secure communication.
- Configuration can be complex for Kerberos and OAuth.
- Incorrect JAAS configuration causes authentication failures.

---

# Common Errors

### Authentication Failed

```text
SaslAuthenticationException
```

Possible causes:

- Wrong username
- Wrong password
- Invalid token

---

### Unsupported Mechanism

```text
UnsupportedSaslMechanismException
```

The client and broker use different mechanisms.

---

### Missing JAAS Configuration

```text
LoginException
```

Verify:

- JAAS configuration
- Username
- Password

---

### SSL Required

Suppose:

```text
security.protocol=SASL_PLAINTEXT
```

Production environments should instead use:

```text
SASL_SSL
```

---

# Best Practices

- Use **SASL_SSL** in production.
- Prefer **SCRAM** over **PLAIN** for password authentication.
- Rotate credentials regularly.
- Store credentials in a secure secret management system.
- Use dedicated service accounts for applications.
- Disable unused authentication mechanisms.
- Audit authentication failures.
- Avoid hardcoding credentials in application source code.

---

# Common Mistakes

- Using SASL without SSL.
- Using SASL/PLAIN in production over plaintext.
- Sharing service account credentials across applications.
- Hardcoding usernames and passwords.
- Misconfiguring JAAS files.
- Enabling unnecessary SASL mechanisms.
- Ignoring failed authentication logs.

---

# Summary

SASL provides Kafka's authentication framework, allowing brokers to verify the identity of producers, consumers, and other brokers before granting access. Kafka supports multiple SASL mechanisms, including PLAIN, SCRAM, Kerberos, and OAuth, making it suitable for a wide range of deployment environments. In production, SASL is almost always combined with SSL/TLS as **SASL_SSL**, providing both strong authentication and encrypted communication for secure Kafka deployments.

---

# Key Takeaways

- SASL is Kafka's authentication framework.
- SASL authenticates users but does not encrypt traffic.
- SSL/TLS provides encryption; SASL provides identity verification.
- SASL_SSL is the recommended production configuration.
- Kafka supports PLAIN, SCRAM, GSSAPI, and OAUTHBEARER authentication.
- SCRAM is generally preferred over PLAIN for production deployments.
- JAAS configuration is commonly used to supply client credentials.
- Strong authentication is a critical part of securing Kafka clusters.