# Overview

When troubleshooting gRPC services, one of the most valuable tools available is **grpcurl**. It is often described as the **curl equivalent for gRPC**, allowing developers to inspect services, invoke RPC methods, test authentication, debug TLS issues, and validate server behavior directly from the command line.

Unlike custom client applications, grpcurl allows engineers to interact with a gRPC server without writing any code. When the server supports **gRPC Reflection**, grpcurl can automatically discover available services and methods. Even without reflection, it can use local `.proto` files to communicate with the server.

Because of its simplicity and versatility, grpcurl has become one of the standard tools used by backend engineers, DevOps engineers, SREs, and platform teams for diagnosing production gRPC systems.

This guide explains how grpcurl works, common debugging workflows, frequently encountered issues, and best practices for using grpcurl effectively.

---

# What is grpcurl?

grpcurl is a command-line tool that communicates directly with a gRPC server.

```text
Developer

↓

grpcurl

↓

gRPC Server

↓

RPC Response
```

It performs tasks similar to:

- `curl` for REST APIs
- `psql` for PostgreSQL
- `redis-cli` for Redis

but specifically for gRPC services.

---

# Why Use grpcurl?

grpcurl is useful because it can:

- Discover available services
- List RPC methods
- Invoke unary RPCs
- Test streaming RPCs
- Send request metadata
- Authenticate using JWT tokens
- Validate TLS configuration
- Debug production services
- Verify deployments

It is often the first tool engineers use when troubleshooting gRPC.

---

# Common Debugging Workflow

A typical workflow looks like this.

```text
Server Running?

        │

        ▼

List Services

        │

        ▼

Describe Service

        │

        ▼

Invoke RPC

        │

        ▼

Inspect Response
```

This systematic approach helps isolate issues quickly.

---

# Step 1: Verify Server Connectivity

The first step is confirming that the server is reachable.

Example:

```bash
grpcurl localhost:50051 list
```

Possible outcomes:

```text
Success
```

or

```text
Connection Refused
```

If the server cannot be reached, investigate networking before debugging the application.

---

# Step 2: List Available Services

When Reflection is enabled:

```bash
grpcurl localhost:50051 list
```

Example output:

```text
grpc.health.v1.Health

employee.EmployeeService

inventory.InventoryService
```

If this command succeeds, the server and Reflection service are working correctly.

---

# Step 3: Describe a Service

Display service information.

```bash
grpcurl localhost:50051 describe employee.EmployeeService
```

Typical output includes:

- RPC methods
- Request messages
- Response messages

This helps verify the API contract.

---

# Step 4: Describe a Message

grpcurl can also display Protocol Buffer messages.

Example:

```bash
grpcurl localhost:50051 describe employee.Employee
```

Example output:

```text
message Employee {

    string id

    string name

    string department

}
```

This is useful when constructing request payloads.

---

# Step 5: Invoke a Unary RPC

Example:

```bash
grpcurl \
-d '{"id":"101"}' \
localhost:50051 \
employee.EmployeeService/GetEmployee
```

Workflow:

```text
grpcurl

↓

Request

↓

Server

↓

Response
```

This allows engineers to verify application behavior without writing client code.

---

# Step 6: Send Authentication Metadata

Many production services require authentication.

Example:

```bash
grpcurl \
-H "authorization: Bearer <TOKEN>" \
localhost:50051 \
employee.EmployeeService/GetEmployee
```

If authentication succeeds, metadata is being transmitted correctly.

---

# Step 7: Test TLS Connections

For secure endpoints:

```bash
grpcurl \
api.company.com:443 \
list
```

Successful execution confirms:

- TLS
- HTTP/2
- Server availability

TLS failures often indicate certificate or hostname issues.

---

# Step 8: Use Local .proto Files

If Reflection is disabled:

```text
Client

↓

.proto Files

↓

grpcurl

↓

Server
```

grpcurl can still invoke RPCs using locally available Protocol Buffer definitions.

---

# Common Errors

Frequently encountered grpcurl errors include:

```text
Connection refused
```

