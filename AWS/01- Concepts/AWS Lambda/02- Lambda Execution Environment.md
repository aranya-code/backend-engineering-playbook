# 02- Lambda Execution Environment.md

# Lambda Execution Environment

One of the most misunderstood aspects of AWS Lambda is what actually happens after a function is invoked.

Many developers think AWS simply "runs their code." In reality, Lambda creates and manages **execution environments** behind the scenes. Understanding this lifecycle is essential for writing performant, scalable, and cost-efficient serverless applications.

---

# What is an Execution Environment?

An **execution environment** is an isolated runtime where AWS executes your Lambda function.

It contains:

- Operating system
- Runtime (Python, Node.js, Java, etc.)
- Your application code
- Dependencies
- Environment variables
- Temporary storage (`/tmp`)
- Memory allocated to the function

Think of it as a lightweight container that exists only to execute your function.

```text
+------------------------------------+
| Lambda Execution Environment       |
|------------------------------------|
| Amazon Linux                       |
| Runtime (Python/Node/Java)         |
| Function Code                      |
| Dependencies                       |
| Environment Variables              |
| /tmp Storage                       |
| Allocated Memory                   |
+------------------------------------+
```

---

# Firecracker MicroVMs

AWS Lambda runs functions inside **Firecracker MicroVMs**.

Firecracker is a virtualization technology developed by AWS that combines:

- Security of Virtual Machines
- Speed of Containers

Unlike Docker containers alone, Firecracker provides stronger isolation between customers while maintaining fast startup times.

Benefits include:

- Lightweight virtualization
- Fast boot times
- Secure multi-tenancy
- Efficient resource utilization

> Firecracker is also used by AWS Fargate.

---

# Execution Lifecycle

A Lambda execution environment goes through several phases.

```text
Request Arrives

        │

        ▼

Execution Environment Exists?

      /     \

    Yes      No

    │         │

    ▼         ▼

Warm Start   Cold Start

    │         │

    └────┬────┘

         ▼

Run Handler

         ▼

Return Response

         ▼

Environment Frozen

         ▼

Wait For Next Request
```

---

# Phase 1 — Environment Creation (Cold Start)

If no execution environment exists, AWS performs a **Cold Start**.

During this phase AWS:

1. Allocates compute resources
2. Starts a Firecracker MicroVM
3. Loads the runtime
4. Downloads function code
5. Loads dependencies
6. Executes initialization code
7. Invokes the handler

This entire process adds latency before your function begins processing.

Example:

```python
import boto3

client = boto3.client("s3")   # Executed once during initialization

def handler(event, context):
    return {"statusCode": 200}
```

The `boto3.client()` call runs only during initialization, not for every invocation.

---

# Phase 2 — Invocation

After initialization completes, Lambda calls your handler function.

```python
def handler(event, context):
    print("Processing request")
```

Everything inside the handler executes on every request.

---

# Phase 3 — Freeze

Once execution finishes, AWS does **not immediately destroy** the environment.

Instead, it freezes it.

Frozen environments retain:

- Initialized SDK clients
- Imported modules
- Cached objects
- Database connection pools (if still valid)
- Variables in global scope
- Files stored in `/tmp`

This enables faster subsequent invocations.

---

# Phase 4 — Warm Start

If another request arrives before AWS discards the environment, Lambda reuses it.

```text
Request

↓

Existing Environment Found

↓

Skip Initialization

↓

Execute Handler
```

This is called a **Warm Start**.

Warm starts are significantly faster because initialization is skipped.

---

# Cold Start vs Warm Start

| Cold Start | Warm Start |
|------------|------------|
| Creates new environment | Reuses existing environment |
| Runtime initialization | No initialization |
| Higher latency | Low latency |
| Downloads function | Already available |
| Imports dependencies | Already loaded |
| Runs global code | Global code skipped |

---

# Initialization Code

Everything outside the handler executes only once per execution environment.

Example:

```python
import boto3
import os

client = boto3.client("s3")
bucket = os.environ["BUCKET_NAME"]

print("Initialization")
```

The following executes on every request:

```python
def handler(event, context):
    print("Inside handler")
```

Output:

First request:

```
Initialization
Inside handler
```

Second request:

```
Inside handler
```

---

# Global Variables

Global variables persist across warm invocations.

```python
counter = 0

def handler(event, context):
    global counter
    counter += 1
    return counter
```

