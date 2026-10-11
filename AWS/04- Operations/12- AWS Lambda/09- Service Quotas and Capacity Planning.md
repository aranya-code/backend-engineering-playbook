# 09- Service Quotas and Capacity Planning

## Overview

AWS Lambda scales automatically by creating execution environments in response to incoming workload demand. However, automatic scaling does not eliminate capacity constraints. Lambda has account-level quotas, function-level concurrency controls, event-source-specific scaling behavior, and downstream capacity dependencies that must be considered when designing production systems.

Capacity planning ensures that a serverless application can absorb expected traffic, handle bursts, recover from failures, and protect dependent systems without unnecessary cost or throttling.

This document covers quota discovery, concurrency calculations, capacity management, event-source scaling, downstream protection, monitoring, and operational readiness.

## Lambda Capacity Model

Lambda capacity is influenced by several interacting factors:

- **Concurrency:** The number of function invocations executing simultaneously.
- **Invocation rate:** The number of invocations arriving per second.
- **Execution duration:** The time each invocation occupies an execution environment.
- **Account concurrency quota:** The regional account-level concurrency limit.
- **Reserved concurrency:** Capacity reserved for a specific function and excluded from the unreserved pool.
- **Provisioned concurrency:** Pre-initialized execution environments allocated to a published version or alias.
- **Event-source scaling:** The rate at which an integration supplies work to Lambda.
- **Downstream capacity:** The throughput and connection limits of databases, APIs, caches, and other dependencies.

A function can have sufficient Lambda concurrency and still fail because PostgreSQL, Redis, or an external API cannot handle the resulting load.

### Concurrency and throughput

Concurrency can be estimated using Little's Law:

\[
C \approx \lambda \times W
\]

Where:

- \(C\) is average concurrent execution demand.
- \(\lambda\) is the arrival rate in invocations per second.
- \(W\) is average execution duration in seconds.

For example, if a function receives 200 invocations per second and each invocation takes 0.25 seconds:

\[
C \approx 200 \times 0.25 = 50
\]

The function requires approximately 50 concurrent executions under these average conditions.

This estimate is not a safe capacity target by itself. Production planning must account for burst traffic, tail latency, retries, uneven request distribution, and downstream constraints.

### Concurrency is not the same as request rate

A function processing 100 requests per second at 100 milliseconds per request may need approximately 10 concurrent executions. The same request rate at two seconds per request may need approximately 200.

Consequently, a latency regression can increase concurrency even when traffic remains unchanged.

## Understand Lambda Quotas

Lambda quotas have different scopes and adjustment mechanisms. Some are account-level, some are function-specific, and others depend on an integration or deployment configuration.

Do not hard-code quota values into operational procedures without checking the current AWS documentation and the affected account and Region.

### Important quota categories

| Category | What to investigate | Operational impact |
|---|---|---|
| Concurrent executions | Regional account concurrency quota | Invocations may be throttled when available capacity is exhausted |
| Function timeout | Maximum configured execution duration | Long-running work may be terminated before completion |
| Memory and ephemeral storage | Supported configuration ranges | Large workloads may require different resource settings |
| Deployment package size | ZIP or container-image constraints | Deployment or initialization may fail |
| Invocation payload | Limits for the invocation model and integration | Large requests or responses may be rejected |
| Event-source scaling | Source-specific concurrency and throughput controls | Work may accumulate in queues or streams |
| Provisioned concurrency | Allocated capacity and applicable quotas | Latency objectives may not be met if capacity is insufficient |
| Regional service capacity | Account and Region availability | Limits and supported capabilities may differ by Region |

For exact values, consult the current [AWS Lambda quotas documentation](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html).

### Inspect account concurrency settings

**Read-only AWS CLI command:**

```bash
aws lambda get-account-settings \
  --region ap-south-1 \
  --query 'AccountLimit.{
    ConcurrentExecutions:ConcurrentExecutions,
    UnreservedConcurrentExecutions:UnreservedConcurrentExecutions
  }'
```

The response provides account-level concurrency information for the selected Region.

`UnreservedConcurrentExecutions` is especially important when evaluating whether functions without reserved concurrency have enough shared capacity.

### Inspect function reserved concurrency

