# ACLs (Access Control Lists)

## Overview

Authentication verifies **who a client is**, but it does not determine **what the client is allowed to do**. Once a producer or consumer successfully authenticates, Kafka must decide whether that client has permission to access specific resources.

Kafka enforces these permissions using **Access Control Lists (ACLs)**.

An ACL defines which users or applications can perform specific operations on Kafka resources such as topics, consumer groups, transactional IDs, and clusters.

ACLs implement the **principle of least privilege**, ensuring clients receive only the permissions they require.

---

# Why ACLs?

Suppose two applications exist.

```text
Inventory Service

↓

Orders Topic
```

Inventory Service should:

- Read messages
- Write inventory updates

Now consider:

```text
Analytics Service
```

Analytics should:

- Read events

But it should **not**:

- Delete topics
- Modify configurations
- Create brokers

ACLs enforce these restrictions.

---

# Authentication vs Authorization

Authentication asks:

```text
Who are you?
```

Authorization asks:

```text
What are you allowed to do?
```

Flow:

```text
Client

↓

Authentication

↓

Authorization (ACL)

↓

Kafka Resource
```

---

# What is an ACL?

An ACL is a rule that grants or denies permissions.

Example:

```text
User

↓

orders Topic

↓

READ

↓

Allowed
```

Or:

```text
User

↓

payments Topic

↓

DELETE

↓

Denied
```

---

# Kafka Resources

ACLs protect several Kafka resources.

Common resources include:

- Topics
- Consumer Groups
- Clusters
- Transactional IDs
- Delegation Tokens

Each resource can have different permissions.

---

# ACL Architecture

```text
             Client

                │

                ▼

        Authentication

                │

                ▼

           ACL Check

                │

      ┌─────────┴─────────┐

      ▼                   ▼

Permission Granted   Permission Denied
```

---

# Common Operations

Kafka ACLs control operations such as:

- READ
- WRITE
- CREATE
- DELETE
- ALTER
- DESCRIBE
- CLUSTER_ACTION
- IDEMPOTENT_WRITE

Each operation can be granted independently.

---

# READ Permission

Allows consumers to read messages.

Example:

```text
User

↓

orders Topic

↓

READ

↓

Allowed
```

Without READ permission:

```text
Consume

↓

Denied
```

---

# WRITE Permission

Allows producers to publish messages.

```text
Producer

↓

Orders Topic

↓

WRITE

↓

Allowed
```

Without WRITE permission:

```text
Produce

↓

Denied
```

---

# CREATE Permission

Allows creation of resources.

Example:

```text
Developer

↓

Create Topic

↓

Allowed
```

---

# DELETE Permission

Allows deletion of resources.

```text
Admin

↓

Delete Topic

↓

Allowed
```

Most application accounts should never receive this permission.

---

# DESCRIBE Permission

Allows viewing metadata.

Example:

```text
User

↓

Describe Topic

↓

Allowed
```

Useful for monitoring tools.

---

# ALTER Permission

Allows modifying configurations.

Example:

```text
Admin

↓

Update Retention

↓

Allowed
```

Regular application accounts typically do not require this permission.

---

# Consumer Group ACLs

Consumers also require permissions on Consumer Groups.

```text
Consumer

↓

Consumer Group

↓

READ
```

Without appropriate group permissions, consumers cannot join the group.

---

# Cluster-Level ACLs

Some operations apply to the entire Kafka cluster.

Example:

```text
Cluster

↓

CREATE Topic

↓

Permission Required
```

Cluster administration is usually limited to platform administrators.

---

# ACL Workflow

```text
Client

↓

Authenticate

↓

Request Operation

↓

ACL Lookup

↓

Permission Decision

↓

Allow / Deny
```

Every operation passes through this process.

---

# Kafka ACL Command

Kafka provides:

```bash
kafka-acls.sh
```

This utility is used to:

- Create ACLs
- List ACLs
- Remove ACLs

---

# Listing ACLs

Display configured ACLs.