Possible output:

Request 1

```
1
```

Request 2

```
2
```

Request 3

```
3
```

However, you **must never rely on this behavior**, because AWS can create a new execution environment at any time.

---

# Reusing SDK Clients

Bad:

```python
def handler(event, context):

    client = boto3.client("s3")

    ...
```

Good:

```python
client = boto3.client("s3")

def handler(event, context):

    ...
```

Creating SDK clients during initialization reduces latency.

---

# Database Connections

A common production optimization is to create database connections outside the handler.

```python
import psycopg2

connection = psycopg2.connect(...)

def handler(event, context):

    cursor = connection.cursor()
```

Advantages:

- Lower latency
- Fewer database handshakes
- Better throughput

Be aware that idle connections may be closed by the database, so reconnection logic is often necessary.

---

# Temporary Storage (/tmp)

Each Lambda execution environment includes temporary storage mounted at:

```
/tmp
```

Characteristics:

- Private to the execution environment
- Persists across warm invocations
- Deleted when the environment is destroyed
- Useful for caching large files

Example:

```python
with open("/tmp/data.json", "w") as f:
    f.write("Hello")
```

Common use cases:

- Image processing
- PDF generation
- ML model caching
- ZIP extraction
- Video processing

---

# Environment Variables

Execution environments expose configured environment variables.

```python
import os

bucket = os.environ["BUCKET_NAME"]
```

Use environment variables for:

- Configuration
- Feature flags
- Resource names
- API endpoints

Avoid storing secrets directly; prefer AWS Secrets Manager or Parameter Store.

---

# Memory Allocation

Memory is allocated per execution environment.

Increasing memory also increases:

- CPU
- Network throughput
- Disk I/O

Example:

```
128 MB

↓

Fractional CPU

------------------

2048 MB

↓

Much higher CPU allocation
```

Choosing more memory can reduce execution time enough to lower overall cost.

---

# Environment Reuse is Not Guaranteed

AWS may destroy execution environments at any time.

Reasons include:

- Idle timeout
- Infrastructure maintenance
- Scaling down
- Runtime updates
- Deployment of new versions

Therefore:

❌ Never depend on:

- In-memory caches
- Global counters
- Local session state

Persist important state externally.

---

# Stateless Design

Each invocation should be independent.

Instead of:

```text
Lambda

↓

Memory
```

Use:

```text
Lambda

↓

Redis

↓

DynamoDB

↓

S3

↓

RDS
```

---

# Best Practices

✅ Initialize SDK clients outside the handler

✅ Cache immutable configuration

✅ Reuse database connections

✅ Keep initialization lightweight

✅ Use `/tmp` for temporary caching

✅ Design for stateless execution

❌ Don't assume execution environments are reused

❌ Don't store user session data in memory

❌ Don't keep mutable global state

---

# Real Production Example

An image processing service:

```text
Image Upload

↓

S3 Trigger

↓

Lambda

↓

Download Image

↓

Store in /tmp

↓

Resize

↓

Upload Thumbnail

↓

Return
```

The image library is loaded once during initialization, while the resize logic runs on every invocation.

---

# Senior Backend Engineering Perspective

Understanding the execution environment helps optimize:

- Cold start latency
- Dependency loading
- Database connection reuse
- Memory utilization
- Throughput
- Cost

Experienced backend engineers place expensive initialization outside the handler while ensuring their functions remain stateless and resilient to execution environment replacement.

---

# Interview Questions

### Beginner

- What is a Lambda execution environment?
- What is stored in an execution environment?
- What is the purpose of `/tmp` storage?

### Intermediate

- What happens during a cold start?
- What code executes during initialization?
- Why create SDK clients outside the handler?

### Senior

- How does Firecracker improve Lambda?
- How would you optimize initialization latency?
- How do you safely reuse database connections?
- Why shouldn't business logic depend on warm starts?
- How would you design a highly performant Lambda execution model?

---

# Key Takeaways

- Lambda runs inside isolated Firecracker MicroVM execution environments.
- The execution lifecycle consists of initialization, invocation, freeze, and possible reuse.
- Initialization code executes only once per execution environment.
- Warm starts improve performance by reusing existing environments.
- Execution environments are ephemeral; functions must remain stateless.
- Reusing SDK clients, database connections, and cached resources can significantly improve performance, provided the application does not rely on their persistence.