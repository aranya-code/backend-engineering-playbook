# 10- Lambda Runtime Lifecycle

# Lambda Runtime Lifecycle

One of the most important topics for senior backend engineers is understanding **how AWS Lambda actually executes your code**.

Many developers know about **cold starts**, but very few understand the complete lifecycle of a Lambda execution environment.

Understanding the runtime lifecycle helps you:

- Reduce latency
- Optimize initialization code
- Reuse expensive resources
- Debug production issues
- Optimize costs
- Improve scalability

This chapter builds upon the concepts introduced in **Execution Environment** and explores what happens internally from the moment a Lambda is invoked until the execution environment is destroyed.

---

# High-Level Lifecycle

Every Lambda execution environment goes through the following phases.

```text
Invoke

↓

Environment Exists?

↓

No
│
├──────────────┐
│              │
▼              ▼

Initialization  (Cold Start)

↓

Invoke Handler

↓

Return Response

↓

Freeze Environment

↓

Wait

↓

Next Request?

↓

Yes

↓

Thaw Environment

↓

Invoke Handler

↓

Freeze Again

↓

Eventually Destroyed
```

---

# Runtime Lifecycle Phases

The Lambda runtime lifecycle consists of six major phases.

```
1. Environment Creation

↓

2. Runtime Initialization

↓

3. Function Initialization

↓

4. Handler Execution

↓

5. Freeze

↓

6. Shutdown
```

Each phase has different performance characteristics.

---

# Phase 1 — Environment Creation

When Lambda receives an invocation and no execution environment exists, AWS creates one.

AWS allocates:

- Firecracker MicroVM
- Memory
- CPU
- Ephemeral storage
- Runtime

```text
Request

↓

Allocate Resources

↓

Create MicroVM
```

This phase contributes to **cold start latency**.

---

# Phase 2 — Runtime Initialization

AWS starts the selected runtime.

Examples:

```
Python 3.13

Node.js

Java

.NET

Go
```

The runtime loads:

- Language interpreter
- Runtime libraries
- Bootstrap process

Example:

```text
Firecracker

↓

Python Runtime

↓

Ready
```

---

# Phase 3 — Function Initialization (INIT Phase)

Now AWS loads your deployment package.

During this stage Lambda:

- Downloads code
- Loads dependencies
- Imports modules
- Executes global variables
- Runs initialization logic

Example:

```python
import boto3

client = boto3.client("s3")

config = load_config()

print("INIT")
```

Everything outside the handler executes here.

---

# Initialization Code

Example:

```python
import boto3

s3 = boto3.client("s3")

database = connect_database()

cache = {}

print("Initialized")
```

This executes **once per execution environment**, not once per request.

---

# INIT vs Handler

Initialization:

```python
client = boto3.client("s3")
```

Handler:

```python
def handler(event, context):

    return {}
```

The handler executes for every invocation.

---

# Phase 4 — Invocation

Lambda invokes the handler.

```python
def handler(event, context):

    print("Processing Request")

    return {}
```

During this phase:

- Business logic executes
- AWS measures duration
- Billing begins
- Logs are generated

---

# Execution Flow

```text
Initialization

↓

Handler

↓

Database

↓

External API

↓

Return Response
```

Everything inside the handler is included in the billed duration.

---

# Successful Execution

```text
Request

↓

Lambda

↓

Success

↓

Return Response

↓

Freeze
```

---

# Failed Execution

```text
Request

↓

Lambda

↓

Exception

↓

Error Returned

↓

Freeze
```

The environment may still be reused.

---

# Phase 5 — Freeze

This phase surprises many developers.

Lambda does **not** immediately terminate the execution environment.

Instead:

```text
Handler Complete

↓

Freeze Memory

↓

Keep Environment Alive
```

Frozen resources include:

- Imported modules
- SDK clients
- Database connections
- Cached variables
- /tmp contents

---

# What Gets Frozen?

```
✓ boto3 client

✓ requests.Session()

✓ Global variables

✓ Imported modules

✓ Cached files

✓ /tmp

✓ Database connections*
```

*Database connections may expire independently.

---

# Warm Start

Suppose another request arrives.

```text
Request

↓

Existing Environment

↓

Skip INIT

↓

Invoke Handler
```

This is known as a **Warm Start**.

Warm starts are significantly faster than cold starts.

---

# Phase 6 — Shutdown

Eventually AWS destroys the environment.

Reasons include:

- Low traffic
- Infrastructure updates
- Scaling down
- New deployment
- Runtime patching

