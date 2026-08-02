# Mutual TLS (mTLS)

## Overview

Transport Layer Security (TLS) encrypts communication between a client and a server. In traditional HTTPS connections, **only the server proves its identity** by presenting a server certificate.

However, some applications require **both the client and the server to authenticate each other**.

This is known as **Mutual TLS (mTLS).**

Amazon API Gateway supports **Mutual TLS** for **Regional Custom Domain Names**, allowing API Gateway to verify client certificates before processing requests.

mTLS is commonly used for:

- Banking APIs
- Healthcare systems
- Government applications
- B2B integrations
- Internal enterprise APIs
- Partner APIs

It provides a much stronger level of authentication than API keys or bearer tokens alone.

---

# Traditional TLS

In standard HTTPS:

```text
Client

↓

HTTPS Request

↓

Server Certificate

↓

Verify Server

↓

Encrypted Connection
```

Only the server is authenticated.

The client is anonymous unless additional authentication mechanisms are used.

---

# Mutual TLS

With Mutual TLS:

```text
Client

↓

Client Certificate

↓

API Gateway

↓

Server Certificate

↓

Both Verified

↓

Encrypted Connection
```

Both sides verify each other's identities.

---

# Architecture

```text
               Client

                  │

        Client Certificate

                  │

                  ▼

          Amazon API Gateway

                  │

       Server Certificate

                  │

                  ▼

      Lambda / ECS / EC2
```

API Gateway validates the client certificate before forwarding the request.

---

# Authentication Flow

```text
Client

↓

HTTPS Connection

↓

Server Certificate

↓

Client Verifies Server

↓

Client Certificate

↓

API Gateway Verifies Client

↓

Request Accepted

↓

Backend
```

If either verification fails, the TLS handshake fails and the request is rejected.

---

# How mTLS Works

During the TLS handshake:

```text
Client

↓

Hello

↓

Server Certificate

↓

Client Certificate Request

↓

Client Certificate

↓

Certificate Validation

↓

Secure Connection
```

Only clients possessing trusted certificates can establish a connection.

---

# Client Certificate

Each client owns an X.509 certificate.

Example:

```text
Company A

↓

Client Certificate

↓

API Gateway
```

Certificates are issued by a trusted Certificate Authority (CA).

---

# Truststore

API Gateway validates client certificates using a **Truststore**.

The Truststore contains trusted CA certificates.

```text
Amazon S3

↓

Truststore

↓

Trusted CAs

↓

API Gateway
```

Only certificates issued by trusted CAs are accepted.

---

# Truststore Location

The Truststore is stored in Amazon S3.

Example:

```text
Amazon S3

↓

truststore.pem
```

API Gateway downloads this file and validates client certificates against it.

---

# Certificate Validation

API Gateway verifies:

- Certificate signature
- Certificate chain
- Expiration date
- Trusted Certificate Authority

If validation succeeds:

```text
Connection Allowed
```

Otherwise:

```http
403 Forbidden
```

or the TLS handshake fails before the request reaches the API.

---

# mTLS Request Flow

```text
Client

↓

Client Certificate

↓

TLS Handshake

↓

API Gateway

↓

Certificate Validation

↓

Backend Service
```

The backend never receives unauthenticated requests.

---

# mTLS vs HTTPS

| HTTPS | Mutual TLS |
|--------|------------|
| Server Authentication | Server + Client Authentication |
| Client Certificate | ❌ | ✅ |
| Server Certificate | ✅ | ✅ |
| Stronger Security | ❌ | ✅ |

HTTPS protects communication.

mTLS protects communication **and** verifies both participants.

---

# mTLS vs API Keys

| API Key | mTLS |
|----------|------|
| Shared Secret | X.509 Certificate |
| Easy to Copy | Difficult to Steal |
| Application-Level | Transport-Level |
| Consumer Identification | Cryptographic Identity |

mTLS provides significantly stronger authentication.

---

# mTLS vs JWT

| JWT | mTLS |
|------|------|
| User Authentication | Client Authentication |
| Bearer Token | Certificate-Based |
| Expires Quickly | Certificate Lifecycle |
| Application Layer | Transport Layer |

Many enterprise systems use **both** together.

---

# Common Use Cases

Mutual TLS is commonly used for:

- Banking APIs
- Healthcare APIs
- Government systems
- B2B integrations
- Partner APIs
- Internal enterprise APIs
- Financial services
- Manufacturing systems

---

# Example Architecture

A bank exposes an internal payment API.

```text
Partner Bank

↓

Client Certificate

↓

API Gateway (mTLS)

↓

Payment Service

↓

Database
```

Only partner banks with trusted certificates can connect.

---

# Combining mTLS with Other Security

mTLS should not replace authorization.

A common production architecture:

```text
Client

↓

mTLS

↓

API Gateway

↓

JWT Authorizer

↓

Lambda

↓

Database
```

Here:

- mTLS authenticates the client device or application.
- JWT authenticates the user.
- Backend authorizes business operations.

---

# Advantages

## Strong Authentication

Client identity is verified cryptographically.

---

## Prevents Unauthorized Clients

Only clients with trusted certificates can establish a connection.

---

## Eliminates Shared Secrets

No passwords or API Keys are exchanged during authentication.

---

## Excellent for B2B

Perfect for trusted partner integrations.

---

## Industry Compliance

Helps satisfy security requirements in regulated industries such as finance and healthcare.

---

# Disadvantages

## Certificate Management

Certificates must be:

- Issued
- Distributed
- Rotated
- Revoked

---

## Operational Complexity

Managing Certificate Authorities and Truststores requires additional operational effort.

---

## Not Ideal for Public APIs

Public consumer applications generally use OAuth, Cognito, or JWT instead of client certificates.

---

# Best Practices

- Use mTLS only for APIs requiring strong client authentication.
- Store the Truststore securely in Amazon S3.
- Rotate client certificates regularly.
- Remove revoked certificates promptly.
- Combine mTLS with JWT or IAM for layered security.
- Monitor certificate expiration dates.
- Use AWS Certificate Manager (ACM) for managing server certificates.

---

# Common Interview Questions

### What is Mutual TLS (mTLS)?

Mutual TLS is an extension of TLS where both the client and the server authenticate each other using X.509 certificates before establishing a secure connection.

---

### Does API Gateway support Mutual TLS?

Yes.

Amazon API Gateway supports Mutual TLS for **Regional Custom Domain Names** using a Truststore stored in Amazon S3.

---

### What is a Truststore?

A Truststore is a collection of trusted Certificate Authority (CA) certificates that API Gateway uses to validate client certificates during the TLS handshake.

---

### Should mTLS replace JWT authentication?

No.

mTLS authenticates the client application or device, while JWT typically authenticates the user. Many production systems use both together.

---

### When should Mutual TLS be used?

mTLS is best suited for B2B integrations, financial services, healthcare systems, government APIs, and other environments requiring strong client authentication.

---

# Key Takeaways

- Mutual TLS (mTLS) authenticates both the client and the server during the TLS handshake.
- API Gateway supports mTLS for Regional Custom Domain Names using a Truststore stored in Amazon S3.
- mTLS provides stronger authentication than API Keys or bearer tokens because it relies on X.509 certificates.
- It is commonly used for enterprise, banking, healthcare, and partner APIs.
- mTLS complements—not replaces—other security mechanisms such as JWT Authorizers, IAM, and application-level authorization.