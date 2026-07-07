# Scalability Patterns — Horizontal Scaling and Auto Scaling

## Vertical vs. Horizontal Scaling

- **Vertical scaling** — a bigger instance (more CPU/RAM). Simple, but has a hard ceiling (the largest instance type available) and usually requires downtime to resize
- **Horizontal scaling** — more instances running in parallel behind a load balancer. No hard ceiling, and can scale down as well as up, but requires the application to be stateless (or externalize state) to work correctly

## Why Horizontal Scaling Requires Statelessness

If a user's session data lives only in the memory of the specific instance that first served them, routing their next request to a *different* instance breaks the session. Horizontal scaling architectures externalize state — session data in ElastiCache/DynamoDB, files in S3, not on local instance disk — so any instance can serve any request.

## AWS Auto Scaling

Automatically adjusts the number of running instances (EC2 Auto Scaling Groups, ECS Service Auto Scaling, or Lambda's inherent concurrency scaling) based on defined metrics.

| Scaling Type | Trigger |
|---|---|
| Target tracking | Maintain a metric (e.g., CPU) at a target value (e.g., 60%) |
| Step scaling | Add/remove capacity in defined steps based on alarm thresholds |
| Scheduled scaling | Scale based on a known schedule (e.g., predictable daily traffic pattern) |
| Predictive scaling | Uses historical data/ML to scale ahead of anticipated demand |

## Scaling Is Not Instant

Launching a new EC2 instance, waiting for it to pass health checks, and having it join the load balancer's rotation takes real time (often minutes) — during a sudden traffic spike, auto scaling reacts *after* the spike starts, not before it. This is exactly why predictive and scheduled scaling exist for known traffic patterns, and why some architectures keep a buffer of extra capacity for genuinely unpredictable spikes.

## Serverless Sidesteps Much of This

Lambda's scaling model (near-instant concurrent execution scaling, within account concurrency limits) avoids the "wait for a new instance to boot" problem entirely — a major reason serverless architectures are attractive for spiky, unpredictable workloads specifically.

## Senior-Level Considerations

- Scaling policies need a cooldown period — reacting too aggressively to short-lived metric spikes causes "flapping" (rapid scale up/down cycles) that wastes resources and can destabilize a system more than the original spike would have
- Auto scaling handles compute capacity; it does nothing for a downstream bottleneck (a database that can't handle the new connection count, for instance) — scaling the compute layer without checking the data layer's capacity is a common, painful production surprise
- Target tracking on the *right* metric matters — CPU is a common default, but for I/O-bound or memory-bound workloads, scaling on CPU alone can leave the system either over- or under-provisioned relative to what's actually constraining it
