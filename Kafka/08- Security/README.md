# Kafka Security

Security is one of the most critical aspects of operating Apache Kafka in production. Since Kafka often carries sensitive business events such as financial transactions, customer information, authentication events, audit logs, and application data, protecting the Kafka cluster from unauthorized access is essential.

Kafka follows a **layered security model**, where different mechanisms work together to secure the platform:

- **Authentication** verifies client identities.
- **Authorization** controls what authenticated clients are allowed to do.
- **SSL/TLS** encrypts data in transit.
- **SASL** provides multiple authentication mechanisms.
- **ACLs** enforce fine-grained access control.

Together, these features help build secure, enterprise-grade event streaming platforms.

---

# Folder Structure

```text
08-Security/
│
├── 01- Kafka Security Overview.md
├── 02- SSL.md
├── 03- SASL.md
├── 04- ACLs.md
├── 05- Authentication.md
├── 06- Authorization.md
└── README.md
```

---

# Navigation

## Security Fundamentals

- [01- Kafka Security Overview](./01-%20Kafka%20Security%20Overview.md)

---

## Encryption

- [02- SSL](./02-%20SSL.md)

---

## Authentication

- [03- SASL](./03-%20SASL.md)
- [05- Authentication](./05-%20Authentication.md)

---

## Authorization & Access Control

- [04- ACLs](./04-%20ACLs.md)
- [06- Authorization](./06-%20Authorization.md)

---

# Learning Path

Study the chapters in the following order:

```text
Kafka Security Overview
          │
          ▼
SSL (Encryption)
          │
          ▼
SASL
          │
          ▼
Authentication
          │
          ▼
ACLs
          │
          ▼
Authorization
```

This sequence introduces Kafka's security model before exploring encryption, authentication, access control, and authorization.

---

# Topics Covered

This section explains:

- Kafka security architecture
- Defense-in-depth
- Encryption in transit
- SSL/TLS
- Certificates
- Keystores and Truststores
- SSL Handshake
- Mutual TLS (mTLS)
- SASL authentication
- SASL mechanisms
- SASL_SSL
- JAAS configuration
- Authentication workflow
- Authorization workflow
- Access Control Lists (ACLs)
- Topic permissions
- Consumer Group permissions
- Cluster permissions
- Principle of Least Privilege
- Production security best practices

---

# Prerequisites

Before studying this section, you should understand:

- Kafka Fundamentals
- Producers
- Consumers
- Consumer Groups
- Topics
- Brokers
- Basic networking concepts
- Basic SSL/TLS concepts (helpful but not mandatory)

---

# Skills You'll Gain

After completing this section, you will be able to:

- Explain Kafka's layered security model.
- Secure communication using SSL/TLS.
- Configure SASL authentication mechanisms.
- Understand the difference between authentication and authorization.
- Design secure Kafka deployments.
- Configure and manage Kafka ACLs.
- Apply the Principle of Least Privilege.
- Troubleshoot common authentication and authorization failures.
- Protect Kafka clusters in production environments.

---

# Real-World Applications

The concepts in this section are widely used in:

- Banking Systems
- Payment Platforms
- Healthcare Applications
- E-commerce Platforms
- Government Systems
- Cloud Platforms
- Enterprise Messaging
- Event-Driven Architectures
- Financial Trading Systems
- IoT Platforms
- SaaS Applications
- Large-Scale Microservices

---

# Best Practices

- Always enable SSL/TLS in production.
- Use **SASL_SSL** instead of plaintext authentication.
- Follow the Principle of Least Privilege.
- Create dedicated service accounts for every application.
- Avoid wildcard ACLs whenever possible.
- Rotate passwords, certificates, and tokens regularly.
- Store secrets in a secure secrets management system.
- Enable authentication for both clients and brokers.
- Audit authentication and authorization failures.
- Keep Kafka and its security configuration up to date.

---

# Common Mistakes

- Running production Kafka without authentication.
- Using PLAINTEXT listeners in production.
- Using SASL/PLAIN without SSL.
- Sharing service account credentials across multiple applications.
- Granting excessive ACL permissions.
- Hardcoding passwords or certificates in application code.
- Ignoring certificate expiration.
- Exposing Kafka brokers directly to the public internet.
- Treating authentication as a replacement for authorization.
- Neglecting regular security reviews and audits.

---

# Security Model at a Glance

```text
                 Client
                    │
                    ▼
         Authentication
                    │
                    ▼
          Authorization
                    │
                    ▼
         SSL/TLS Encryption
                    │
                    ▼
             Kafka Broker
                    │
                    ▼
        Topics & Consumer Groups
```

Each layer contributes to the overall security posture of the Kafka cluster.

---

# Summary

Kafka security is built on a layered approach that combines authentication, authorization, encryption, and access control to protect event streaming infrastructure. SSL/TLS secures communication, SASL verifies client identities, and ACLs enforce fine-grained permissions on Kafka resources. Together, these mechanisms ensure that only trusted clients can connect, only authorized operations are permitted, and sensitive business data remains protected throughout its lifecycle. Mastering these security concepts is essential for designing and operating production-grade Kafka clusters.