**Read-only:**

```bash
aws lambda get-function-concurrency \
  --function-name order-processor \
  --region ap-south-1
```

If no reserved concurrency is configured, the command may return a resource-not-found response for the concurrency configuration.

### Inspect provisioned concurrency

**Read-only:**

```bash
aws lambda get-provisioned-concurrency-config \
  --function-name order-processor \
  --qualifier production \
  --region ap-south-1
```

The qualifier must refer to the applicable published version or alias.

Inspect allocation, requested capacity, and status before assuming provisioned capacity is ready to serve traffic.

### Request a quota increase

When workload requirements exceed an adjustable service quota:

1. Identify the exact quota and its scope.
2. Measure current usage and forecast peak demand.
3. Estimate the required capacity, including a justified safety margin.
4. Check whether the quota is adjustable in the relevant Region.
5. Submit the request through Service Quotas or the applicable AWS support process.
6. Load-test the workload and verify the resulting capacity before relying on it.

A quota increase does not guarantee that downstream systems can sustain the additional load.

## Account-Level Concurrency Planning

Lambda concurrency is shared across functions in an account and Region, subject to reserved and provisioned concurrency behavior and applicable service rules.

Consider a regional concurrency quota of 1,000 as a hypothetical planning example. If several workloads share that quota, one function's traffic spike can reduce the capacity available to unrelated functions.

### Capacity allocation strategy

| Workload | Capacity strategy | Reason |
|---|---|---|
| Customer-facing API | Evaluate reserved concurrency and latency requirements | Protect critical request processing from unrelated workloads |
| Background queue consumer | Use an appropriate concurrency ceiling | Prevent downstream overload |
| Scheduled batch processing | Limit concurrency when work can be delayed | Avoid competing with latency-sensitive workloads |
| Latency-sensitive endpoint | Consider provisioned concurrency when cold-start latency matters | Keep allocated execution environments initialized |
| Noncritical asynchronous processing | Share unreserved capacity where appropriate | Avoid reserving capacity unnecessarily |

Reserved concurrency both reserves capacity for a function and sets its concurrency ceiling. It is useful for protecting critical workloads and limiting a consumer, but a poorly chosen reservation can reduce capacity available to other functions.

### Avoid capacity fragmentation

Do not reserve concurrency for every function without a clear reason. Excessive reservations can constrain the unreserved pool even when some reserved capacity is idle.

Review reservations as part of capacity planning, especially after service decomposition creates many independent functions.

## Reserved Concurrency

Reserved concurrency is a function-level allocation and maximum concurrency setting.

Use it when:

- A critical function must retain a share of account capacity.
- A queue consumer must not overwhelm a database.
- A function's maximum parallelism needs to be controlled.
- A noisy workload must be prevented from consuming excessive concurrency.

### Configure reserved concurrency

**State-changing command:**

```bash
aws lambda put-function-concurrency \
  --function-name order-processor \
  --reserved-concurrent-executions 100 \
  --region ap-south-1
```

This example reserves 100 concurrent executions for the function and sets its concurrency ceiling to 100.

Verify the result:

```bash
aws lambda get-function-concurrency \
  --function-name order-processor \
  --region ap-south-1
```

Choose the value based on measured demand and downstream capacity, not merely the desired Lambda throughput.

### Remove reserved concurrency

**State-changing command:**

```bash
aws lambda delete-function-concurrency \
  --function-name order-processor \
  --region ap-south-1
```

This removes the function's reserved concurrency configuration. It does not delete the function, but it changes its capacity allocation and throttling behavior.

Verify the resulting configuration and monitor the workload after the change.

## Provisioned Concurrency

Provisioned concurrency allocates pre-initialized execution environments for a published version or alias. It is intended to reduce initialization latency for workloads with strict response-time requirements.

It does not eliminate every source of latency. Network calls, database queries, downstream service delays, and application processing still affect total response time.

### When to use it

Provisioned concurrency may be appropriate for:

- Interactive APIs with strict latency objectives.
- Predictable traffic windows.
- Workloads with expensive initialization.
- Functions where cold-start latency materially affects user experience.

It may be unnecessary for infrequent, latency-tolerant background jobs.

### Operational considerations

