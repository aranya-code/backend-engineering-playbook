# 10- Rapid Fire Questions

## Overview

Rapid-fire Elastic Beanstalk questions test whether an engineer can recall core concepts quickly and distinguish closely related AWS features.

The expected answers should be short, precise, and technically accurate. For interview preparation, avoid memorizing isolated definitions. Focus on the architectural reason behind each answer.

## Core Concepts

### What is Amazon Elastic Beanstalk?

Elastic Beanstalk is an AWS managed application platform that simplifies deploying, running, and scaling applications without requiring the team to manage every underlying infrastructure component directly.

### What does Elastic Beanstalk manage?

Depending on the environment configuration, Elastic Beanstalk can provision and manage resources such as:

- EC2 instances
- Auto Scaling
- Elastic Load Balancing
- Security groups
- CloudWatch integration
- Platform/runtime configuration

### Does Elastic Beanstalk eliminate EC2?

No. Elastic Beanstalk commonly runs applications on EC2 instances. It primarily automates the provisioning and management of the application environment.

### Is Elastic Beanstalk a serverless service?

No. It is a managed application platform built around infrastructure such as EC2 and load balancing.

### What is an Elastic Beanstalk application?

An application is a logical container for related environments, application versions, and configuration.

### What is an Elastic Beanstalk environment?

An environment is the running infrastructure and configuration used to host a specific application version.

### Can one application have multiple environments?

Yes.

Typical environments include:

```text
my-api
├── development
├── staging
└── production
```

### Why use multiple environments?

They provide isolation for different deployment stages, configuration, scaling requirements, and operational risk.

### What is an application version?

An application version is a specific deployable source bundle associated with an Elastic Beanstalk application.

### Can multiple environments use the same application version?

Yes. The same immutable application artifact can be deployed to different environments.

### What is a platform in Elastic Beanstalk?

A platform defines the operating system, runtime, web server/application server, and related components used to run the application.

### What is a platform branch?

A platform branch represents a particular runtime/platform generation within an Elastic Beanstalk platform family.

## Environment Types

### What is a web server environment?

A web server environment is designed to receive and process web requests, typically through a load balancer and application instances.

### What is a worker environment?

A worker environment is designed for background processing of messages delivered through an associated queue.

### When would you use a worker environment?

Use it when application work can be processed asynchronously instead of being completed synchronously during an HTTP request.

### What is the advantage of a worker architecture?

It separates request handling from background processing and can absorb workload through queue-based buffering.

## Deployment

### What is the default deployment behavior in Elastic Beanstalk?

The deployment behavior depends on the selected deployment policy. Common policies include rolling, rolling with additional batch, immutable, and traffic-splitting approaches.

### What is a rolling deployment?

Instances are updated in batches while the environment remains operational.

### What is the main risk of rolling deployment?

Different application versions can temporarily coexist, so the application and database schema must remain backward compatible.

### What is an immutable deployment?

Elastic Beanstalk launches a new set of instances with the new version before replacing the old instances.

### Why is immutable deployment safer?

The existing instances remain available while the new version is being provisioned and validated.

### What is the cost of immutable deployment?

It temporarily requires additional compute capacity.

### What is blue/green deployment?

Blue/green deployment uses two separate environments, with traffic moved from the old environment to the new one after validation.

### Why use blue/green deployment?

It provides strong environment isolation and makes rollback relatively straightforward by moving traffic back to the previous environment.

### What is the main disadvantage of blue/green deployment?

It requires additional environment capacity and operational management.

### Does blue/green deployment automatically solve database rollback?

No.

Database schema compatibility must be designed independently.

### What is traffic splitting?

Traffic splitting gradually directs a percentage of production traffic to a new application version while the existing version continues serving traffic.

### When is traffic splitting useful?

It is useful for controlled canary-style releases where production behavior needs to be observed before sending all traffic to the new version.

### What is an immutable infrastructure principle?

Instead of modifying running servers repeatedly, deploy a new known-good version and replace the old infrastructure.

## Scaling

### How does Elastic Beanstalk scale applications?

