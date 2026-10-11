# 11- Comparison Questions and Common Interview Traps

## Overview

AWS Lambda interviews often test whether an engineer understands the differences between similar AWS services, invocation mechanisms, scaling controls, and failure-handling features. Memorizing definitions is insufficient because production architecture depends on workload characteristics, delivery guarantees, security boundaries, and operational constraints.

Senior-level answers should explain:

- What each option provides and how it works.
- Which requirements favor one option over another.
- What reliability, performance, and cost trade-offs exist.
- Which assumptions are incorrect or incomplete.
- How the proposed design can be verified in production.

This document focuses on comparison questions, common misconceptions, and interview traps that frequently arise when designing Lambda-based backend systems.

## Lambda vs. ECS/Fargate vs. EC2

### Question: When would you choose Lambda over ECS/Fargate or EC2?

**Model answer:**

The decision depends on execution duration, scaling behavior, runtime requirements, workload predictability, and operational ownership.

| Dimension | AWS Lambda | ECS with Fargate | EC2 |
|---|---|---|---|
| Execution model | Event-driven function invocations | Containerized tasks and services | Virtual machines running applications |
| Infrastructure management | AWS manages the function execution environment | AWS manages the underlying server infrastructure | Customer manages instance configuration and operating-system maintenance |
| Long-running processes | Subject to Lambda execution limits | Suitable for many long-running container workloads | Suitable for long-running workloads |
| Runtime control | Supported managed runtimes or compatible Lambda container images | Greater control over the container environment | Broad operating-system and process control |
| Scaling | Invocation-driven scaling, subject to quotas and configuration | Task and service scaling configured for the workload | Instance scaling and capacity management |
| Persistent processes | Not designed for continuously running application processes | Supported | Supported |
| Operational responsibility | Primarily function, integration, and application configuration | Container, task, networking, scaling, and application configuration | Instance, operating system, runtime, networking, and application configuration |
| Cost model | Invocation, execution duration, memory, and applicable additional features | Task resource allocation and runtime, plus associated services | Instance capacity and associated resources |
| Typical fit | APIs, event processing, scheduled jobs, bursty background work | Containerized APIs, workers, and persistent services | Specialized workloads requiring extensive host control |

**Choose Lambda when:**

- Work is naturally triggered by requests, events, or schedules.
- Execution is bounded and compatible with Lambda's limits.
- Traffic varies significantly.
- You want to minimize infrastructure management.

**Choose ECS/Fargate when:**

- The application requires long-running processes or persistent connections.
- Container-level runtime control is important.
- Workloads are sustained and better suited to service or task management.

**Choose EC2 when:**

- Host-level customization is necessary.
- Specialized software or operating-system control is required.
- The organization needs direct management of instance-level resources.

### Common interview trap

"Lambda is always cheaper because you pay only when it runs."

This is incomplete. Cost depends on invocation frequency, execution duration, memory allocation, provisioned concurrency, data transfer, logging, database capacity, and the cost of connected services. A continuously busy workload may be more economical on containers or instances, depending on its resource profile.

The correct approach is to benchmark representative workloads and compare total system cost, not just compute charges.

## Lambda vs. API Gateway

### Question: Why use API Gateway when Lambda can be invoked directly?

**Model answer:**

Lambda provides the execution environment, while API Gateway provides an API-facing integration layer with capabilities such as routing, authorization integrations, throttling, request handling, and access logging.

| Requirement | API Gateway + Lambda | Direct Lambda invocation |
|---|---|---|
| Public REST or HTTP API | Strong fit | Requires another API-facing mechanism |
| API routing and management | Gateway provides API-level capabilities | Caller manages routing |
| Authentication integration | Supports configured authorization mechanisms | Depends on the caller and invocation permissions |
| AWS service-to-service invocation | Possible, but may add unnecessary overhead | Often simpler |
| API-specific access logging and throttling | Available through gateway configuration | Must be handled by the relevant caller or service |
| Additional cost and latency | Adds gateway processing | Avoids gateway overhead when direct invocation is suitable |

**When direct invocation is appropriate:**

- A trusted AWS service invokes the function.
- An application invokes Lambda through the AWS SDK.
- A workflow orchestrator calls Lambda as one of its tasks.

**When API Gateway is appropriate:**