- Provisioned capacity incurs cost even when it is not fully utilized.
- Allocation and initialization take time.
- Traffic exceeding provisioned capacity can use other available execution capacity, subject to function and account limits.
- Provisioned concurrency must be associated with an appropriate published version or alias.
- Deployment workflows must account for readiness before directing latency-sensitive traffic.

### Inspect utilization and readiness

Use the provisioned concurrency configuration command and the relevant CloudWatch metrics to evaluate allocated capacity, spillover, utilization, and invocation behavior.

Do not treat successful configuration submission as proof that all requested capacity is ready.

## Capacity Planning for Event Sources

Lambda's scaling behavior depends on how work reaches the function. Direct invocation, asynchronous invocation, and event-source mappings have different failure and capacity characteristics.

### Event-source capacity comparison

| Integration | Capacity planning concern | Main protection mechanism |
|---|---|---|
| API Gateway | Request rate, Lambda concurrency, and response latency | Reserved concurrency, throttling, and upstream rate limits |
| Application Load Balancer | Request distribution and target capacity | Concurrency planning and load-balancer health controls |
| Amazon SQS | Queue backlog, batch size, and consumer scaling | Mapping concurrency limits and queue-based backpressure |
| Amazon Kinesis Data Streams | Shard throughput, parallelization, and checkpoint progress | Source-specific scaling and iterator-age monitoring |
| DynamoDB Streams | Stream processing rate and record-processing delays | Event-source mapping configuration and downstream protection |
| Amazon S3 | Event bursts and asynchronous processing capacity | Queue buffering, controlled consumers, and idempotency |
| Amazon EventBridge | Event delivery rate, retries, and target capacity | Retry policies, failure destinations, and downstream controls |
| Direct asynchronous invocation | Pending event volume and asynchronous processing latency | Retry configuration, concurrency planning, and failure destinations |

Exact scaling behavior depends on the integration, mapping configuration, service quotas, and Region. Validate the relevant integration documentation before applying numeric assumptions.

### SQS consumer capacity

SQS decouples event production from processing. When incoming message volume exceeds consumer throughput, queue depth and message age increase.

A simplified backlog model is:

\[
B_{t+1} \approx B_t + A_t - P_t
\]

Where:

- \(B_t\) is the existing backlog.
- \(A_t\) is the number of new messages arriving during the interval.
- \(P_t\) is the number of messages successfully processed during the interval.

If arrivals consistently exceed processing capacity, the backlog grows even if Lambda is scaling.

To manage the backlog:

- Tune batch size and batching window based on latency and processing efficiency.
- Configure event-source mapping concurrency where appropriate.
- Ensure visibility timeout and retry behavior match processing characteristics.
- Use partial batch responses when supported to avoid retrying successful records unnecessarily.
- Protect databases and external APIs from excessive parallelism.
- Monitor the age of the oldest message, not just queue depth.

### Stream consumer capacity

For stream-based event sources, throughput depends on source-specific constraints, shard configuration, batch processing, and checkpoint behavior.

Monitor relevant metrics such as iterator age and event-source processing failures. A rising iterator age indicates that processing is falling behind the stream, but it does not identify the root cause by itself.

Increasing parallelism can improve throughput in some configurations, but it may also increase duplicate processing risk or overload downstream services.

## Protect Downstream Dependencies

Lambda can scale faster than a traditional application server pool. That makes downstream protection a primary capacity-planning responsibility.

Consider a function that creates one database connection per execution environment. A sudden increase in concurrent environments can exhaust PostgreSQL's connection limit even when Lambda itself is healthy.

### Estimate downstream connection demand

A rough upper-bound estimate is:

\[
D \approx C \times K
\]

Where:

- \(D\) is the potential number of simultaneous downstream connections.
- \(C\) is Lambda concurrency.
- \(K\) is the maximum connections maintained per execution environment.

For example, 150 concurrent executions maintaining up to two database connections each could create approximately 300 connections.

This is a planning estimate, not a guarantee. Actual connection behavior depends on pooling, connection reuse, application code, and execution-environment lifecycle.

### Recommended protections

