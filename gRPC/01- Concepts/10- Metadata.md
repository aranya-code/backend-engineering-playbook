# Metadata


# What is Metadata?

Metadata is **additional information** sent along with a gRPC request or response.

It is **not part of the actual request or response message**.

Instead, metadata provides contextual information that helps both the client and server process the request.

Think of metadata as the equivalent of **HTTP headers** in a REST API.

---

# Why Do We Need Metadata?

Not all information belongs inside the request message.

Consider an Employee Service.

Request message:

```proto
message EmployeeRequest {

    int32 id = 1;

}
```

The request only needs the employee ID.

However, the server may also need information such as:

- Authentication token
- User ID
- Language preference
- Request ID
- Correlation ID
- Client version

Instead of adding these values to every request message, they are sent as metadata.

---

# Metadata vs Request Message

| Request Message | Metadata |
|----------------|----------|
| Business data | Contextual information |
| Defined in `.proto` | Not defined in `.proto` |
| Serialized using Protobuf | Sent as key-value pairs |
| Part of the API contract | Communication metadata |

Example:

Request Message

```text
Employee ID = 101
```

Metadata

```text
Authorization = Bearer <token>

Request-ID = abc123

Language = en
```

---

# Types of Metadata

gRPC supports two types of metadata.

## Request Metadata

Sent from the client to the server.

```text
Client

Authorization

Request-ID

Language

↓

Server
```

Examples include:

- JWT token
- API key
- Correlation ID
- Locale
- Client version

---

## Response Metadata

Sent from the server back to the client.

```text
Server

Server Version

Processing Time

Rate Limit

↓

Client
```

Examples include:

- Server version
- Processing duration
- Rate limit information
- Custom response headers

---

# Metadata Format

Metadata consists of **key-value pairs**.

Example:

```text
authorization : Bearer eyJhb...

request-id    : 9f8d32

language      : en-US

client-name   : MobileApp
```

Each key is associated with a corresponding value.

---

# Sending Metadata

A client attaches metadata when making an RPC call.

Example:

```python
metadata = (
    ("authorization", "Bearer my-token"),
    ("request-id", "abc123"),
)

response = stub.GetEmployee(
    request,
    metadata=metadata
)
```

The metadata is sent alongside the request.

---

# Receiving Metadata

The server can read incoming metadata before processing the request.

Example:

```python
authorization = dict(
    context.invocation_metadata()
).get("authorization")
```

The server can then:

- Authenticate the client
- Validate permissions
- Log request information
- Apply business rules

---

# Sending Response Metadata

The server can also return metadata to the client.

Example:

```python
context.send_initial_metadata((
    ("server-version", "1.0"),
))
```

The client receives this metadata before the actual response message.

---

# Trailing Metadata

In addition to initial response metadata, gRPC supports **trailing metadata**.

Trailing metadata is sent after the RPC completes.

```text
Client

↓

Request

↓

Server

↓

Response

↓

Trailing Metadata
```

Trailing metadata is commonly used for:

- Debugging information
- Processing statistics
- Custom status information

---

# Common Use Cases

Metadata is commonly used for:

- Authentication
- Authorization
- API keys
- JWT tokens
- Correlation IDs
- Distributed tracing
- Request tracking
- Localization
- Client versioning
- Logging

---

# Authentication Example

A client sends an authentication token.

```text
Metadata

authorization

Bearer eyJhbGci...
```

The server validates the token before executing the requested RPC.

If authentication fails, the server rejects the request.

---

# Distributed Tracing

Large systems often consist of multiple microservices.

```text
Frontend

↓

API Gateway

↓

User Service

↓

Payment Service

↓

Inventory Service
```

A **Correlation ID** or **Trace ID** is added to the metadata.

Example:

```text
trace-id

7c19a21e-8d44
```

Every service logs the same trace ID.

This makes it much easier to follow a request across the entire system.

---

# Metadata Size

Metadata should remain small.

Good examples:

- Authentication token
- Request ID
- Language
- User ID

Avoid sending:

- Images
- Large JSON objects
- Files
- Business data

Large metadata increases network overhead and reduces performance.

---

# Metadata Keys

Metadata keys are generally lowercase.

Examples:

```text
authorization

request-id

trace-id

user-agent

client-version
```

Binary metadata keys typically end with:

```text
-bin
```

Example:

```text
signature-bin
```

---

# Best Practices

When using metadata:

- Use metadata only for contextual information.
- Keep metadata small.
- Store business data inside request messages.
- Use metadata for authentication and tracing.
- Use consistent key names across services.
- Protect sensitive metadata using TLS.

---

# Common Mistakes

Avoid the following mistakes:

- Sending business data as metadata.
- Storing large objects in metadata.
- Using inconsistent metadata keys.
- Sending sensitive information over insecure channels.
- Duplicating data already present in the request message.

---

# Key Takeaways

- Metadata is additional contextual information sent alongside gRPC requests and responses.
- Metadata is transmitted as key-value pairs and is similar to HTTP headers.
- Request metadata flows from the client to the server, while response metadata flows back to the client.
- Metadata is commonly used for authentication, authorization, tracing, logging, and localization.
- Business data should remain inside Protocol Buffer messages, while contextual information belongs in metadata.
- Keeping metadata small and consistent improves performance and maintainability.