- External clients need a managed HTTP API.
- API-level authentication, throttling, routing, or observability is required.
- The system benefits from separating its public API contract from the function implementation.

### Common interview trap

"Every Lambda-backed API requires API Gateway."

Not necessarily. Lambda function URLs and Application Load Balancer integrations can be suitable alternatives. The choice depends on authentication, routing, API management, streaming, networking, and operational requirements.

## Lambda Function URLs vs. API Gateway

### Question: When would you use a Lambda function URL instead of API Gateway?

**Model answer:**

A function URL provides an HTTP(S) endpoint directly associated with a Lambda function. It can be useful for simple HTTP integrations where a full API management layer is unnecessary.

| Dimension | Lambda function URL | API Gateway |
|---|---|---|
| Setup complexity | Relatively simple | More configuration options |
| Endpoint | Directly associated with a function | Managed API endpoint |
| Authentication | AWS IAM or unauthenticated mode | Supports multiple configured authorization mechanisms |
| API management | More limited | Broader API routing and management capabilities |
| Throttling and API controls | Must be evaluated against available controls and surrounding architecture | Provides gateway-level controls |
| Cost | No separate API Gateway request charge for the URL itself; other Lambda and service charges still apply | API Gateway charges apply, in addition to relevant backend charges |
| Best fit | Simple HTTP endpoints | APIs needing broader management and integration capabilities |

**Security consideration:** An unauthenticated function URL should be treated as publicly accessible unless other controls in the architecture provide the required protection. An IAM-authenticated URL requires callers to have the necessary permissions and sign requests appropriately.

### Common interview trap

"Function URLs are private because the Lambda function is inside AWS."

The execution environment's location does not make an HTTP endpoint private. Authentication and authorization must be configured explicitly.

## Synchronous vs. Asynchronous Invocation

### Question: How do synchronous and asynchronous Lambda invocations differ?

**Model answer:**

Synchronous invocation waits for the function execution result. Asynchronous invocation accepts the event for processing and returns before the handler's final outcome is known.

| Dimension | Synchronous invocation | Asynchronous invocation |
|---|---|---|
| Caller waits for execution result | Yes | No |
| Handler error returned to caller | Typically available through the invocation result or integration behavior | Not returned as the original submission result |
| Common use case | Interactive API request | Background processing |
| Retry responsibility | Often belongs to the caller or integration, depending on the invocation path | Lambda's asynchronous invocation mechanism has its own retry behavior |
| Delivery and duplication | Depends on the caller and integration | Duplicate processing is possible |
| Best fit | Immediate response required | Processing can complete independently |

Synchronous invocation does not mean that the business operation is transactional or immune to duplicate requests. A caller can time out and retry even if the original operation succeeded.

### Common interview trap

"If the asynchronous invocation returns success, the function completed successfully."

False. The acceptance response means the event was accepted for asynchronous processing, not that the handler completed successfully.

Use application-level status tracking, appropriate failure destinations, and business metrics when eventual completion matters.

## SQS vs. Direct Asynchronous Lambda Invocation

### Question: Why choose SQS instead of invoking Lambda asynchronously?

**Model answer:**

Both approaches can decouple a producer from immediate execution, but SQS provides explicit queue-based buffering and consumer controls.

| Requirement | Direct asynchronous invocation | SQS with Lambda |
|---|---|---|
| Submit work without waiting for handler completion | Supported | Supported |
| Explicit queue depth and backlog visibility | Less direct | Strong fit |
| Buffering and consumer throughput control | More limited | Strong fit |
| Message retention and visibility controls | Managed by Lambda's asynchronous invocation system | Configured through SQS |
| Dead-letter handling | Asynchronous invocation failure mechanisms can be configured | SQS redrive policy and DLQ |
| Batch processing | Not the same queue-based batch model | Supported by event source mappings |
| Operational inspection and replay | Requires the appropriate failure-handling setup | Queue and DLQ provide explicit operational resources |

Choose direct asynchronous invocation when the workload is straightforward and its managed retry behavior meets the requirements. Choose SQS when backlog management, buffering, consumer isolation, or explicit redrive handling is important.

### Common interview trap

"SQS guarantees that every message is processed exactly once."

SQS delivery semantics depend on queue type, and Lambda event source mappings can retry processing. Even with FIFO deduplication features, downstream side effects and application processing still require careful idempotency design.