```text
Frozen

↓

Idle

↓

Destroy Environment
```

Everything in memory is lost.

---

# Complete Lifecycle Example

```text
Request 1

↓

Create Environment

↓

INIT

↓

Handler

↓

Freeze

-----------------------

Request 2

↓

Reuse Environment

↓

Handler

↓

Freeze

-----------------------

Idle

↓

Destroy
```

---

# Execution Timeline

```text
Cold Start

│

├── Create VM

├── Start Runtime

├── Load Code

├── Import Libraries

├── Execute Global Code

└── Handler

----------------------------

Warm Start

│

└── Handler Only
```

---

# Billing Lifecycle

Lambda billing begins when initialization starts.

```
Cold Start

↓

Initialization

↓

Handler

↓

Return
```

Both INIT and Handler time are billed.

Warm start:

```
Handler Only
```

Lower latency.

---

# Global Variable Example

```python
counter = 0

def handler(event, context):

    global counter

    counter += 1

    return counter
```

Possible output:

```
Request 1

1

Request 2

2

Request 3

3
```

Eventually:

```
Environment Destroyed

↓

Request 4

1
```

Never rely on global state.

---

# Database Connection Reuse

Good:

```python
connection = create_connection()

def handler(event, context):

    connection.query(...)
```

Bad:

```python
def handler(event, context):

    connection = create_connection()
```

Opening new database connections on every request increases latency.

---

# /tmp Lifecycle

```
Initialization

↓

Create File

↓

Freeze

↓

Warm Start

↓

Reuse File

↓

Destroy Environment

↓

File Deleted
```

---

# Runtime API

Internally, Lambda runtimes communicate using the **Lambda Runtime API**.

```text
Lambda Service

↓

Runtime API

↓

Python Runtime

↓

Handler
```

Custom runtimes also use this API.

---

# Runtime Reuse

AWS attempts to reuse execution environments whenever possible.

Benefits:

- Faster execution
- Lower latency
- Reduced initialization time
- Better SDK reuse

However:

**Reuse is never guaranteed.**

---

# Common Misconceptions

## "Global Variables Always Persist"

Incorrect.

They persist only while the execution environment exists.

---

## "Lambda Terminates After Every Request"

Incorrect.

Most environments remain frozen.

---

## "Initialization Runs Every Time"

Incorrect.

Initialization only runs during cold starts.

---

# Best Practices

✅ Initialize SDK clients globally.

✅ Load configuration during INIT.

✅ Cache immutable data.

✅ Reuse HTTP sessions.

✅ Reuse database connections.

✅ Keep initialization lightweight.

❌ Never depend on execution environment reuse.

---

# Production Example

Image processing pipeline:

```text
Request

↓

Create Environment

↓

Load Pillow Library

↓

Handler

↓

Resize Image

↓

Freeze

↓

Next Upload

↓

Reuse Pillow Library

↓

Resize Image
```

Loading the image library only once significantly reduces latency.

---

# Senior Backend Engineering Perspective

Understanding the Lambda runtime lifecycle is essential for building high-performance serverless systems.

Senior engineers optimize the **INIT phase** by minimizing dependency loading, moving expensive operations outside the handler only when beneficial, and ensuring functions remain stateless despite execution environment reuse.

They also understand that execution environments are ephemeral and design applications that benefit from warm starts without relying on them.

A deep understanding of the lifecycle enables better decisions around cold start optimization, database connectivity, caching, memory usage, and cost management.

---

# Interview Questions

### Beginner

- What phases make up the Lambda runtime lifecycle?
- What happens during initialization?
- What is a warm start?

### Intermediate

- What resources survive a warm start?
- Why should SDK clients be created outside the handler?
- When is a Lambda execution environment destroyed?

### Senior

- How would you optimize the INIT phase of a Lambda function?
- Why shouldn't applications depend on execution environment reuse?
- How would you design a Lambda function to maximize warm-start performance while remaining stateless?
- How does the runtime lifecycle affect latency, cost, and scalability?

---

# Key Takeaways

- The Lambda runtime lifecycle consists of environment creation, runtime initialization, function initialization, handler execution, freeze, and shutdown.
- Initialization code executes only during cold starts, while the handler executes for every invocation.
- Execution environments are frozen after successful or failed executions and may be reused for future requests.
- Warm starts reduce latency by skipping initialization, but reuse is never guaranteed.
- Understanding the runtime lifecycle is fundamental for optimizing performance, reducing costs, and designing resilient serverless applications.