Elastic Beanstalk can use EC2 Auto Scaling to increase or decrease application capacity based on configured scaling policies.

### What is horizontal scaling?

Adding more application instances.

```text
2 instances
   |
   v
5 instances
   |
   v
10 instances
```

### What is vertical scaling?

Increasing the capacity of an individual instance.

```text
Small EC2
   |
   v
Larger EC2
```

### Which scaling model is generally preferred for stateless web applications?

Horizontal scaling because it improves capacity and provides instance-level redundancy.

### What is the minimum instance count?

It is the minimum number of instances that Auto Scaling should maintain.

### What is the maximum instance count?

It is the upper capacity limit Auto Scaling can reach.

### Why is setting maximum capacity too low dangerous?

Traffic spikes may exhaust application capacity, causing increased latency and errors.

### Why is setting maximum capacity excessively high dangerous?

It can create unexpected infrastructure cost and overload downstream dependencies such as PostgreSQL.

### Does adding more EC2 instances guarantee better performance?

No.

The bottleneck may be:

- Database
- Redis
- External API
- Network
- CPU
- Memory
- Disk I/O
- Application locks

### What is a scaling bottleneck?

A resource whose capacity limits the ability of the entire system to scale.

### Why can Auto Scaling overload PostgreSQL?

Every additional application instance may create additional worker processes and database connections.

## Load Balancing

### What is the role of the load balancer?

It distributes incoming traffic across healthy application instances.

### Why is load balancing important?

It enables:

- Horizontal scaling
- Instance-level fault tolerance
- Health-based traffic routing
- Controlled deployments

### What happens when an instance becomes unhealthy?

The load balancer can stop routing traffic to it, while Auto Scaling can replace it depending on the environment configuration and failure conditions.

### Should an application instance be publicly accessible?

In a typical production architecture, application instances can be placed in private subnets while the load balancer provides the public entry point.

## High Availability

### Does two-instance deployment guarantee high availability?

No.

The instances should be distributed across multiple Availability Zones and critical dependencies must also have appropriate availability designs.

### What is an Availability Zone?

An isolated location within an AWS Region designed to provide fault isolation from other Availability Zones.

### Why deploy across multiple Availability Zones?

To reduce the impact of an Availability Zone failure.

### Is multi-AZ application deployment enough for high availability?

No.

The database, cache, queues, networking, DNS, and external dependencies must also be considered.

### What is a single point of failure?

A component whose failure can cause the entire service or critical functionality to become unavailable.

### Give an example of a single point of failure.

A production API with multiple EC2 instances but a single non-redundant database dependency can still have a database-level single point of failure.

## Networking

### Can Elastic Beanstalk environments run inside a VPC?

Yes.

### Why place Elastic Beanstalk resources in a VPC?

To control:

- Network isolation
- Subnets
- Security groups
- Routing
- Internet access
- Private service communication

### What is a common production network architecture?

```text
Internet
   |
   v
Public Load Balancer
   |
   v
Private Application Instances
   |
   v
Private Database
```

### Should a production database be publicly accessible?

Generally no. Prefer private networking and tightly scoped security-group rules.

### What is a security group?

A stateful virtual firewall controlling inbound and outbound network traffic associated with AWS resources.

### Should the database security group allow traffic from the entire VPC CIDR?

Not necessarily.

Prefer allowing traffic from the specific application security group when possible.

### What is the difference between a public and private subnet?

A public subnet has a route to an internet gateway. A private subnet does not directly expose resources through an internet gateway.

## Security

### How should an Elastic Beanstalk application access AWS services?

Prefer IAM roles attached to the workload rather than hardcoded AWS access keys.

### Why are IAM roles preferred over access keys?

Roles provide temporary credentials and avoid embedding long-lived credentials in application code or configuration.

### Where should application secrets be stored?

Use an appropriate managed secret/configuration mechanism such as AWS Secrets Manager or Systems Manager Parameter Store, depending on the requirement.

### Should passwords be committed to Git?

No.

### Should secrets be printed in application logs?