```text
UNAVAILABLE
```

```text
Deadline Exceeded
```

```text
UNAUTHENTICATED
```

```text
Permission Denied
```

```text
server does not support the reflection API
```

Each error indicates a different stage of the request lifecycle.

---

# Debugging Reflection Issues

Example:

```bash
grpcurl localhost:50051 list
```

Output:

```text
server does not support the reflection API
```

Possible causes:

- Reflection disabled
- Reflection not registered
- Proxy configuration issues

See the dedicated **Reflection Issues** chapter for detailed guidance.

---

# Debugging Authentication

Example:

```text
UNAUTHENTICATED
```

Verify:

- Authorization metadata
- JWT token
- Expiration time
- Server authentication configuration

grpcurl makes it easy to test different authentication scenarios.

---

# Debugging TLS

Example:

```text
TLS handshake failed
```

Possible causes:

- Expired certificate
- Unknown CA
- Hostname mismatch
- Missing certificate chain

Testing with grpcurl helps isolate transport-layer issues.

---

# Debugging Service Availability

Suppose:

```bash
grpcurl localhost:50051 list
```

returns:

```text
Connection refused
```

Verify:

- Server running
- Correct port
- Firewall
- Docker networking
- Kubernetes Service

This quickly distinguishes networking problems from application errors.

---

# Diagnostic Workflow

Use the following sequence.

```text
RPC Failed

        │

Server Reachable?

        │

Yes

        ▼

Reflection Enabled?

        │

Yes

        ▼

Service Exists?

        │

Yes

        ▼

Authentication?

        │

Yes

        ▼

Invoke RPC
```

---

# Integrating grpcurl into CI/CD

grpcurl can validate deployments automatically.

Example workflow:

```text
Deploy

↓

Health Check

↓

grpcurl Test

↓

Smoke Test

↓

Production
```

This helps detect deployment issues before users encounter them.

---

# Real-World Example

A team deploys a new version of an employee service.

The deployment succeeds, but client applications begin reporting:

```text
UNAVAILABLE
```

An engineer connects to the server using grpcurl.

```bash
grpcurl localhost:50051 list
```

Output:

```text
employee.EmployeeService
```

Reflection works.

Next:

```bash
grpcurl \
-d '{"id":"101"}' \
localhost:50051 \
employee.EmployeeService/GetEmployee
```

Response:

```text
UNAUTHENTICATED
```

The deployment accidentally removed the API Gateway's authorization header forwarding.

After restoring metadata forwarding, grpcurl returns a successful response, confirming the issue is resolved.

---

# Prevention Checklist

Before deploying:

- Verify server connectivity.
- Test Reflection.
- Validate every public RPC.
- Test authenticated requests.
- Verify TLS configuration.
- Test through the reverse proxy.
- Include grpcurl in deployment validation.
- Document commonly used commands.

---

# Best Practices

- Use grpcurl as the first debugging tool for gRPC services.
- Enable Reflection in development environments.
- Test production endpoints through the same network path used by clients.
- Verify authentication and TLS separately.
- Keep grpcurl updated to match modern gRPC features.
- Automate grpcurl smoke tests in CI/CD pipelines.
- Maintain a library of reusable grpcurl commands for operations teams.

---

# Common Mistakes

Avoid the following mistakes:

- Assuming Reflection is always enabled.
- Testing only local environments.
- Ignoring authentication metadata.
- Using outdated `.proto` files.
- Skipping TLS validation.
- Forgetting to verify services after deployment.
- Treating grpcurl as a development-only tool.

---

# Key Takeaways

- grpcurl is the primary command-line tool for interacting with and debugging gRPC services.
- It can discover services, inspect APIs, invoke RPC methods, validate authentication, and troubleshoot TLS issues without requiring custom client code.
- Reflection simplifies grpcurl usage, but local `.proto` files can be used when Reflection is disabled.
- Integrating grpcurl into deployment pipelines helps detect configuration and networking issues before they impact production.
- Mastering grpcurl significantly improves the speed and effectiveness of troubleshooting production gRPC systems.