# 07- Scenario Based Questions

## Overview

Scenario-based questions test whether you can apply Elastic Beanstalk concepts to real production problems rather than simply recall service definitions.

A strong answer should identify:

- The symptom or business requirement.
- The likely technical cause.
- The relevant Elastic Beanstalk component.
- The investigation path.
- The safest remediation.
- Production and reliability implications.
- Preventive controls.

The scenarios below focus on deployment, scaling, health, networking, security, configuration, CI/CD, failures, cost, and operational decision-making.

## Deployment Scenarios

### Your Django application works locally but fails immediately after deployment to Elastic Beanstalk. How would you troubleshoot it?

Start by separating application-level failures from platform-level failures.

A practical investigation sequence is:

1. Check environment health and recent events.
2. Inspect application logs.
3. Verify the deployed artifact contains the expected files.
4. Verify the platform/runtime version.
5. Check environment variables and secrets.
6. Verify the application entry point.
7. Verify dependency installation.
8. Check database and external-service connectivity.
9. Review the deployment command and process configuration.

For a Python application, common causes include:

- Incorrect WSGI/ASGI configuration.
- Missing dependencies in `requirements.txt`.
- Wrong Python/platform version.
- Missing environment variables.
- Incorrect application module path.
- Database connectivity failure.
- Incorrect static-file configuration.
- Application binding to the wrong interface or port.

The important production principle is to **start from observable evidence rather than changing configuration randomly**.

### A deployment succeeds, but the application becomes unhealthy. What would you investigate?

A successful deployment only means that Elastic Beanstalk completed the deployment workflow. It does not guarantee that the application is serving requests correctly.

Check:

- Elastic Beanstalk events.
- Health status.
- Application logs.
- Web server logs.
- HTTP status codes.
- Health-check path.
- Application startup time.
- CPU and memory utilization.
- Database connectivity.
- Security groups and network routes.

A common failure pattern is:

```text
Deployment succeeds
       |
       v
Application starts
       |
       v
Health check
       |
       v
HTTP 5xx / timeout
       |
       v
Environment becomes unhealthy
```

The health-check endpoint should be lightweight and should not depend unnecessarily on slow external systems.

### A new deployment causes 5xx errors immediately. What would you do?

First determine whether the issue is isolated to the new application version.

Check:

- Deployment events.
- Application logs.
- HTTP error rates.
- Environment health.
- Recent configuration changes.
- Dependency changes.
- Database migrations.
- Runtime/platform changes.

If the previous version is known to be healthy, rollback is often safer than attempting multiple live fixes.

```text
New version
    |
    v
5xx spike
    |
    +----> Investigate
    |
    v
Known-good version
    |
    v
Rollback
```

After stabilizing production, investigate the root cause in a lower environment.

### A database migration is required during deployment. How should you handle it?

Database migrations require backward-compatibility planning because application instances may not all switch versions simultaneously.

A safer deployment pattern is:

```text
Backward-compatible schema change
             |
             v
Deploy application
             |
             v
Verify application
             |
             v
Remove obsolete schema usage later
```

Avoid migrations that immediately remove or rename columns still required by the previous application version.

For larger systems, use an expand-and-contract migration strategy.

### Your application starts slowly and Elastic Beanstalk reports unhealthy instances during deployment. What could cause this?

Possible causes include:

- Large dependency installation.
- Slow application initialization.
- Database connection delays.
- External API calls during startup.
- Excessive initialization work.
- Large application packages.
- Insufficient instance resources.

Investigate startup duration and health-check behavior rather than simply increasing health-check timeouts.

Production applications should keep startup logic deterministic and avoid performing unnecessary work before the web process can respond.

## Deployment Strategy Scenarios

### You need to release a major application version without immediately replacing all production capacity. What strategy would you consider?

Elastic Beanstalk supports deployment policies that can control how instances are updated.

Depending on the requirement, consider:

- Rolling deployments.
- Rolling deployments with additional batch.
- Immutable deployments.
- Blue/green deployments.

The decision depends on the required balance between:

- Deployment speed.
- Capacity.
- Risk.
- Rollback speed.
- Cost.
- Availability.

### When would you prefer an immutable deployment?

Immutable deployments are useful when deployment isolation is more important than minimizing temporary infrastructure cost.

A new set of instances is created with the new version while the existing environment remains available during the deployment process.

Conceptually:

```text
Existing instances
       |
       | remain available
       v
New instances
       |
       v
Deploy new version
       |
       v
Health validation
       |
       v
Traffic transition
```

This reduces the risk of partially modified production instances.

### When would you use a blue/green deployment?

Blue/green deployment is useful when you need strong separation between the existing production environment and the new version.

```text
              Load Balancer
                   |
             +-----+-----+
             |           |
          Blue          Green
        v1.0.0         v2.0.0
             |
             v
       Switch traffic
```

Benefits include:

- Clear version isolation.
- Fast rollback.
- Independent environment validation.
- Reduced risk during major releases.

The trade-off is additional infrastructure cost and operational complexity.

### Your team wants zero-downtime deployment. Is changing the deployment policy enough?

No.

Zero-downtime deployment depends on the entire application architecture.

Consider:

- Multiple instances.
- Load balancer behavior.
- Health checks.
- Connection draining.
- Session management.
- Backward-compatible database changes.
- Startup time.
- Application shutdown behavior.
- Deployment policy.

A deployment can still cause downtime if the application requires incompatible schema changes or if all capacity becomes unavailable.

## Scaling Scenarios

### Your application receives a sudden traffic spike. What happens in Elastic Beanstalk?

In an Auto Scaling environment, Elastic Beanstalk can work with Auto Scaling to adjust instance capacity according to configured scaling policies.

The general flow is:

```text
Traffic increases
      |
      v
Load balancer
      |
      v
Instances become heavily utilized
      |
      v
Scaling policy triggers
      |
      v
Additional instances
      |
      v
Traffic distributed
```

Scaling is not instantaneous. New instances need time to launch, initialize, install dependencies, start the application, and become healthy.

### CPU utilization is consistently high. Should you immediately increase the instance size?

Not necessarily.

First determine why CPU is high.

Potential causes include:

- Increased traffic.
- Inefficient application code.
- CPU-intensive serialization.
- Expensive database operations.
- Background jobs running on web instances.
- Incorrect worker configuration.
- Memory pressure causing system instability.

The correct response may be:

- Horizontal scaling.
- Vertical scaling.
- Code optimization.
- Database optimization.
- Worker separation.
- Caching.
- Architecture changes.

### Your application has unpredictable traffic spikes. How would you design scaling?

Use horizontal scaling with appropriate Auto Scaling policies and sufficient baseline capacity.

Also consider:

- Load-balancer health checks.
- Instance startup time.
- Minimum and maximum capacity.
- CPU or request-based scaling signals.
- Database connection limits.
- Redis capacity.
- Downstream API limits.

Scaling the application tier without considering the database can simply move the bottleneck:

```text
More EC2 instances
       |
       v
More application workers
       |
       v
More database connections
       |
       v
Database saturation
```

Senior-level scaling decisions therefore consider the entire dependency chain.

## Health Monitoring Scenarios

### Elastic Beanstalk reports a degraded environment. What is your first step?

Do not immediately restart instances.

Start with:

1. Environment health.
2. Recent Elastic Beanstalk events.
3. Application logs.
4. Web server logs.
5. Instance metrics.
6. Load balancer health.
7. Recent deployments.
8. Dependency health.

Determine whether the failure is:

- Application-level.
- Instance-level.
- Network-level.
- Dependency-level.
- Deployment-level.

### Health checks are failing, but users can access the application. How is that possible?