## SQS Standard vs. SQS FIFO

### Question: When should you choose a FIFO queue?

**Model answer:**

Choose SQS FIFO when the workload requires ordering within message groups and FIFO deduplication behavior is useful.

| Dimension | Standard queue | FIFO queue |
|---|---|---|
| Ordering | Best-effort ordering | Ordering within a message group |
| Delivery behavior | At-least-once delivery | FIFO delivery and deduplication features, with application-level failure handling still required |
| Parallel processing | Broad parallelism | Parallelism across message groups |
| Throughput | Suitable for high-throughput workloads | Depends on FIFO configuration and applicable quotas |
| Typical use case | Independent background jobs | Ordered customer events or sequential operations within a group |

For example, if events for an individual account must be processed in order, use a stable account identifier as the message group identifier.

### Common interview trap

"FIFO means the business operation happens exactly once."

FIFO deduplication does not make arbitrary external side effects transactional. A consumer can perform an operation and fail before successful acknowledgement. Use idempotent processing and durable operation state.

## Event Source Mappings vs. Direct Service Invocation

### Question: What is the difference between an event source mapping and a service invoking Lambda directly?

**Model answer:**

An event source mapping polls or reads from supported event sources, obtains records, and invokes the function with batches. Direct service invocation occurs when a service or caller invokes Lambda through its supported invocation mechanism.

| Dimension | Event source mapping | Direct service invocation |
|---|---|---|
| Examples | SQS, Kinesis Data Streams, DynamoDB Streams | S3 notifications, EventBridge targets, direct SDK invocation |
| Consumption model | Lambda-managed polling or stream consumption | Service or caller initiates the invocation |
| Batching | Supported for applicable event sources | Depends on the invoking service and event mechanism |
| Checkpointing | Relevant to supported stream integrations | Not generally the same checkpoint model |
| Permissions | Mapping, source access, and execution-role requirements depend on the source | Invocation permission and caller configuration depend on the integration |
| Failure handling | Source-specific retries, checkpoints, and partial batch behavior | Depends on the service's delivery and retry model |

The distinction matters because retry semantics, ordering, batch failures, and scaling controls are not identical across integrations.

### Common interview trap

"All Lambda triggers behave the same way."

They do not. An SQS event source mapping, DynamoDB Streams mapping, S3 notification, and asynchronous SDK invocation have different delivery and failure-handling semantics.

## Reserved Concurrency vs. Provisioned Concurrency

### Question: What problem does each concurrency setting solve?

**Model answer:**

Reserved concurrency controls the concurrency capacity allocated to a function and establishes a function-level upper bound. Provisioned concurrency prepares execution environments in advance to reduce initialization latency for supported invocation paths.

| Dimension | Reserved concurrency | Provisioned concurrency |
|---|---|---|
| Primary purpose | Reserve function concurrency and cap simultaneous executions | Reduce cold-start latency by keeping execution environments initialized |
| Limits concurrency | Yes | Provides configured ready capacity but is not a substitute for all concurrency controls |
| Keeps environments initialized | No | Yes |
| Protects downstream systems | Can limit function concurrency | May need to be combined with other concurrency controls |
| Additional cost | No separate provisioned-concurrency charge for the setting itself; normal invocation charges apply | Additional charges apply for provisioned capacity and execution |
| Typical use case | Protect a database or reserve capacity for a critical function | Latency-sensitive APIs with predictable or planned traffic |

Provisioned concurrency is associated with a published version or alias. Verify that production traffic invokes the correct qualifier and that the provisioned capacity is ready.

### Common interview traps

- Reserved concurrency does not eliminate cold starts.
- Provisioned concurrency does not automatically fix slow application code.
- Provisioned concurrency does not mean unlimited traffic can be handled without additional capacity planning.
- Increasing concurrency without considering downstream limits can make an incident worse.

## Provisioned Concurrency vs. SnapStart

### Question: How do these features differ?

**Model answer:**

Provisioned concurrency maintains initialized execution environments ready to serve requests. SnapStart uses a snapshot-based initialization mechanism for supported runtimes and configurations to reduce startup work.

