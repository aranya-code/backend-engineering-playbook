# Serverless Architecture Patterns and Trade-offs

## What "Serverless" Actually Means Architecturally

Not "no servers" — servers still run your code — but no server *management*: no patching, no capacity planning, no idle-capacity cost, with the provider (AWS) handling scaling automatically. Lambda, API Gateway, DynamoDB (on-demand mode), and Step Functions are the core building blocks.

## The Canonical Serverless API Pattern

```text
Client → API Gateway → Lambda → DynamoDB
```

No EC2 instances, no load balancer to configure, no idle capacity cost when there's no traffic.

## Genuine Benefits

- **Pay-per-use** — no charge for idle time, which can be dramatically cheaper for spiky or low/moderate-traffic workloads
- **Near-instant scaling** — Lambda scales concurrent executions automatically, sidestepping the "wait for a new instance to boot" problem covered in the Auto Scaling file
- **Reduced operational burden** — no OS patching, no server fleet to maintain

## Real Trade-offs

- **Cold starts** — a Lambda function that hasn't run recently incurs extra latency on its first invocation while its execution environment initializes; this matters for latency-sensitive synchronous APIs, less so for async/background processing
- **Execution time limits** — Lambda has a maximum execution duration (15 minutes); long-running processes need a different tool (ECS/EKS, Step Functions for long orchestrations)
- **Vendor lock-in is real** — code written against Lambda's specific event/context model, and architectures built deeply around Step Functions or EventBridge, are more work to port to another provider than a containerized application would be
- **Local development and testing friction** — simulating the full serverless event ecosystem locally is harder than running a containerized app locally, though tooling (SAM, LocalStack) has narrowed this gap significantly
- **Connection-based backends need extra care** — as covered in Database Scaling, Lambda's rapid concurrent scaling can exhaust traditional database connection limits without a pooler (RDS Proxy) in front

## When Serverless Is a Strong Fit

Spiky or unpredictable traffic, event-driven processing (react to an S3 upload, a queue message, a schedule), and workloads where the team wants to minimize infrastructure operations entirely.

## When It's a Weaker Fit

Very high, sustained, predictable throughput (where the always-on cost of provisioned compute can actually be cheaper than per-invocation pricing at scale), long-running processes, and workloads with hard, consistent low-latency requirements where cold starts are unacceptable (though provisioned concurrency can mitigate this at added cost).

## Senior-Level Considerations

- "Serverless" is a spectrum, not binary — a genuinely common and pragmatic architecture mixes Lambda for event-driven glue code with ECS/Fargate for the core, sustained-traffic services, choosing per-component rather than dogmatically going all-in on one style
- Cost modeling matters here specifically because the pricing model inverts the usual assumption — serverless can be either much cheaper or much more expensive than provisioned compute depending on actual traffic shape, and that needs real usage-pattern math, not intuition