The health check may test a different path, host, port, or request behavior than normal users.

Possible causes include:

- Incorrect health-check path.
- Authentication requirement on the health endpoint.
- Slow health-check response.
- Dependency failure affecting only the health endpoint.
- Security-group or network configuration.
- Application routing mismatch.

A health endpoint should provide a reliable signal of whether the application instance can actually serve traffic.

### Should a health-check endpoint query PostgreSQL, Redis, and every external dependency?

Usually not.

A deep dependency check can turn a temporary dependency problem into an environment-wide unhealthy state.

A useful distinction is:

| Check | Purpose |
|---|---|
| Liveness | Is the process running? |
| Readiness | Can the instance serve traffic? |
| Dependency health | Is a particular dependency available? |

Do not make a simple process health signal depend on every external system unless that dependency is genuinely required for serving requests.

## Logging and Troubleshooting Scenarios

### An application returns HTTP 500, but the Elastic Beanstalk environment is healthy. What does that tell you?

Environment health and application correctness are different signals.

The infrastructure can be healthy while the application returns errors.

Investigate:

- Application logs.
- Exception traces.
- Request-specific context.
- Database errors.
- External API failures.
- Recent code changes.

A healthy EC2 instance does not imply a healthy application.

### Logs are growing rapidly and consuming disk space. What would you investigate?

Check:

- Application logging level.
- Web-server logs.
- Rotation behavior.
- Repeated exceptions.
- Request logging volume.
- Debug logging enabled in production.
- Large payload logging.

Production logging should be:

- Structured where practical.
- Appropriately leveled.
- Searchable.
- Retained according to operational requirements.
- Free from credentials and sensitive data.

### An engineer discovers passwords in application logs. What should happen?

Treat the credentials as compromised.

Actions should include:

1. Stop further logging of the secret.
2. Rotate the credential.
3. Remove or restrict access to affected logs where appropriate.
4. Investigate exposure.
5. Review log retention and access.
6. Fix the application logging behavior.
7. Add secret-scanning controls where appropriate.

Never assume that CloudWatch or Elastic Beanstalk logs are safe places to store secrets.

## Networking Scenarios

### Your Elastic Beanstalk application cannot connect to PostgreSQL in a private subnet. What would you check?

Work through the network path:

```text
Elastic Beanstalk EC2
       |
       v
Security Group
       |
       v
Subnet Route Table
       |
       v
VPC Network
       |
       v
Database Security Group
       |
       v
PostgreSQL
```

Check:

- VPC configuration.
- Subnet placement.
- Route tables.
- Security groups.
- Database listener port.
- Network ACLs if relevant.
- DNS resolution.
- Database availability.
- Credentials.

The database security group should allow traffic from the application's security group rather than from the entire internet.

### The application can connect to an external API from a public environment but not from a private subnet. What could be wrong?

A private subnet does not automatically provide internet access.

If outbound internet access is required, the architecture may require:

```text
Private Subnet
      |
      v
Route Table
      |
      v
NAT Gateway
      |
      v
Internet Gateway
      |
      v
External API
```

Also verify:

- Route configuration.
- NAT gateway availability.
- Security groups.
- Network ACLs.
- DNS resolution.

### Should an Elastic Beanstalk application database be publicly accessible?

Generally, no.

A common production architecture is:

```text
Internet
   |
   v
Load Balancer
   |
   v
Elastic Beanstalk
   |
   v
Private Database
```

The database should normally remain private and accept traffic only from the application's security group or appropriate private network paths.

## Security Scenarios

### Your Elastic Beanstalk application needs a database password. Where should you store it?

Do not hard-code credentials into:

- Source code.
- Git repositories.
- Docker images.
- Configuration committed to version control.
- Application logs.

Prefer managed secret mechanisms such as AWS Secrets Manager or Systems Manager Parameter Store, depending on the application's requirements.

Use IAM permissions to restrict access to only the resources that require the secret.

