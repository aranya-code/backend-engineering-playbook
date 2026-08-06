# Authorization

## Overview

After a client successfully authenticates with a Kafka broker, Kafka must determine **what that client is allowed to do**. This process is called **Authorization**.

Authorization controls access to Kafka resources such as topics, consumer groups, clusters, and transactional IDs. It ensures that authenticated users can perform only the operations they have been explicitly granted permission to perform.

Authentication answers:

```text
Who are you?
```

Authorization answers:

```text
What are you allowed to do?
```

Kafka implements authorization primarily through **Access Control Lists (ACLs)**.

---

# Why Authorization Matters

Suppose a company has multiple services.

```text
Order Service

Inventory Service

Analytics Service

Admin Team
```

Should every service be allowed to:

- Delete topics?
- Modify broker configuration?
- Read every topic?
- Create new topics?

Obviously not.

Authorization limits every client to only the permissions required.

---

# Authentication vs Authorization

Authentication:

```text
Client

↓

Verify Identity

↓

Authenticated
```

Authorization:

```text
Authenticated Client

↓

Permission Check

↓

Allowed / Denied
```

Authentication always occurs first.

---

# Authorization Workflow

```text
Client

↓

Authentication

↓

Authorization

↓

Kafka Resource

↓

Operation Executed
```

Every Kafka request follows this workflow.

---

# Authorization Architecture

```text
            Producer

                │

                ▼

       Authentication

                │

                ▼

        Authorization

                │

        ┌───────┴────────┐

        ▼                ▼

     Allowed          Denied
```

Only authorized requests reach Kafka resources.

---

# What Can Be Protected?

Kafka authorization protects:

- Topics
- Consumer Groups
- Clusters
- Transactional IDs
- Delegation Tokens

Every resource has its own permissions.

---

# Common Operations

Authorization controls operations such as:

```text
READ

WRITE

CREATE

DELETE

ALTER

DESCRIBE

ALTER_CONFIGS

DESCRIBE_CONFIGS
```

Each operation can be granted independently.

---

# Topic Authorization

Suppose:

```text
Inventory Service
```

Permissions:

```text
READ

Orders Topic

↓

Allowed
```

Attempt:

```text
DELETE

Orders Topic

↓

Denied
```

The service can consume messages but cannot delete the topic.

---

# Producer Authorization

Producer workflow:

```text
Producer

↓

WRITE Permission

↓

Kafka Topic

↓

Message Stored
```

Without WRITE permission:

```text
Authorization Failed
```

---

# Consumer Authorization

Consumer workflow:

```text
Consumer

↓

READ Permission

↓

Kafka Topic

↓

Consume Messages
```

Without READ permission:

```text
Access Denied
```

---

# Consumer Group Authorization

Consumers also require access to Consumer Groups.

```text
Consumer

↓

Consumer Group

↓

READ Permission

↓

Join Group
```

Without this permission:

```text
GroupAuthorizationException
```

---

# Cluster Authorization

Administrative operations require cluster permissions.

Example:

```text
Create Topic

↓

Cluster Permission

↓

Allowed
```

Cluster-level permissions are typically granted only to administrators.

---

# Authorization Decision

Kafka evaluates every request.

```text
Authenticated User

↓

ACL Lookup

↓

Permission Found?

↓

Yes

↓

Execute Operation
```

Otherwise:

```text
Permission Denied
```

---

# Example: Microservices

Suppose:

```text
Order Service
```

Permissions:

```text
WRITE

orders Topic
```

Inventory Service:

```text
READ

orders Topic
```

Analytics Service:

```text
READ

orders Topic
```

Each service has only the permissions it requires.

---

# Example: Administrator

Administrator permissions:

```text
CREATE Topics

DELETE Topics

ALTER Configuration

DESCRIBE Cluster
```

Regular application services should not receive these privileges.

---

# Authorization Flow Example

```text
Inventory Service

↓

Authenticate

↓

ACL Check

↓

READ Orders Topic

↓

Allowed

↓

Consume Records
```