No.

### What is least privilege?

Granting only the permissions required to perform a specific task.

### Should an Elastic Beanstalk application have AdministratorAccess?

Generally no.

The application should have only the AWS permissions it actually requires.

### What is the security risk of exposing the EC2 instances directly?

It increases the attack surface and bypasses the intended load-balancer/application-tier security boundary.

## Application Architecture

### Why should Elastic Beanstalk applications generally be stateless?

Instances can be added, removed, or replaced at any time.

Any request should therefore be capable of being processed by any healthy instance.

### Where should uploaded files be stored?

Typically Amazon S3 rather than the local instance filesystem.

### Why is local filesystem storage risky?

An instance can be terminated or replaced, causing locally stored data to disappear.

### Where should shared sessions be stored?

Depending on the architecture, sessions can be stored in a shared database or Redis rather than local instance memory.

### Can local temporary files be used?

Yes, when the data is explicitly disposable and does not need to survive instance replacement.

### Why are sticky sessions usually undesirable?

They create instance affinity and can reduce the flexibility and resilience of horizontal scaling.

## Django and FastAPI

### Can Django run on Elastic Beanstalk?

Yes.

### Can FastAPI run on Elastic Beanstalk?

Yes, provided the selected platform and application configuration correctly support the application server and runtime.

### What is important when deploying Django?

Validate:

- WSGI configuration
- Static files
- Database configuration
- Secret management
- Allowed hosts
- Debug settings
- Migration strategy
- Application logging

### What is important when deploying FastAPI?

Validate:

- ASGI server configuration
- Worker configuration
- Environment variables
- Health checks
- Timeouts
- Database connections
- Logging

### Should Django migrations automatically run on every instance startup?

This requires careful design.

Running migrations concurrently from multiple instances can create race conditions or operational problems.

Prefer controlled migration execution through CI/CD or a dedicated deployment step.

## Database

### Should PostgreSQL run inside Elastic Beanstalk EC2 instances?

Generally no.

Use an appropriate managed database service such as Amazon RDS or Amazon Aurora when that architecture fits the workload.

### Why separate application and database infrastructure?

It provides independent lifecycle management, scaling, backup, availability, and operational controls.

### What happens if application instances scale from 5 to 50?

Database connection demand can increase dramatically.

### How can database connection pressure be reduced?

Use:

- Appropriate worker counts
- Connection pooling
- Query optimization
- Caching
- Controlled scaling
- Database capacity planning

### Can Auto Scaling fix a slow database?

No.

It can increase application capacity while making the database bottleneck worse.

## Redis and Caching

### Why use Redis with Elastic Beanstalk?

Redis can provide:

- Shared caching
- Session storage
- Rate limiting
- Temporary state
- Distributed coordination

### What should happen when Redis is used only as a cache and fails?

The application may fall back to the database, assuming the architecture supports cache failure.

### What is cache invalidation?

The process of ensuring stale cached data is removed or refreshed when the underlying data changes.

### What is a cache stampede?

A large number of requests simultaneously miss the cache and query the underlying dependency.

### How can cache stampedes be mitigated?

Possible techniques include:

- TTL jitter
- Request coalescing
- Cache warming
- Locking
- Stale-while-revalidate patterns

## CI/CD

### What should a production Elastic Beanstalk pipeline contain?

A typical pipeline includes:

```text
Commit
  |
  v
Build
  |
  v
Unit Tests
  |
  v
Package
  |
  v
Deploy Staging
  |
  v
Integration / Smoke Tests
  |
  v
Production
  |
  v
Monitor
```

### Why should the same artifact be promoted across environments?

It reduces the risk that staging and production run different builds.

### Should production deployments be performed manually?

Manual deployment can work for small systems, but mature production environments generally benefit from automated, auditable CI/CD.

### What should trigger rollback?

Examples include:

- Elevated 5xx rate
- Increased latency
- Failed health checks
- Application startup failures
- Business metric degradation

### Does a successful deployment mean the release is successful?

No.