### An engineer wants to open PostgreSQL port 5432 to `0.0.0.0/0` to solve connectivity problems. Would you approve it?

No.

That creates unnecessary public exposure.

Instead:

```text
Application Security Group
          |
          | TCP 5432
          v
Database Security Group
```

Allow access from the application security group rather than the entire internet.

### An application requires access to an S3 bucket. Should the application use AWS access keys stored in environment variables?

Prefer IAM roles associated with the Elastic Beanstalk instances rather than long-lived static credentials.

The preferred model is:

```text
Application
    |
    v
EC2 Instance Role
    |
    v
IAM Policy
    |
    v
S3
```

This provides temporary credentials and reduces credential-management overhead.

## Configuration Scenarios

### A configuration value differs between development, staging, and production. How should you manage it?

Separate configuration from application code.

Typical examples include:

- Database endpoints.
- Feature flags.
- External service URLs.
- Runtime configuration.
- Environment-specific settings.

Do not create separate application binaries merely because configuration differs.

A typical model is:

```text
Application Artifact
        |
        +--> Development Configuration
        +--> Staging Configuration
        +--> Production Configuration
```

Sensitive values should use an appropriate secret-management mechanism.

### A developer changes an environment variable directly in production. Why is this risky?

Manual changes create configuration drift.

The actual production state may no longer match:

- Infrastructure-as-code.
- Deployment configuration.
- Documentation.
- Version-controlled environment configuration.

Prefer configuration changes through controlled deployment or infrastructure workflows with appropriate auditing.

## CI/CD Scenarios

### How would you design a CI/CD pipeline for Elastic Beanstalk?

A production pipeline could look like:

```mermaid
flowchart LR
    Dev[Developer] --> Git[Git Repository]
    Git --> CI[CI Pipeline]
    CI --> Test[Tests]
    Test --> Build[Build Artifact]
    Build --> Stage[Staging]
    Stage --> Validate[Validation]
    Validate --> Approval[Production Approval]
    Approval --> Prod[Elastic Beanstalk]
    Prod --> Monitor[Health Monitoring]
```

The pipeline should typically include:

- Dependency installation.
- Unit tests.
- Integration tests where appropriate.
- Static analysis.
- Security scanning.
- Artifact creation.
- Staging deployment.
- Smoke tests.
- Production deployment.
- Health verification.
- Rollback capability.

### Should production deployments be triggered manually from an engineer's laptop?

Prefer CI/CD for production deployments.

A controlled pipeline provides:

- Repeatability.
- Auditability.
- Consistent tooling.
- Controlled credentials.
- Approval workflows.
- Deployment history.
- Automated validation.

Manual CLI deployments can be useful for development and emergency operations, but should not become the normal production process.

### Your CI/CD pipeline reports a successful deployment, but production is broken. How would you improve the pipeline?

The pipeline is probably validating deployment completion rather than application correctness.

Add post-deployment checks such as:

- Health verification.
- Smoke tests.
- HTTP status checks.
- Application metrics.
- Critical endpoint validation.
- Error-rate monitoring.

A stronger deployment pipeline is:

```text
Deploy
  |
  v
Platform success
  |
  v
Application health
  |
  v
Smoke tests
  |
  v
Metrics validation
  |
  +---- failure ---> Rollback
  |
  v
Deployment accepted
```

## Platform Update Scenarios

### An Elastic Beanstalk platform version is approaching end of support. What should you do?

Do not wait until the final deadline.

A controlled upgrade process should include:

1. Identify the current platform version.
2. Review supported target versions.
3. Test the application against the target runtime.
4. Verify dependency compatibility.
5. Test staging.
6. Deploy using a controlled strategy.
7. Monitor application behavior.
8. Roll out production.
9. Document the resulting platform version.

Platform upgrades should be treated as engineering changes rather than administrative maintenance.

### A Python platform upgrade breaks a package used by Django. How would you respond?

