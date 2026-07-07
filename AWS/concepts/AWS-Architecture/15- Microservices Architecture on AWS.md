# Microservices Architecture on AWS

## What Microservices Actually Buy You

Independent deployability (ship one service without redeploying everything), independent scalability (scale the busy service without over-provisioning the quiet ones), and team autonomy (different teams own different services with their own release cadence) — none of which come for free.

## What Microservices Cost You

Distributed systems complexity that a monolith simply doesn't have: network calls where function calls used to be (with all the failure modes covered elsewhere in this folder — retries, circuit breakers, timeouts), data consistency across service boundaries (no more single-database transactions spanning everything), and significantly more operational surface area (more things to deploy, monitor, and secure independently).

## Common AWS Compute Choices for Microservices

| Option | Fit |
|---|---|
| ECS (Fargate) | Container-based services without managing servers; a common default for teams already comfortable with Docker |
| EKS | Kubernetes on AWS — appropriate when you need Kubernetes's ecosystem/portability specifically, at real added operational complexity vs. ECS |
| Lambda | Event-driven or low-traffic services where paying only per-invocation matters; less natural fit for long-running or highly stateful services |

## Service Discovery and Communication

Services need to find each other (AWS Cloud Map, or a service mesh like App Mesh) and communicate — synchronously via API Gateway/ALB-fronted HTTP calls, or asynchronously via the SQS/SNS/EventBridge patterns covered earlier in this folder. A senior-level architecture deliberately chooses sync vs. async per interaction, rather than defaulting to synchronous HTTP for everything simply because it's the most familiar.

## The API Gateway / BFF Pattern

Rather than clients calling many microservices directly, a Backend-for-Frontend (or a shared API Gateway) sits in front, composing multiple backend calls into the shape a specific client (web, mobile) actually needs. This avoids exposing internal service topology to clients directly, and lets internal services be restructured without breaking client contracts.

## Data Ownership Per Service

A core microservices principle: each service owns its own data store, and no other service reaches directly into another service's database. Cross-service data needs are satisfied via API calls or events, not shared database access — violating this ("just query the other team's database directly, it's faster") is one of the most common ways microservices architectures quietly turn into a distributed monolith with all the coupling of a monolith and none of the deployment benefits.

## Senior-Level Considerations

- Microservices are a genuine trade-off, not an unconditional upgrade from a monolith — a small team building a small product often ships faster and more reliably with a well-structured monolith, and splits into services later when a specific, real scaling or team-boundary pain point justifies the added complexity
- "Distributed monolith" (services that are deployed separately but so tightly coupled they must be deployed together to work) is worse than either a real monolith or real microservices — it has the operational cost of the former and none of the benefits of the latter
- Observability (distributed tracing, correlation IDs, centralized logging) is not optional once you have more than a couple of services — without it, understanding a single user request that spans five services during an incident becomes close to impossible