Infrastructure deployment success only confirms that the deployment operation completed. Application behavior still needs validation.

## Monitoring

### What should be monitored?

At minimum:

- Request rate
- Error rate
- Latency
- Instance health
- CPU
- Memory where available
- Deployment health
- Database health
- Cache health
- Queue depth

### What are the three primary signals for an HTTP API?

A useful starting point is:

- Traffic
- Errors
- Latency

Resource saturation should also be monitored.

### Why is CPU alone insufficient?

An API can be CPU-light while experiencing:

- Database saturation
- Memory pressure
- Network bottlenecks
- External API latency
- Connection exhaustion

### What is a health check?

A mechanism used to determine whether an instance is capable of serving traffic.

### Should health checks be extremely deep?

Not always.

Overly strict health checks can cause healthy instances to be removed when a non-critical dependency has a temporary problem.

## Logging

### Where should application logs go?

Prefer centralized logging rather than relying exclusively on local instance files.

### Why?

Instances are ephemeral and may be replaced.

Centralized logs improve:

- Troubleshooting
- Searchability
- Retention
- Incident investigation

### What should never be logged?

Avoid logging:

- Passwords
- Access tokens
- API keys
- Session secrets
- Sensitive personal data

## Platform Updates

### What is a platform update?

An update to the underlying Elastic Beanstalk platform/runtime components.

### Why should platform updates be planned?

They can affect:

- Operating system behavior
- Runtime versions
- Native libraries
- Web servers
- Application compatibility

### Should platform updates be tested in production first?

No.

Validate them in a lower environment before production rollout.

### Why should runtime upgrades be separated from feature releases?

Separating changes makes failures easier to attribute and reduces the size of each production change.

## Troubleshooting

### An Elastic Beanstalk deployment failed. What do you check first?

Check:

1. Deployment events.
2. Application logs.
3. Instance health.
4. Load-balancer health.
5. Configuration changes.
6. Platform/runtime compatibility.
7. Application startup errors.

### The environment is healthy but the API returns 500 errors. What does that indicate?

Infrastructure health does not necessarily mean application correctness.

Investigate:

- Application logs
- Exceptions
- Database connectivity
- Environment variables
- Dependency failures
- Recent releases

### The application returns 502 errors. What would you investigate?

Look at the load balancer-to-application path:

```text
Client
  |
  v
Load Balancer
  |
  v
Application Instance
  |
  v
Application Server
```

Check:

- Instance health
- Application process
- Port configuration
- Application server
- Timeouts
- Security groups
- Startup failures

### Instances repeatedly become unhealthy. What could cause this?

Potential causes include:

- Application crashes
- Incorrect health-check path
- Insufficient memory
- CPU saturation
- Startup failures
- Dependency failures
- Incorrect ports
- Deployment problems

### The application works locally but fails on Elastic Beanstalk. What do you check?

Compare:

- Runtime version
- Environment variables
- Dependencies
- OS packages
- Startup command
- Working directory
- Network access
- IAM permissions
- Database configuration

## Reliability

### What is graceful degradation?

Allowing non-critical functionality to fail while preserving critical functionality.

### What is a timeout?

A limit on how long an operation is allowed to wait for completion.

### Why are timeouts important?

Without bounded timeouts, slow dependencies can consume workers and eventually exhaust application capacity.

### Why can retries be dangerous?

Retries can multiply traffic against an already failing dependency and create a retry storm.

### What should retries normally include?

Where appropriate:

- Maximum attempts
- Exponential backoff
- Jitter
- Idempotency
- Time limits

## Disaster Recovery

### What is RTO?

Recovery Time Objective: the maximum acceptable time to restore service after a failure.

### What is RPO?

Recovery Point Objective: the maximum acceptable amount of data loss measured in time.

### Does Elastic Beanstalk automatically provide complete disaster recovery?

No.

Disaster recovery must include application artifacts, configuration, databases, object storage, secrets, networking, and recovery procedures.

### Why test disaster recovery?

A backup is not equivalent to a verified recovery procedure.

### Should recovery procedures be documented?

Yes.