- Set reserved concurrency or event-source mapping limits according to downstream capacity.
- Reuse clients and connections safely across invocations within an execution environment.
- Use appropriate database connection management, such as Amazon RDS Proxy where it fits the architecture.
- Apply bounded retries with backoff and jitter.
- Use request deadlines and dependency-specific timeouts.
- Monitor database connections, CPU, query latency, and connection acquisition failures.
- Avoid retry storms that amplify an existing outage.

### Concurrency as backpressure

Concurrency limits can act as a backpressure mechanism by restricting the rate at which Lambda workloads place demand on downstream systems.

However, limiting concurrency can move the bottleneck upstream. For SQS, the queue backlog may grow; for synchronous APIs, callers may receive throttling or errors; for stream sources, processing lag may increase.

Choose the behavior intentionally and define how the system should respond when capacity is exhausted.

## Forecast Peak Capacity

Capacity planning should use workload measurements rather than average traffic alone.

### Required inputs

Collect:

- Normal and peak invocation rates.
- Burst size and burst duration.
- Average and tail execution duration.
- Error and retry rates.
- Batch sizes and processing times.
- Downstream request and connection limits.
- Queue arrival and drain rates.
- Latency objectives and acceptable backlog age.
- Expected growth and deployment-related traffic changes.

### Estimate concurrency

For a synchronous request workload:

\[
C_{\text{estimated}} = \lambda_{\text{peak}} \times W_{\text{representative}}
\]

Use representative duration for initial estimates, then validate against real concurrency and latency distributions during load testing.

For a more conservative capacity plan, evaluate higher-percentile durations and realistic burst scenarios rather than multiplying peak arrival rate by the average duration alone.

### Example planning worksheet

Assume the following hypothetical workload:

| Input | Value |
|---|---:|
| Peak arrival rate | 250 invocations/second |
| Representative duration | 0.4 seconds |
| Estimated average concurrency | 100 |
| Planned headroom | 50% |
| Initial planning target | 150 concurrent executions |

The 150-concurrency target is an initial engineering estimate, not a universal sizing rule. Validate it against account quotas, observed bursts, duration percentiles, downstream limits, and the chosen integration.

Headroom should reflect traffic variability and recovery objectives. Avoid adding an arbitrary percentage without considering the actual workload.

## Monitor Capacity and Scaling

Capacity planning requires ongoing monitoring because traffic patterns, application behavior, and dependencies change.

### Key metrics

| Metric | What it indicates | Example response |
|---|---|---|
| `ConcurrentExecutions` | Current concurrent execution demand | Compare with quotas and reserved capacity |
| `UnreservedConcurrentExecutions` | Shared concurrency usage | Identify contention between functions |
| `Throttles` | Invocations rejected because of concurrency limits | Inspect function and account capacity |
| `Duration` | Execution time distribution | Investigate latency and resource regressions |
| `Invocations` | Invocation volume | Identify unexpected traffic growth |
| `Errors` | Failed executions | Correlate with dependencies and deployment changes |
| `AsyncEventAge` | Age of pending asynchronous events | Investigate processing delays and failures |
| `AsyncEventsDropped` | Asynchronous events discarded under applicable conditions | Investigate retry exhaustion and event-age limits |
| `IteratorAge` | Delay in processing supported stream sources | Investigate throughput and checkpoint progress |
| SQS `ApproximateAgeOfOldestMessage` | Age of the oldest queued message | Investigate consumer throughput and poison messages |

Metric availability and dimensions vary by integration. Use the correct metric namespace and dimensions for the affected function, queue, stream, or account.

### Alerting principles

Create actionable alarms around:

- Sustained throttling.
- Error-rate increases.
- Duration approaching timeout.
- Queue age exceeding the workload's processing objective.
- Stream-processing lag.
- Unexpected invocation growth.
- Database connection exhaustion.
- Provisioned concurrency spillover or insufficient ready capacity when relevant.

Avoid relying only on absolute invocation counts. A large invocation count can be normal for one service and an incident for another.

Use workload-specific thresholds, evaluation windows, and notification routing.

## Capacity Testing

Load testing should validate both Lambda capacity and the entire request path.

### Recommended test scenarios

