# RDS Security and Encryption

Securing database workloads is a critical requirement for production systems. Amazon RDS implements security in depth through a combination of network isolation, identity and access management, encryption at rest, encryption in transit, and auditing.

Understanding these security controls, their limitations, and configuration steps is essential for protecting sensitive business data.

---

# Encryption at Rest

Encryption at rest secures database storage, automated backups, read replicas, and snapshots against unauthorized physical access.

## KMS Integration

- **Mechanism**: Uses the industry-standard AES-256 encryption algorithm via AWS Key Management Service (KMS).
- **Scope**: Once enabled, data stored on the underlying EBS volumes, temporary storage, backups, snapshots, and replication streams are all encrypted.
- **Key Types**: Can use the AWS-managed default key (`aws/rds`) or a Customer Managed Key (CMK) for cross-account sharing and custom key rotation policies.
- **Creation Time Constraint**: Encryption at rest **must be enabled when the RDS instance is created**. You cannot enable encryption on an existing unencrypted RDS instance.

## Encrypting an Existing Unencrypted RDS Instance

To encrypt an existing unencrypted database, you must follow a specific snapshot-copy-restore migration path:

```text
Unencrypted RDS Instance
       │
   Take Snapshot
       │
       ▼
Unencrypted Snapshot
       │
   Copy Snapshot + Enable Encryption (specify KMS Key)
       │
       ▼
Encrypted Snapshot
       │
   Restore Snapshot
       │
       ▼
Encrypted RDS Instance
```

---

# Encryption in Transit

Encryption in transit protects query payloads and credentials from eavesdropping on the network.

- **SSL/TLS**: RDS automatically generates an SSL/TLS certificate for every database instance.
- **Certificate Authority (CA)**: RDS certificates are periodically updated by AWS. You must update your client applications to trust the new CA root certificates during rotation events to prevent connection failures.
- **Enforcing SSL**: You can configure parameter groups to force all database connections to use SSL/TLS:
  - **PostgreSQL**: Set `rds.force_ssl = 1`.
  - **MySQL / MariaDB**: Enforce via user privileges (`REQUIRE SSL`) or set `require_secure_transport = ON`.

---

# Network Security

VPC isolation is the primary layer of network security for RDS.

- **Private Subnets**: Always deploy production databases in private subnets with no internet route. Databases should never be deployed in public subnets.
- **Public Accessibility**: Set the `Publicly Accessible` flag to `No` to prevent the database from getting a public IP address, ensuring it remains unreachable from the internet even if subnets are misconfigured.
- **Security Groups**: Restrict inbound database traffic using Security Group Chaining. Only allow connections on the specific database port (e.g., `5432` for PostgreSQL) originating from the security group of your compute resources (EC2, ECS, Lambda).

```text
Permissive (Anti-Pattern):
Inbound: Port 5432 from 0.0.0.0/0  ✗ (Exposed to internet)
Inbound: Port 5432 from 10.0.0.0/16 ✗ (Too broad inside VPC)

Secure (Best Practice):
Inbound: Port 5432 from sg-app-tier  ✓ (Only app servers can connect)
```

---

# Authentication Methods

RDS supports three primary authentication mechanisms:

## 1. Native Database Authentication

Standard username and password verification managed by the database engine.
- **Storage**: Passwords stored inside database system tables.
- **Best Practice**: Integrate with **AWS Secrets Manager** to rotate credentials automatically.

## 2. IAM Database Authentication

Allows users and applications to authenticate to RDS using IAM credentials and temporary security tokens.

- **Mechanism**: The application generates a short-lived login token using the `rds-db:connect` action via STS. The database verifies the token with the RDS service.
- **Lifecycle**: Tokens have a lifetime of **15 minutes**.
- **No Passwords**: No credentials are stored in the application or the database.

```text
Application                    AWS STS                      RDS Instance
     │                            │                             │
     │ Request Auth Token         │                             │
     ├───────────────────────────►│                             │
     │◄──────────────────────────┤                             │
     │ Return 15-Min Token        │                             │
     │                            │                             │
     │ Connect with Token as Password                           │
     ├─────────────────────────────────────────────────────────►│
     │                                                          │ Validate token
     │                                                          │ with AWS IAM
```

### IAM Authentication Limitations

- **Throughput Constraint**: IAM authentication is limited to **200 connections per second** (limitations vary by engine). If your application establishes frequent new connections (e.g., serverless Lambda functions), use standard password auth via Secrets Manager or place an **RDS Proxy** in front of the database.
- **Configuration Overhead**: Requires database users to be configured with the specific external identity plugin (e.g., `aws_iam` for MySQL/PostgreSQL).

## 3. Active Directory Authentication

Integrates with AWS Directory Service to allow users to log in using corporate credentials.
- **Best Use Case**: Enterprise environments with centralized directory services (e.g., Microsoft SQL Server setups).

---

# Key Takeaways

- **Encryption at rest** is mandatory for production. If missed at creation, use the snapshot-copy-restore path to encrypt.
- Always enforce **SSL/TLS connections** via parameter groups to secure data in transit.
- Deploy databases in **private subnets** only, with `Publicly Accessible` set to `No`.
- Restrict inbound access by **chaining security groups** directly to your application tier.
- Use **IAM Database Authentication** to eliminate hardcoded database credentials, but be mindful of its 200 connections/sec limit.
- Integrate native database credentials with **AWS Secrets Manager** for secure, automated rotation.

---