Operational recovery should not depend entirely on the memory of one engineer.

## Cost

### What are major Elastic Beanstalk-related cost drivers?

Depending on architecture:

- EC2 instances
- Load balancer
- Database
- Cache
- NAT Gateway
- Data transfer
- Logging
- Storage
- Additional environments

### Is Elastic Beanstalk itself the primary cost?

Elastic Beanstalk does not eliminate the cost of the AWS resources it provisions. The underlying infrastructure and related services remain important cost drivers.

### How can application infrastructure cost be reduced?

Evaluate:

- Instance sizing
- Minimum capacity
- Scaling policies
- Environment count
- Idle staging resources
- Log retention
- Network architecture
- Database sizing

### Should minimum capacity always be one instance to save money?

Not for production workloads requiring high availability.

## Architecture Comparison

### Elastic Beanstalk vs EC2?

| Elastic Beanstalk | EC2 |
|---|---|
| Higher-level application platform | Lower-level compute |
| More automation | More infrastructure control |
| Easier standard deployments | More manual management |
| Less infrastructure customization | Greater customization |

### Elastic Beanstalk vs ECS?

| Elastic Beanstalk | ECS |
|---|---|
| Application-platform abstraction | Container orchestration |
| Simpler traditional application deployment | Container-native |
| Less orchestration complexity | Greater container control |
| Good for conventional web applications | Good for containerized workloads |

### Elastic Beanstalk vs EKS?

| Elastic Beanstalk | EKS |
|---|---|
| Simpler operational model | Kubernetes-based |
| Less platform complexity | More control and complexity |
| Limited orchestration model | Kubernetes ecosystem |
| Lower operational burden for conventional applications | Better for Kubernetes-standardized organizations |

### Elastic Beanstalk vs Lambda?

| Elastic Beanstalk | Lambda |
|---|---|
| Long-running application instances | Event/function execution model |
| EC2-backed | Serverless compute |
| Suitable for conventional web applications | Suitable for event-driven workloads |
| Instance-level scaling | Invocation-based scaling |

## Interview Traps

### Is Elastic Beanstalk serverless?

**No.** It is a managed application platform that commonly uses EC2.

### Does Elastic Beanstalk manage your database schema?

**No.** Database schema and migration strategy remain application responsibilities.

### Does Auto Scaling automatically make the entire system highly available?

**No.** It only addresses capacity and instance-level availability. Dependencies must also be designed for resilience.

### Does a successful health check prove the application is fully functional?

**No.** Health checks only validate the conditions they are designed to test.

### Does blue/green deployment guarantee zero downtime?

**No.** It can reduce deployment-related downtime, but application errors, dependency failures, database migrations, DNS behavior, and configuration problems can still cause outages.

### Does immutable deployment mean there is no additional cost?

**No.** New instances temporarily coexist with the old instances.

### Can Elastic Beanstalk automatically fix every application failure?

**No.** It can replace unhealthy infrastructure, but it cannot correct arbitrary application bugs.

### Should all application state be stored on the EC2 instance?

**No.** Shared and persistent state should generally be externalized.

### Is rolling deployment always safer than immutable deployment?

**No.** The appropriate strategy depends on application compatibility, risk, capacity, and rollback requirements.

### Is the load balancer enough to provide security?

**No.** Security requires network controls, IAM, application security, secret management, encryption, and appropriate authorization.

## Rapid-Fire Scenario Questions

### Traffic suddenly increases 10x. What do you check?

Auto Scaling capacity, instance performance, load-balancer metrics, database saturation, Redis, external dependencies, and application bottlenecks.

### Database CPU reaches 100% after adding instances. Why?

The application tier scaled faster than the database capacity.

### One Availability Zone fails. What should happen?

Traffic should continue through healthy capacity in other Availability Zones, assuming the architecture and dependencies support multi-AZ operation.

### A deployment succeeds but error rate increases. What do you do?

Stop further rollout, investigate application and dependency metrics, and roll back or shift traffic to the known-good version when appropriate.