- Normal steady-state traffic.
- Expected peak traffic.
- Short bursts above normal peak.
- Long-running dependency calls.
- Downstream rate limiting and connection exhaustion.
- Retry amplification after transient failures.
- Deployment during representative traffic.
- Recovery after a temporary outage.
- Queue backlog accumulation and drain.
- Regional or dependency degradation where the architecture supports such testing.

### Testing procedure

1. Define throughput, latency, error-rate, and recovery objectives.
2. Confirm that the test environment has representative configuration and permissions.
3. Record baseline metrics and downstream capacity.
4. Increase traffic gradually while monitoring concurrency and latency.
5. Exercise failure scenarios with controlled fault injection.
6. Verify throttling and backpressure behavior.
7. Confirm that the system recovers without duplicate business effects or data loss.
8. Document tested limits and assumptions.

Use controlled environments and approved test windows. Avoid generating high-volume traffic against production dependencies without explicit authorization.

## Capacity Planning for Deployments

Deployment events can temporarily change concurrency and latency behavior.

Consider:

- New versions with different initialization costs.
- Alias traffic shifting between versions.
- Provisioned concurrency initialization and readiness.
- Temporary overlap between old and new execution environments.
- Database schema changes and connection behavior.
- Changes to batch size, retry configuration, or event-source mapping concurrency.

Use published versions and aliases for controlled rollout where appropriate. Verify the target version and alias configuration before shifting traffic, and monitor error rate, duration, throttles, and downstream health during deployment.

A code rollback does not automatically reverse database migrations, queue side effects, or external operations. Deployment capacity planning must include compatibility and recovery strategy.

## Operational Capacity Review

Perform a periodic review for critical Lambda workloads.

### Capacity review checklist

- [ ] Confirm account concurrency quotas for every deployed Region.
- [ ] Review reserved concurrency allocations and the remaining shared capacity.
- [ ] Validate provisioned concurrency requirements and utilization.
- [ ] Recalculate expected concurrency using current traffic and duration measurements.
- [ ] Check event-source scaling limits, queue backlog, and stream-processing lag.
- [ ] Verify that downstream databases and APIs can tolerate peak parallelism.
- [ ] Review throttling, duration, errors, and retry-related metrics.
- [ ] Validate alarms against realistic incident scenarios.
- [ ] Confirm quota-increase procedures and operational ownership.
- [ ] Test recovery and backlog-drain behavior.
- [ ] Review cost impact before increasing provisioned capacity or sustained concurrency.
- [ ] Update assumptions after significant traffic, code, or architecture changes.

## Common Capacity Planning Mistakes

| Mistake | Consequence | Prevention |
|---|---|---|
| Sizing from average traffic only | Peak demand exceeds available capacity | Model bursts and tail latency |
| Treating automatic scaling as unlimited | Throttling or downstream failures occur | Validate quotas and integration-specific limits |
| Reserving concurrency indiscriminately | Shared account capacity becomes constrained | Reserve only for clear isolation or protection requirements |
| Increasing concurrency to solve all backlogs | Downstream systems may become overloaded | Identify the true throughput bottleneck |
| Ignoring retries | Retry traffic amplifies the original workload | Model failure rates and retry behavior |
| Ignoring database connection limits | Connection exhaustion causes cascading failures | Bound concurrency and manage connections |
| Monitoring only Lambda errors | Backlogs and dependency failures remain undetected | Monitor source-specific and downstream metrics |
| Treating provisioned concurrency as a complete latency solution | Network and application delays remain | Measure end-to-end latency |
| Using stale quota assumptions | Capacity estimates become inaccurate | Revalidate quotas and regional configuration |
| Scaling without cost analysis | Unexpected spend increases | Compare capacity strategies and monitor usage |

## Key Takeaways

- Estimate Lambda concurrency from arrival rate and execution duration, then validate against peak traffic, tail latency, quotas, and downstream limits.
- Treat account quotas, reserved concurrency, provisioned concurrency, and event-source scaling as distinct capacity controls.
- Protect databases and external services with bounded concurrency, connection management, timeouts, and controlled retry behavior.
- Monitor throttling, duration, queue age, stream lag, and dependency health to detect capacity problems before they become outages.
- Validate capacity through realistic load and failure testing, and revisit assumptions whenever traffic or architecture changes.