| Dimension | Provisioned concurrency | SnapStart |
|---|---|---|
| Mechanism | Maintains initialized execution environments | Restores execution environments from a snapshot created for a published version |
| Main goal | Reduce cold-start latency and provide ready capacity | Reduce initialization time where supported |
| Capacity planning | Explicit provisioned capacity is required | Does not replace capacity and concurrency planning |
| Runtime constraints | Depends on the supported runtime and invocation configuration | Has specific runtime and configuration compatibility requirements |
| Cost considerations | Provisioned-capacity charges apply | Feature-specific pricing and execution charges must be evaluated |
| Key concern | Readiness, utilization, alias targeting, and capacity | Snapshot lifecycle, initialization assumptions, and runtime compatibility |

Feature availability and limitations can change. Verify current AWS documentation for the chosen runtime and Region before committing to a design.

### Common interview trap

"SnapStart and provisioned concurrency are interchangeable."

They address related latency problems through different mechanisms. Selection should be based on runtime support, startup behavior, latency objectives, capacity needs, and total cost.

## Lambda Layers vs. Deployment Packages vs. Container Images

### Question: How should shared dependencies be packaged?

**Model answer:**

Choose the packaging model that balances dependency reuse, artifact size, reproducibility, native-library compatibility, and deployment complexity.

| Option | Advantages | Limitations |
|---|---|---|
| ZIP deployment package | Simple deployment for application code and dependencies | Package size and dependency compatibility must be managed |
| Lambda layers | Share dependencies or extensions across functions | Layer versioning and compatibility become additional operational responsibilities |
| Lambda container image | Supports larger container-based packaging and greater control over included dependencies | Image build, scanning, registry access, and image lifecycle management add complexity |

Layers are useful when several functions share stable dependencies. They are not automatically better than bundling dependencies with each function. A shared layer can introduce coordinated upgrades and compatibility risks.

Container images are useful for complex dependencies or container-oriented build workflows, but Lambda container images must conform to Lambda's supported image requirements.

### Common interview trap

"Lambda container images run like ordinary long-lived Docker containers."

A Lambda container image uses Lambda's execution and invocation model. It does not automatically become a continuously running web server simply because it is packaged as a container.

## Lambda vs. Step Functions

### Question: When should workflow orchestration move from application code into Step Functions?

**Model answer:**

Use Step Functions when a workflow requires durable state, branching, parallel execution, retry policies, timeouts, or operational visibility across multiple steps.

| Requirement | Lambda-managed orchestration | Step Functions |
|---|---|---|
| Simple short sequence | Can be appropriate | May add unnecessary complexity |
| Durable multi-step state | Requires custom state management or another service | Core workflow capability |
| Branching and parallel execution | Implemented in application code or supporting services | Defined in the workflow |
| Retry and timeout policies | Application-specific logic | Workflow-level configuration is available |
| Operational visibility | Requires custom instrumentation and state tracking | Workflow execution history and status are available |
| Cost model | Lambda and supporting service costs | Workflow execution or state-transition charges, depending on workflow type, plus task costs |

Step Functions does not automatically reverse external side effects. Compensation, idempotency, and business-state consistency must still be designed.

### Common interview trap

"Step Functions eliminates the need for error handling."

It provides workflow orchestration and failure-handling primitives. The application must still define retryable errors, terminal failures, compensation, and recovery behavior.

## Lambda@Edge vs. CloudFront Functions

### Question: Which should you use for edge processing?

**Model answer:**

Both execute logic near CloudFront's edge locations, but they differ in runtime model, execution capabilities, and suitable workloads.

| Dimension | CloudFront Functions | Lambda@Edge |
|---|---|---|
| Typical use | Lightweight request and response manipulation | More complex edge logic requiring broader execution capabilities |
| Runtime model | Specialized lightweight JavaScript execution | Lambda-based execution with supported runtimes and event types |
| Common use cases | Header changes, URL rewrites, redirects, simple request authorization logic | More complex request processing and origin-response workflows where supported |
| Resource model | Designed for short, lightweight operations | Supports more extensive execution capabilities, subject to Lambda@Edge constraints |
| Operational constraints | Specialized runtime and feature limitations | Regional deployment and replication behavior, supported runtimes, and edge-specific restrictions |

Select based on the required event phase, runtime capabilities, latency needs, and service constraints. Do not assume that all Lambda features available in a regional function are available to Lambda@Edge.

## Common Lambda Interview Traps

### Trap: "Lambda is stateless, so it cannot reuse anything between invocations."

**Correct answer:**

