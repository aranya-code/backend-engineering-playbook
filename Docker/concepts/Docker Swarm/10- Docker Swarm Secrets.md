# Docker Swarm Secrets

## Overview

Modern applications require sensitive information to function.

Examples:

```text
Database Passwords

API Keys

TLS Certificates

SSH Keys

OAuth Tokens

Private Keys
```

Storing these values directly inside:

```dockerfile
ENV DB_PASSWORD=admin123
```

or

```yaml
password: admin123
```

is insecure and considered a bad practice.

Docker Swarm solves this problem using **Secrets Management**.

---

# What are Docker Swarm Secrets?

## Definition

Docker Swarm Secrets are encrypted pieces of sensitive information that are securely stored and distributed only to services that require them.

Secrets are:

- Encrypted at rest
- Encrypted in transit
- Accessible only to authorized services
- Never stored inside images

---

# Why Do We Need Secrets?

Without secrets:

```text
Dockerfile

ENV PASSWORD=admin123
```

Problems:

- Password visible in image history
- Password visible in source code
- Difficult to rotate credentials
- Security risk

---

# With Docker Secrets

```text
Secret Store

      │

      ▼

Authorized Service

      │

      ▼

Container
```

Secrets remain protected.

---

# Secret Architecture

```text
                  Manager Node

                Secret Store

                       │

            ┌──────────┼──────────┐

            ▼                     ▼

       Service A             Service B

            │

            ▼

      Mounted Secret
```

Only services granted access can read the secret.

---

# How Secrets Work

## Step 1

Create secret.

```text
Database Password
```

---

## Step 2

Store secret securely in Swarm.

---

## Step 3

Attach secret to a service.

---

## Step 4

Secret appears inside container.

---

## Step 5

Application reads secret.

---

# Secret Lifecycle

```text
Create Secret

      │

      ▼

Store in Raft Database

      │

      ▼

Attach to Service

      │

      ▼

Mount in Container

      │

      ▼

Application Uses Secret
```

---

# Secret Storage

Secrets are stored inside:

```text
Raft Database
```

on manager nodes.

---

# Security Features

Secrets are:

```text
Encrypted at Rest

Encrypted in Transit

Access Controlled
```

Even if someone gains access to a worker node, secrets remain protected.

---

# Creating a Secret

## Method 1 - Using Echo

```bash
echo "mypassword" | \
docker secret create db_password -
```

Output:

```text
<secret-id>
```

---

# Verify Secret

```bash
docker secret ls
```

Example:

```text
ID        NAME

abc123    db_password
```

---

# Inspect Secret

```bash
docker secret inspect db_password
```

Example:

```json
{
  "ID": "abc123",
  "Spec": {
    "Name": "db_password"
  }
}
```

Notice:

```text
Secret Value Not Displayed
```

for security reasons.

---

# Creating Secret from File

Create file:

```text
password.txt
```

Contents:

```text
mypassword123
```

Create secret:

```bash
docker secret create \
db_password \
password.txt
```

---

# Secret File Workflow

```text
password.txt

      │

      ▼

docker secret create

      │

      ▼

Swarm Secret Store
```

---

# Using Secrets in Services

Create service:

```bash
docker service create \
--name mysql \
--secret db_password \
mysql
```

---

# Secret Mount Location

Inside container:

```text
/run/secrets/
```

Example:

```text
/run/secrets/db_password
```

---

# View Secret Inside Container

Enter container:

```bash
docker exec -it <container-id> sh
```

View secret:

```bash
cat /run/secrets/db_password
```

Output:

```text
mypassword
```

---

# Secret Access Architecture

```text
Container

   │

   ▼

/run/secrets

   │

   ▼

db_password
```

Application reads from file.

---

# Example: MySQL Password

Create secret:

```bash
echo "SuperSecurePassword" | \
docker secret create mysql_password -
```

---

Create service:

```bash
docker service create \
--name mysql \
--secret mysql_password \
mysql
```

---

Inside Container

```text
/run/secrets/mysql_password
```

Contains:

```text
SuperSecurePassword
```

---

# Updating Secrets

Secrets are immutable.

Meaning:

```text
Cannot Modify Existing Secret
```

---

# Why?

Changing secrets directly could break running services.

Instead:

```text
Create New Secret
```

---

# Secret Rotation

Current:

```text
db_password_v1
```

Create:

```text
db_password_v2
```

---

Create New Secret

```bash
echo "NewPassword" | \
docker secret create db_password_v2 -
```

---

Update Service

```bash
docker service update \
--secret-add db_password_v2 \
mysql
```

---

Remove Old Secret

```bash
docker service update \
--secret-rm db_password_v1 \
mysql
```

---

# Secret Rotation Workflow

```text
Old Secret

     │

     ▼

New Secret

     │

     ▼

Attach New Secret

     │

     ▼

Remove Old Secret
```

---

# Removing Secrets

Delete secret:

```bash
docker secret rm db_password
```

---

# Limitation

Secret cannot be removed while in use.

Example:

```text
Secret Used By Service
```

Attempt:

```bash
docker secret rm db_password
```

Result:

```text
Error
```

---

# Remove Secret Safely

Step 1

Detach from service:

```bash
docker service update \
--secret-rm db_password \
mysql
```

---

Step 2

Delete secret:

```bash
docker secret rm db_password
```

---

# Secrets vs Environment Variables

## Environment Variables

```bash
docker run \
-e PASSWORD=admin123
```

Problems:

- Visible via inspect
- Visible in process lists
- Exposed accidentally

---

## Docker Secrets

```text
Encrypted

Access Controlled

Stored Securely
```

Recommended.

---

# Comparison

| Feature | Environment Variable | Docker Secret |
|-----------|---------------------|---------------|
| Encryption | No | Yes |
| Access Control | Limited | Strong |
| Production Ready | No | Yes |
| Secure Storage | No | Yes |
| Rotation Support | Limited | Better |

---

# Secrets vs Configs

Docker Swarm provides:

```text
Secrets

Configs
```

---

# Secrets

For:

```text
Passwords

API Keys

Certificates

Tokens
```

---

# Configs

For:

```text
Application Settings

Nginx Configs

Application Config Files
```

---

# Secret Best Practices

## Never Store Passwords in Images

Avoid:

```dockerfile
ENV DB_PASSWORD=password123
```

---

## Use Secret Rotation

Rotate credentials periodically.

---

## Follow Least Privilege

Only attach secrets to services that require them.

---

## Store Certificates as Secrets

Examples:

```text
TLS Certificates

Private Keys
```

---

## Remove Unused Secrets

Regularly audit:

```bash
docker secret ls
```

---

# Real-World Example

E-Commerce Application

```text
Frontend

Backend

Database
```

Secrets:

```text
DB_PASSWORD

API_TOKEN

TLS_CERTIFICATE
```

Only:

```text
Backend
```

receives:

```text
DB_PASSWORD
```

Frontend cannot access it.

---

# Common Commands

## Create Secret

```bash
docker secret create
```

---

## List Secrets

```bash
docker secret ls
```

---

## Inspect Secret

```bash
docker secret inspect
```

---

## Remove Secret

```bash
docker secret rm
```

---

## Add Secret to Service

```bash
docker service create \
--secret secret_name
```

---

## Add Secret to Existing Service

```bash
docker service update \
--secret-add secret_name
```

---

## Remove Secret from Service

```bash
docker service update \
--secret-rm secret_name
```

---

# Common Interview Questions

## What are Docker Swarm Secrets?

Docker Swarm Secrets are encrypted sensitive values securely stored in the Swarm Raft database and made available only to authorized services.

---

## Where are Secrets Stored?

Secrets are stored in the encrypted Raft database maintained by manager nodes.

---

## Where do Secrets Appear Inside Containers?

Secrets are mounted inside:

```text
/run/secrets/
```

---

## Can a Secret Be Modified?

No. Secrets are immutable. A new secret must be created and rotated into the service.

---

## Why Are Secrets Better Than Environment Variables?

Secrets provide encryption, access control, secure distribution, and are not exposed through image history or process inspection.

---

## Are Secrets Available to All Containers?

No. Only services explicitly granted access can read them.

---

# Interview One-Liner

Docker Swarm Secrets provide a secure mechanism for storing and distributing sensitive information such as passwords, API keys, and certificates by encrypting them in the Raft database and exposing them only to authorized services through the `/run/secrets` directory.