First isolate whether the issue is caused by:

- Python version changes.
- System-library changes.
- Package compatibility.
- Dependency resolution.
- Build configuration.

Then:

- Reproduce the issue in staging.
- Pin compatible dependency versions.
- Update incompatible dependencies if required.
- Test application behavior.
- Roll back the platform upgrade if production stability is at risk.

Avoid blindly upgrading all dependencies during the same change. Keep the change surface controlled.

## Database Scenarios

### Your Elastic Beanstalk application starts returning database connection errors after scaling from 2 to 20 instances. Why?

The database may have reached its connection limit.

If each instance runs multiple application workers:

```text
20 instances
   x
8 workers
   =
160 potential database connections
```

The actual number depends on application and connection behavior, but the architecture can quickly exceed database capacity.

Possible solutions include:

- Connection pooling.
- Appropriate worker counts.
- Database scaling.
- Query optimization.
- Reducing unnecessary connections.
- Separating workloads.
- Using caching where appropriate.

### Redis is being used for caching, but adding more application instances causes Redis saturation. What does this demonstrate?

Scaling one application tier can increase load on shared dependencies.

The dependency chain must therefore be analyzed as a system:

```text
Clients
   |
   v
Load Balancer
   |
   v
Application Fleet
   |
   +----> PostgreSQL
   |
   +----> Redis
   |
   +----> External APIs
```

Horizontal scaling does not automatically mean the entire system scales horizontally.

## Background Processing Scenarios

### Celery workers are running on the same Elastic Beanstalk instances as Django web workers, and API latency increases. What could be happening?

Background jobs may be competing with web requests for:

- CPU.
- Memory.
- Network bandwidth.
- Database connections.

A better architecture may separate workloads:

```text
                 Load Balancer
                      |
                      v
                Web Environment
                      |
                      v
                   Django
                      |
                      v
                    Redis
                      |
                      v
                Worker Environment
                      |
                      v
                   Celery
```

This allows web and worker capacity to scale independently.

### Your Celery queue is growing continuously even though the web application is healthy. What would you investigate?

Check:

- Worker count.
- Worker CPU and memory.
- Task execution time.
- Failed/retried tasks.
- Queue depth.
- Database performance.
- External API latency.
- Task concurrency.
- Dead-letter or failure handling where applicable.

A healthy web environment does not imply a healthy asynchronous processing system.

## Availability Scenarios

### One Availability Zone experiences an outage. How should a production Elastic Beanstalk environment respond?

For high availability, use a load-balanced environment with multiple instances distributed across Availability Zones.

Conceptually:

```text
                  Load Balancer
                 /             \
                v               v
          Availability Zone A  Availability Zone B
                |               |
             Instance         Instance
```

If one instance or Availability Zone fails, remaining capacity can continue serving traffic, assuming the application and dependencies are also designed for failure.

### Does running multiple Elastic Beanstalk instances guarantee high availability?

No.

You also need to consider:

- Availability Zone distribution.
- Load balancer configuration.
- Database availability.
- Redis availability.
- External dependencies.
- Deployment strategy.
- Application statelessness.
- Session handling.

High availability is an architecture property, not simply an instance count.

## Session Management Scenarios

### Your Django application stores sessions locally on application instances. Users are randomly logged out after scaling. Why?

Requests may reach different instances:

```text
Request 1 --> Instance A --> Session exists
Request 2 --> Instance B --> Session missing
```

Avoid relying on instance-local state in horizontally scaled applications.

Use shared session storage or another architecture that does not depend on a specific instance.

Common options include:

- Database-backed sessions.
- Redis-backed sessions.
- Appropriate external session storage.

The general rule is:

> Application instances should be replaceable.

## Cost Optimization Scenarios

### Your Elastic Beanstalk environment is running four large instances with very low utilization. What would you investigate?

Review:

- CPU utilization.
- Memory utilization.
- Request volume.
- Network utilization.
- Scaling configuration.
- Minimum instance count.
- Instance type.
- Deployment requirements.
- Availability requirements.

Possible optimizations include:

- Smaller instances.
- Lower minimum capacity where safe.
- Better scaling policies.
- Right-sizing.
- Removing unused environments.

Do not reduce capacity blindly if the environment requires redundancy.

### A staging environment runs 24/7 despite being used only during business hours. What could you do?

If operational requirements permit, consider scheduling environment capacity or using a lower-cost architecture for non-production workloads.

However, automated shutdown/startup processes must account for:

- Database availability.
- Persistent state.
- CI/CD dependencies.
- Testing requirements.
- Startup time.

Cost optimization should not compromise developer productivity or environment reliability.

## Disaster Recovery Scenarios

### Your Elastic Beanstalk environment is destroyed. Can you recover the application?

The application artifact can generally be redeployed, but recovery depends on how stateful resources were designed.

Elastic Beanstalk environment configuration should not be treated as the only copy of operational knowledge.

A resilient architecture separates:

```text
Application Artifact
        |
        +--> Version Control
        |
        +--> CI/CD

Infrastructure Configuration
        |
        +--> Infrastructure as Code / Configuration Management

Persistent Data
        |
        +--> Database Backups
        +--> Object Storage
```

### What should be backed up?

Depending on the architecture:

- Database data.
- Object-storage data.
- Critical configuration.
- Infrastructure definitions.
- Application artifacts.
- Important operational metadata.

Do not assume that rebuilding EC2 instances is equivalent to restoring the application state.

### How would you design disaster recovery for a Django application on Elastic Beanstalk?

A typical design is:

```text
                    Route / DNS
                         |
                         v
                Elastic Beanstalk
                         |
              +----------+----------+
              |                     |
              v                     v
          Application          Application
            AZ-A                 AZ-B
              |                     |
              +----------+----------+
                         |
                         v
                    PostgreSQL
                         |
                         v
                     Backups
```

The application tier should be reproducible, while persistent state requires explicit backup and recovery mechanisms.

## Troubleshooting Scenarios

### CPU is normal, memory is normal, but response latency has increased significantly. What would you investigate?

Do not assume infrastructure capacity is the problem.

Investigate:

- Database latency.
- External API latency.
- Redis latency.
- Network latency.
- Application lock contention.
- Thread/process configuration.
- Slow queries.
- Increased request volume.
- Garbage collection or runtime behavior.
- Recent deployments.

A common senior-level debugging principle is:

> A saturated resource is not required for latency to increase.

The bottleneck can be an external dependency or serialization point.

### The application is returning intermittent 502 errors. What would you investigate?

Potential causes include:

- Application process crashes.
- Application process restarts.
- Upstream connection failures.
- Incorrect web-server configuration.
- Instance health issues.
- Insufficient worker capacity.
- Long-running requests.
- Deployment transitions.

Correlate:

```text
502 errors
   |
   +--> Load balancer logs
   +--> Web-server logs
   +--> Application logs
   +--> Instance health
   +--> Deployment events
   +--> Resource metrics
```

Look for temporal correlation rather than inspecting each system independently.

### One instance is unhealthy while the others are healthy. Would you immediately redeploy?

No.

First determine whether the problem is isolated to that instance.

Possible causes include:

- Corrupted local state.
- Memory leak.
- Disk exhaustion.
- Process failure.
- Instance-level networking issue.
- Bad startup state.

If the instance is disposable and Auto Scaling can replace it safely, replacement may be appropriate. But root-cause investigation is still valuable if the issue can recur.

## Configuration Drift Scenarios

### The production environment contains settings that do not exist in version control. What problem does this create?

This is configuration drift.

It makes production difficult to reproduce and increases operational risk.

A better model is:

```text
Version-controlled configuration
             |
             v
        CI/CD Pipeline
             |
             v
      Production Environment
```

Production should be reproducible from controlled sources as much as practical.

### An engineer manually modifies production configuration during an incident. Is that always wrong?

No.

Emergency changes may be necessary to restore service.

The problem occurs when emergency changes are not:

- Documented.
- Audited.
- Reconciled into the normal configuration source.
- Tested.
- Reverted or permanently adopted.

Operational maturity means distinguishing emergency mitigation from permanent configuration management.

## Architecture Decision Scenarios

### Your company has a small team building a single Django monolith. Would you recommend EKS?

Probably not unless there is a specific requirement.

A simpler architecture such as Elastic Beanstalk may provide sufficient:

- Deployment automation.
- Load balancing.
- Scaling.
- Health management.
- Platform management.

The goal is not to maximize infrastructure sophistication. The goal is to satisfy requirements with an appropriate operational burden.

### Your company has standardized all workloads on Kubernetes. Should a new Django service use Elastic Beanstalk?

Not necessarily.

Organizational standards can outweigh the isolated technical advantages of another service.

Consider:

- Existing deployment tooling.
- Monitoring.
- Security controls.
- Developer expertise.
- Platform team capabilities.
- Compliance.
- Service-to-service networking.
- Operational consistency.

Architecture decisions should consider the broader platform ecosystem.

### You need separate scaling for API requests and Celery workloads. How would you approach it?

Separate the workloads into independently scalable environments.

```text
                    Clients
                       |
                       v
                 Load Balancer
                       |
                       v
                Web Environment
                       |
                       v
                    Django
                       |
                       v
                    Redis
                       |
                       v
               Worker Environment
                       |
                       v
                    Celery
```

This prevents background workloads from consuming the capacity required by user-facing requests.

## Senior-Level Incident Scenario

### Production latency suddenly increases after a deployment. What is your response?

A strong incident response is systematic:

1. Confirm the impact.
2. Identify when the regression started.
3. Correlate the timing with the deployment.
4. Check application error rates.
5. Check infrastructure metrics.
6. Check database and cache latency.
7. Check external dependencies.
8. Compare the current version with the previous version.
9. Roll back if the deployment is the most likely cause and user impact is significant.
10. Continue root-cause analysis after service stability is restored.

The priority order is:

```text
Protect users
     |
     v
Restore service
     |
     v
Collect evidence
     |
     v
Identify root cause
     |
     v
Implement permanent fix
     |
     v
Prevent recurrence
```

Do not spend excessive time proving the exact root cause while production remains degraded if a safe rollback can restore service.

## Senior-Level Trade-Off Scenario

### The business asks for a deployment platform that is simple, highly available, cheap, infinitely scalable, and fully customizable. How would you respond?

Explain that these requirements contain trade-offs.

For example:

| Requirement | Typical trade-off |
|---|---|
| Maximum simplicity | Less infrastructure control |
| Maximum customization | More operational work |
| Very low cost | Potentially less redundancy |
| High availability | Additional infrastructure cost |
| Rapid scaling | Capacity and dependency planning |
| Full control | Higher engineering responsibility |

The correct architecture is determined by business priorities and technical constraints, not by finding a service that theoretically provides everything.

## Interview Decision Matrix

| Scenario | Likely direction |
|---|---|
| Django monolith with small operations team | Elastic Beanstalk |
| Full VM customization required | EC2 |
| Containerized microservices | ECS |
| Containers without server management | ECS + Fargate |
| Kubernetes-standard organization | EKS |
| Event-driven short-lived workloads | Lambda |
| Simple managed web service | App Runner |
| Shared web and worker workloads causing contention | Separate environments |
| Database inaccessible from application | Investigate VPC, routes, and security groups |
| Deployment causes immediate 5xx errors | Investigate and consider rollback |
| Unpredictable traffic | Auto Scaling + dependency capacity planning |
| Platform version nearing end of support | Test and upgrade proactively |
| Credentials committed to source control | Rotate and move to managed secrets |
| Database exposed publicly | Restrict access using private networking/security groups |
| Production configuration differs from source | Eliminate configuration drift |
| Instance-local sessions fail after scaling | Externalize session state |
| Database connection exhaustion after scaling | Review workers, pooling, and DB capacity |
| Celery impacts API performance | Separate web and worker capacity |
| Need fast rollback for major release | Blue/green or immutable deployment |