Now consider:

```text
Inventory Service

↓

DELETE Orders Topic

↓

ACL Check

↓

Denied
```

Kafka blocks the operation.

---

# Principle of Least Privilege

Instead of:

```text
Application

↓

All Permissions
```

Grant:

```text
Application

↓

READ

Orders Topic
```

Only the minimum required permissions should be assigned.

---

# Multi-Tenant Example

Suppose one Kafka cluster serves multiple teams.

```text
Finance

↓

finance.*

Topics

----------------

Sales

↓

sales.*

Topics

----------------

Marketing

↓

marketing.*

Topics
```

Authorization prevents teams from accessing each other's data.

---

# Authorization Failure

Example:

```text
Producer

↓

WRITE

payments Topic

↓

Denied
```

Kafka returns:

```text
TopicAuthorizationException
```

The producer cannot publish the message.

---

# Authorization Lifecycle

```text
Client Connects

↓

Authentication

↓

Authorization

↓

Permission Check

↓

Kafka Operation

↓

Response
```

Every request follows this sequence.

---

# Common Authorization Errors

### Topic Authorization Failed

```text
TopicAuthorizationException
```

Cause:

Missing permission on the topic.

---

### Group Authorization Failed

```text
GroupAuthorizationException
```

Cause:

Missing Consumer Group permission.

---

### Cluster Authorization Failed

```text
ClusterAuthorizationException
```

Cause:

Insufficient cluster privileges.

---

### Transaction Authorization Failed

```text
TransactionalIdAuthorizationException
```

Cause:

Missing permission for transactional producers.

---

# Authorization vs Network Security

Authorization controls:

```text
Who Can Access Resources
```

Network security controls:

```text
Who Can Reach Kafka
```

Both are important.

Example:

```text
Firewall

↓

Authentication

↓

Authorization

↓

Kafka
```

Each layer provides additional protection.

---

# Production Authorization Workflow

```text
Application Starts

↓

Authenticate

↓

Authorization Check

↓

Read / Write Messages

↓

Business Processing
```

Applications cannot bypass authorization.

---

# Advantages

Authorization provides:

- Fine-grained access control
- Protection of sensitive data
- Multi-tenant isolation
- Reduced security risks
- Compliance support
- Least privilege enforcement

---

# Limitations

- Requires careful permission planning.
- Large environments may have many ACL rules.
- Poorly managed permissions become difficult to maintain.
- Authorization alone cannot verify client identity.

Authentication must always precede authorization.

---

# Best Practices

- Follow the principle of least privilege.
- Create separate service accounts for every application.
- Grant only required permissions.
- Restrict cluster administration to trusted administrators.
- Audit authorization failures regularly.
- Review permissions periodically.
- Remove unused accounts immediately.
- Automate permission management using Infrastructure as Code where possible.

---

# Common Mistakes

- Giving every application full permissions.
- Sharing service accounts between teams.
- Forgetting Consumer Group permissions.
- Allowing application services to delete topics.
- Ignoring authorization failures in logs.
- Using wildcard permissions excessively.
- Treating authorization as a replacement for authentication.

---

# Summary

Authorization determines what authenticated Kafka clients are permitted to do after they successfully connect to a cluster. By enforcing fine-grained permissions on topics, consumer groups, clusters, and other Kafka resources, authorization protects sensitive data and prevents unauthorized operations. Combined with authentication and encryption, authorization forms a critical pillar of Kafka's layered security model and is essential for operating secure production Kafka deployments.

---

# Key Takeaways

- Authorization determines what authenticated clients can do.
- It occurs after successful authentication.
- Kafka primarily implements authorization using ACLs.
- Permissions can be applied to topics, Consumer Groups, clusters, and other resources.
- Producers require WRITE permission, while consumers require READ permission.
- Authorization enforces the principle of least privilege.
- Authentication verifies identity; authorization verifies permissions.
- Proper authorization is essential for securing production Kafka environments.