### A new release requires a breaking database schema change. Can you use rolling deployment?

Not safely unless the schema and application versions are made compatible.

### Redis goes down. What should happen?

If Redis is only a cache, the application may fall back to the database. If Redis stores critical state, the recovery strategy must be substantially stronger.

### An instance stores uploaded files locally. What is wrong?

Instance-local storage is ephemeral and unsuitable as the authoritative location for persistent user data.

### A production environment has only one EC2 instance. What is the concern?

The instance is a single point of failure and cannot provide meaningful instance-level high availability.

### The application is slow but CPU is only 20%. What could be wrong?

Investigate database latency, external API latency, network behavior, locks, connection pools, I/O, and application-level contention.

### Application instances continuously restart. What do you investigate?

Startup logs, memory usage, health checks, application crashes, dependency connectivity, configuration, and platform compatibility.

### The team wants Kubernetes only because it is "more scalable." What is your response?

Scalability is a system property. First identify actual workload, orchestration, operational, and organizational requirements before selecting Kubernetes.

### The company requires five-minute recovery. What should you investigate?

RTO feasibility, infrastructure recreation time, database recovery time, DNS/traffic failover, automation, backups, and operational runbooks.

### The company allows only one minute of data loss. What does that imply?

The RPO requirement demands an appropriate replication, backup, or recovery architecture capable of meeting that target.

### Production and staging have different application artifacts. What is the concern?

The environments are not testing the same release candidate, reducing deployment confidence.

### An application uses environment variables for configuration. Is that inherently insecure?

No. Environment variables can be appropriate for configuration, but sensitive values require controlled secret management and must not leak into logs or diagnostics.

## Key Takeaways

- Elastic Beanstalk is a managed application platform, not a serverless compute service.
- An Elastic Beanstalk application can contain multiple environments.
- An environment represents a running deployment and its associated infrastructure/configuration.
- Elastic Beanstalk commonly uses EC2, Auto Scaling, and load balancing underneath.
- Web server environments handle HTTP workloads; worker environments support asynchronous processing patterns.
- Stateless application design is critical for reliable horizontal scaling.
- Persistent files should generally be stored in durable storage such as S3 rather than instance-local disks.
- Application scaling does not automatically scale databases or other dependencies.
- Multi-AZ deployment improves availability but does not guarantee end-to-end high availability.
- Load balancers distribute traffic and can remove unhealthy instances from service.
- IAM roles are preferred over hardcoded long-lived AWS credentials.
- Least privilege should apply to application, deployment, and administrative identities.
- Secrets should not be committed to source control or exposed through logs.
- Rolling deployments can temporarily run multiple application versions.
- Immutable deployments provide stronger isolation but require additional temporary capacity.
- Blue/green deployments provide environment-level isolation and facilitate traffic rollback.
- Deployment strategy does not eliminate database migration compatibility requirements.
- Database migrations should be designed for mixed-version deployments when rolling or gradual releases are used.
- Auto Scaling should be evaluated together with database connection capacity and downstream bottlenecks.
- CPU is useful but insufficient as the only application scaling or health signal.
- Monitor traffic, errors, latency, saturation, infrastructure health, and critical dependencies.
- Timeouts and bounded retries prevent slow dependencies from exhausting application capacity.
- Retries should use appropriate backoff and jitter and must consider idempotency.
- Redis failures should be handled according to whether Redis stores optional cache data or critical application state.
- CI/CD should promote tested artifacts through environments rather than rebuilding different artifacts for production.
- A successful infrastructure deployment does not prove that the application release is healthy.
- Platform and runtime upgrades should be tested separately from application feature changes when practical.
- RTO and RPO determine disaster recovery architecture; Elastic Beanstalk alone does not define the recovery strategy.
- Cost optimization should consider EC2, load balancing, databases, caching, networking, logging, and environment count.
- Elastic Beanstalk versus ECS, EKS, EC2, or Lambda should be decided from workload and operational requirements rather than perceived service maturity.
- The strongest interview answers explain not only what Elastic Beanstalk does, but also what it does not solve.