## Common Mistakes

### Treating Elastic Beanstalk health as application health

Environment health provides valuable infrastructure and application signals, but a healthy environment does not mean every API endpoint is functioning correctly.

Use application-level observability alongside platform health.

### Scaling without checking dependencies

Adding application instances can increase pressure on:

- PostgreSQL.
- Redis.
- Kafka.
- External APIs.
- Connection pools.

Always evaluate downstream capacity.

### Using instance-local state

Instances in a scalable environment are disposable.

Avoid relying on:

- Local session files.
- Local uploaded files.
- Local persistent application state.

Use appropriate shared services instead.

### Making production changes manually without reconciliation

Emergency changes may be necessary, but permanent configuration should be captured in the controlled deployment or infrastructure workflow.

### Treating rollback as a substitute for compatibility

Rollback cannot always safely undo:

- Database schema changes.
- Data migrations.
- External API changes.
- Irreversible state changes.

Design deployments for compatibility rather than assuming rollback is always sufficient.

### Exposing databases publicly to solve connectivity problems

Fix networking and security-group configuration instead.

Public exposure increases attack surface without solving the underlying architectural problem correctly.

### Running background jobs on web instances without capacity planning

Celery, scheduled jobs, or other workers can consume resources required for HTTP traffic.

Separate workloads when their scaling characteristics differ.

### Using overly complex infrastructure for simple applications

A technically sophisticated platform can create more operational risk than it removes.

Choose the smallest architecture that satisfies the real requirements.

## Key Takeaways

- Scenario-based Elastic Beanstalk questions are primarily testing engineering judgment.
- Start troubleshooting with evidence: health, events, logs, metrics, deployments, and dependency status.
- A successful deployment does not guarantee a healthy application.
- A healthy Elastic Beanstalk environment does not guarantee that every application endpoint works.
- Prefer backward-compatible database changes for rolling or multi-instance deployments.
- Use deployment strategies based on risk, rollback requirements, availability, and cost.
- Blue/green deployments provide strong environment isolation and fast traffic switching at additional infrastructure cost.
- Immutable deployments reduce the risk of modifying existing production instances during deployment.
- Horizontal scaling must be evaluated together with database, Redis, Kafka, and external-service capacity.
- Database connection limits are a common hidden bottleneck when application capacity increases.
- Application instances should be stateless and replaceable wherever practical.
- Sessions, uploaded files, and persistent state should not depend on a particular instance.
- Separate web and Celery worker capacity when their resource or scaling characteristics differ.
- Private application architectures should use appropriate VPC routing, security groups, and NAT where required.
- Databases should generally remain private and should not be exposed to the public internet merely to solve connectivity problems.
- Prefer IAM roles and managed secret stores over long-lived credentials embedded in applications.
- CI/CD should validate application health, not merely deployment completion.
- Platform upgrades should be tested proactively rather than performed only when support deadlines become urgent.
- Production incidents should prioritize user impact reduction and service restoration before extended root-cause analysis.
- Rollback is a mitigation mechanism, not a replacement for backward-compatible application and database design.
- High availability requires redundancy across the entire architecture, not merely multiple application instances.
- Cost optimization should be based on utilization and business requirements rather than blindly reducing capacity.
- Production configuration should be reproducible and protected from unmanaged configuration drift.
- Senior engineers optimize for reliability, simplicity, observability, and operational safety rather than infrastructure complexity.