Lambda functions should not rely on execution-environment memory for durable business state, but an execution environment may be reused. SDK clients, database connections, and immutable configuration can often be initialized outside the handler and reused safely.

For example:

```python
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("orders")


def handler(event, context):
    order_id = event["order_id"]

    response = table.get_item(Key={"order_id": order_id})

    return response.get("Item")
```

The SDK resource is initialized outside the handler to reduce repeated initialization. The example assumes the table key is `order_id` and that the execution role has the necessary permissions.

Do not store user-specific data in global mutable variables and assume the next invocation will receive a clean execution environment.

### Trap: "Lambda automatically retries every failed invocation in the same way."

**Correct answer:**

Retry behavior depends on the invocation model and event source.

- Synchronous callers commonly decide whether to retry.
- Asynchronous Lambda invocation has its own retry and failure-handling behavior.
- SQS event source mappings use queue visibility and redelivery behavior.
- Stream-based event source mappings have source-specific retry and checkpoint semantics.

Understand the integration before defining retry policies.

### Trap: "Increasing timeout always fixes Lambda failures."

**Correct answer:**

A timeout increase may help when the workload legitimately needs more time, but it can also increase execution duration, concurrency pressure, and cost.

First identify whether the bottleneck is a slow dependency, connection failure, inefficient algorithm, or insufficient timeout. Fix the underlying problem and increase the timeout only when justified.

### Trap: "Lambda scales infinitely."

**Correct answer:**

Lambda can scale substantially, but execution concurrency, scaling behavior, account quotas, function configuration, event-source limits, and downstream capacity all matter.

A scalable Lambda application must coordinate concurrency with databases, external APIs, and queues.

### Trap: "A Lambda function's execution role controls who can invoke it."

**Correct answer:**

The execution role controls what the function can access after execution begins. Invocation authorization is governed by the caller's permissions, the function's resource-based policy, and the applicable integration's permission model.

A secure design distinguishes runtime permissions from invocation permissions.

### Trap: "A successful Lambda invocation means the business operation succeeded."

**Correct answer:**

A function may return success after accepting work for asynchronous processing, or its code may incorrectly suppress a business failure. Track business outcomes explicitly.

Examples include payment confirmation, order completion, file-processing status, and successful reconciliation.

### Trap: "A DLQ automatically fixes failed events."

**Correct answer:**

A dead-letter queue preserves messages or failure records for investigation and recovery according to the relevant service's behavior. Operators still need alarms, ownership, root-cause analysis, and a safe replay procedure.

### Trap: "All Lambda cold starts can be eliminated by increasing memory."

**Correct answer:**

Memory can affect CPU allocation and performance, but it does not guarantee that initialization will be avoided. Cold-start behavior depends on runtime initialization, dependency loading, networking, and available execution environments.

Measure initialization behavior and evaluate provisioned concurrency or SnapStart where supported.

### Trap: "Moving Lambda into a public subnet gives it Internet access."

**Correct answer:**

Subnet placement alone does not provide a public IP address or a working Internet route. Validate route tables, NAT or other egress mechanisms, security groups, network ACLs, and DNS.

## How to Answer Comparison Questions at Senior Level

Use a consistent answer structure:

1. **State the distinction:** Explain the primary purpose of each option.
2. **Identify the requirement:** Name the workload characteristic that determines the choice.
3. **Explain the operational impact:** Discuss failure handling, security, scaling, and monitoring.
4. **Describe the trade-off:** Include cost, complexity, latency, or delivery semantics.
5. **Validate the decision:** Explain what you would measure or test before production rollout.

For example, when comparing SQS with direct asynchronous Lambda invocation, do not stop at "SQS is a queue." Explain whether explicit backlog management, consumer throttling, message retention, and redrive behavior justify adding SQS to the architecture.

## Key Takeaways

- Compare AWS services by workload requirements, execution semantics, reliability, security, and total system cost rather than by feature lists alone.
- Distinguish invocation authorization from execution-role permissions, and distinguish successful event acceptance from successful business processing.
- Understand that retry, ordering, batching, and delivery guarantees vary across Lambda invocation models and event sources.
- Treat concurrency, provisioned capacity, database connections, and downstream throughput as related capacity-planning concerns.
- In interviews, explain the trade-offs, failure modes, and verification strategy behind every architecture choice rather than presenting a single service as universally superior.