```bash
kafka-acls.sh \
--bootstrap-server localhost:9092 \
--list
```

Useful for auditing permissions.

---

# Adding an ACL

Grant READ access.

```bash
kafka-acls.sh \
--bootstrap-server localhost:9092 \
--add \
--allow-principal User:inventory-service \
--operation READ \
--topic orders
```

This allows the specified user to consume from the **orders** topic.

---

# Granting WRITE Access

Example:

```bash
kafka-acls.sh \
--bootstrap-server localhost:9092 \
--add \
--allow-principal User:order-service \
--operation WRITE \
--topic orders
```

Now the producer can publish messages.

---

# Removing ACLs

Remove an ACL.

```bash
kafka-acls.sh \
--bootstrap-server localhost:9092 \
--remove
```

The remaining options identify the ACL to remove.

---

# Wildcard ACLs

ACLs can use wildcards.

Example:

```text
Topic

↓

*
```

This matches every topic.

While convenient, wildcard permissions should be used carefully.

---

# Principle of Least Privilege

Instead of:

```text
User

↓

All Permissions
```

Grant only:

```text
User

↓

READ

↓

Orders Topic
```

This minimizes security risks.

---

# Example: Microservices

```text
Order Service

↓

WRITE

↓

Orders Topic

----------------

Inventory Service

↓

READ

↓

Orders Topic

----------------

Analytics Service

↓

READ

↓

Orders Topic
```

Each service receives only the permissions it needs.

---

# Production Workflow

```text
Application Starts

↓

Authenticate

↓

ACL Check

↓

Permission Granted

↓

Produce / Consume
```

Unauthorized requests are rejected immediately.

---

# Advantages

ACLs provide:

- Fine-grained authorization
- Least privilege access
- Strong security boundaries
- Multi-tenant isolation
- Auditable permissions

---

# Limitations

- ACL management becomes complex in very large environments.
- Poorly designed ACLs are difficult to maintain.
- Requires careful planning of users and roles.

Many organizations automate ACL management using Infrastructure as Code (IaC).

---

# Common Errors

### Authorization Failed

```text
TopicAuthorizationException
```

The user lacks permission on the topic.

---

### Group Authorization Failed

```text
GroupAuthorizationException
```

The consumer lacks permission on the Consumer Group.

---

### Cluster Authorization Failed

```text
ClusterAuthorizationException
```

The user lacks cluster-level privileges.

---

### Principal Not Found

Verify:

- Username
- Authentication mechanism
- SASL configuration

---

# Best Practices

- Follow the principle of least privilege.
- Create separate service accounts for each application.
- Avoid wildcard permissions whenever possible.
- Grant only required operations.
- Review ACLs regularly.
- Remove unused accounts promptly.
- Audit authorization failures.
- Manage ACLs using automation for large environments.

---

# Common Mistakes

- Granting all permissions to every application.
- Using wildcard ACLs excessively.
- Sharing service accounts across multiple services.
- Forgetting Consumer Group permissions.
- Ignoring authorization failures.
- Allowing applications to modify broker configurations.
- Treating ACLs as a substitute for authentication.

---

# Summary

ACLs provide Kafka's authorization layer by controlling which authenticated users and applications can perform specific operations on Kafka resources. By granting permissions at the topic, Consumer Group, and cluster levels, ACLs enforce the principle of least privilege and prevent unauthorized access to critical messaging infrastructure. Proper ACL design is an essential component of securing production Kafka deployments.

---

# Key Takeaways

- ACLs determine what authenticated clients are allowed to do.
- Kafka ACLs protect topics, Consumer Groups, clusters, and other resources.
- Common permissions include READ, WRITE, CREATE, DELETE, ALTER, and DESCRIBE.
- `kafka-acls.sh` is used to manage ACLs.
- Follow the principle of least privilege when assigning permissions.
- Separate service accounts improve security and maintainability.
- ACLs complement authentication—they do not replace it.
- Well-designed ACLs are critical for securing production Kafka clusters.