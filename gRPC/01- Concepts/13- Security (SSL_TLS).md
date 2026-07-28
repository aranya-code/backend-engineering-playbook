# Security (SSL/TLS)


# Introduction

Applications often exchange sensitive information over the network.

Examples include:

- User credentials
- Personal information
- Payment details
- Authentication tokens
- Financial transactions

If this data is transmitted without protection, an attacker could intercept or modify it.

To secure communication, gRPC uses **Transport Layer Security (TLS)**.

---

# Why Do We Need Security?

Consider the following communication.

```text
Client

      │

      ▼

Internet

      │

      ▼

Server
```

Without encryption:

- Data can be intercepted.
- Messages can be modified.
- Client identity cannot be verified.
- Sensitive information may be exposed.

Secure communication prevents these problems.

---

# What is SSL/TLS?

**SSL (Secure Sockets Layer)** was the original protocol for securing network communication.

It has been replaced by **TLS (Transport Layer Security)**.

Today, when people refer to SSL certificates, they are usually referring to TLS certificates.

Modern gRPC implementations use **TLS**, not the older SSL protocol.

---

# What Does TLS Provide?

TLS provides three important security guarantees.

## 1. Encryption

Data is encrypted before being transmitted.

```text
Client

↓

Encrypt Data

↓

Internet

↓

Decrypt Data

↓

Server
```

Anyone intercepting the communication sees only encrypted data.

---

## 2. Authentication

TLS allows the client to verify that it is communicating with the correct server.

This prevents attackers from impersonating legitimate services.

---

## 3. Integrity

TLS ensures that transmitted data has not been modified during transit.

If someone changes the message, the receiving side detects the modification.

---

# Secure vs Insecure Communication

## Insecure Communication

```text
Client

↓

Plain Data

↓

Network

↓

Server
```

Characteristics:

- No encryption
- Vulnerable to interception
- Suitable only for local development

---

## Secure Communication

```text
Client

↓

Encrypted Data

↓

Network

↓

Server
```

Characteristics:

- Encrypted traffic
- Server authentication
- Data integrity
- Recommended for production

---

# Secure Channel

To use TLS, the client creates a secure channel.

Example:

```python
credentials = grpc.ssl_channel_credentials()

channel = grpc.secure_channel(
    "api.company.com:443",
    credentials
)
```

The secure channel automatically encrypts all RPC traffic.

---

# Insecure Channel

For local development, an insecure channel can be used.

Example:

```python
channel = grpc.insecure_channel(
    "localhost:50051"
)
```

This should **never** be used for production systems exposed to public networks.

---

# Certificates

TLS relies on digital certificates.

A certificate contains information such as:

- Server identity
- Public key
- Certificate issuer
- Expiration date

When the client connects to the server, it verifies the server's certificate before exchanging data.

---

# TLS Handshake

Before any RPC is sent, the client and server perform a TLS handshake.

```text
Client

      │

      │ Request Secure Connection

      ▼

Server

      │

      │ Send Certificate

      ▼

Client

      │

      │ Verify Certificate

      ▼

Secure Connection Established
```

Once the handshake completes successfully, encrypted communication begins.

---

# Mutual TLS (mTLS)

Normally, only the server proves its identity to the client.

With **Mutual TLS (mTLS)**:

- The server authenticates the client.
- The client authenticates the server.

```text
Client Certificate

        │

        ▼

Server

        ▲

Server Certificate
```

Both parties verify each other's certificates.

This provides stronger security.

---

# When is mTLS Used?

Mutual TLS is commonly used in:

- Internal microservices
- Banking systems
- Healthcare applications
- Government systems
- Enterprise environments
- Kubernetes service-to-service communication

---

# TLS in Microservices

Consider the following architecture.

```text
Frontend

        │

        ▼

API Gateway

        │

        ▼

User Service

        │

        ▼

Payment Service

        │

        ▼

Database
```

Each service communicates over TLS.

This protects communication even inside private networks.

---

# Authentication vs Encryption

These concepts are related but different.

| Authentication | Encryption |
|---------------|------------|
| Verifies identity | Protects data |
| Confirms who is communicating | Prevents others from reading data |
| Uses certificates | Uses cryptographic algorithms |

TLS provides both authentication and encryption.

---

# Advantages of TLS

Using TLS provides several benefits.

- Encrypts network traffic
- Prevents eavesdropping
- Verifies server identity
- Protects sensitive information
- Ensures message integrity
- Builds trust between services

---

# Common Mistakes

Avoid the following mistakes:

- Using insecure channels in production.
- Ignoring certificate expiration.
- Sharing private keys.
- Disabling certificate verification.
- Assuming private networks do not require encryption.

---

# Best Practices

When securing gRPC applications:

- Always use TLS in production.
- Protect private keys carefully.
- Rotate certificates before they expire.
- Use Mutual TLS for internal microservices when appropriate.
- Never disable certificate verification.
- Use trusted Certificate Authorities (CAs) whenever possible.

---

# Key Takeaways

- gRPC secures communication using Transport Layer Security (TLS).
- TLS provides encryption, authentication, and data integrity.
- Secure channels encrypt all RPC traffic between clients and servers.
- Digital certificates allow clients to verify server identity.
- Mutual TLS (mTLS) enables both clients and servers to authenticate each other.
- Production gRPC applications should always use secure channels and follow certificate management best practices.