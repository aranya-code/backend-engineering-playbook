# 03- Deployment Questions

## Overview

Deployment questions for Amazon Elastic Beanstalk typically evaluate whether an engineer understands the difference between **shipping application code** and performing a **safe production release**.

Strong answers should cover:

- Application versions and deployments
- Deployment policies
- Rolling, rolling with additional batch, immutable, and traffic-shifting approaches
- Blue/green deployments
- CI/CD integration
- Environment configuration
- Database migration safety
- Health checks
- Rollbacks
- Deployment failure handling
- Platform updates
- Secrets and configuration
- Deployment observability
- Zero-downtime requirements
- Production release strategy

The important interview distinction is that a deployment can succeed technically while the application is still unhealthy. A production deployment strategy must therefore consider **capacity, compatibility, health, rollback, dependencies, and observability**.

## Deployment Model

### How does deployment work in Elastic Beanstalk?

**Answer:**

An application version is uploaded to Elastic Beanstalk and then deployed to an environment.

Conceptually:

```text
Source Code
    |
    v
Build / Test
    |
    v
Application Artifact
    |
    v
Elastic Beanstalk Application Version
    |
    v
Deployment Policy
    |
    v
Environment Instances
    |
    v
Health Validation
```

The deployment mechanism determines how existing instances are replaced or updated.

A production pipeline should treat the application artifact as immutable and promote the same tested artifact across environments rather than rebuilding different artifacts for each environment.

### What is an Elastic Beanstalk application version?

**Answer:**

An application version represents a specific deployable version of an application.

A version should correspond to a known source revision or build artifact.

For example:

```text
Git commit
    |
    v
CI build
    |
    v
Application artifact
    |
    v
EB Application Version
```

This makes releases traceable and allows a known-good version to be redeployed.

### Why should deployments use immutable artifacts?

**Answer:**

If the artifact changes after testing, production is no longer receiving exactly what was validated.

A safer model is:

```text
Build once
    |
    v
Test artifact
    |
    v
Deploy same artifact
    |
    v
Production
```

Avoid:

```text
Build for staging
    |
    v
Modify
    |
    v
Build again for production
```

The second approach can introduce differences that were never tested.

## Deployment Policies

### What deployment policies does Elastic Beanstalk provide?

**Answer:**

Elastic Beanstalk supports several deployment approaches, including:

| Strategy | Existing instances | Temporary capacity | Typical use |
|---|---|---|---|
| All at once | Replaced together | No | Development or downtime-tolerant workloads |
| Rolling | Updated in batches | No | Cost-sensitive deployments |
| Rolling with additional batch | Updated in batches | Yes | Higher availability during rolling updates |
| Immutable | New instances created | Yes | Safer production deployments |
| Traffic splitting | New capacity receives controlled traffic | Yes | Gradual validation and rollout |

The exact suitability depends on application architecture, availability requirements, deployment duration, and dependency compatibility.

### What is an all-at-once deployment?

**Answer:**

All-at-once deployment updates the entire environment at once.

Conceptually:

```text
Before:

Instance A -> v1
Instance B -> v1
Instance C -> v1

Deployment

Instance A -> v2
Instance B -> v2
Instance C -> v2
```

The advantage is simplicity and speed.

The major disadvantage is that the entire application fleet can be affected simultaneously.

It is generally more appropriate for:

- Development
- Testing
- Non-critical environments
- Applications where short downtime is acceptable

### What is rolling deployment?

**Answer:**

Rolling deployment updates a subset of instances at a time.

```text
Before:

A -> v1
B -> v1
C -> v1
D -> v1

Batch 1:

A -> v2
B -> v2
C -> v1
D -> v1

Batch 2:

A -> v2
B -> v2
C -> v2
D -> v2
```

This reduces the amount of capacity affected simultaneously.

The trade-off is that different application versions may temporarily coexist.

### What is rolling deployment with an additional batch?

**Answer:**

A temporary batch of additional capacity is created so that existing capacity can continue serving traffic while new capacity is updated.

This reduces the capacity impact of deployment compared with a standard rolling deployment.

The trade-off is additional temporary infrastructure cost.

### What is immutable deployment?

**Answer:**

Immutable deployment creates a new set of instances with the new application version rather than modifying the existing instances in place.

Conceptually:

```text
Existing fleet
    |
    +--> A v1
    +--> B v1
    +--> C v1

New fleet
    |
    +--> D v2
    +--> E v2
    +--> F v2

Validate v2
    |
    v
Replace old fleet
```

This provides stronger isolation between old and new versions.

It is particularly useful when deployment safety is more important than minimizing temporary compute cost.

### Why is immutable deployment safer?

**Answer:**

The existing environment remains intact while the new capacity is created.

If the new version fails health checks:

```text
v2 unhealthy
     |
     v
Discard new capacity
     |
     v
v1 remains available
```

This is generally safer than modifying the only production capacity in place.

### What is traffic splitting?

**Answer:**

Traffic splitting sends a controlled percentage of production traffic to a new application version while the existing version continues serving the remaining traffic.

Conceptually:

```text
                 Load Balancer
                  /          \
                 /            \
             95%              5%
              |                |
             v1               v2
```

If the new version behaves correctly, traffic can be increased or the deployment can be completed.

If the new version produces problems, traffic can be returned to the previous version.

### What are the risks of traffic splitting?

**Answer:**

Traffic splitting does not make incompatible application versions safe automatically.

Potential issues include:

- Incompatible database schemas
- Different session formats
- Cache incompatibility
- Different API behavior
- Non-idempotent operations
- External side effects
- Inconsistent feature behavior

The old and new versions must be able to coexist safely.

## Choosing a Deployment Strategy

### Which deployment strategy would you choose for a critical production API?

**Answer:**

For a critical API, I would generally prefer an approach that keeps existing capacity available while validating the new version, such as immutable deployment or controlled traffic shifting.

The decision depends on:

- Application architecture
- Deployment duration
- Cost tolerance
- Database compatibility
- Rollback requirements
- Traffic characteristics
- Availability requirements

The answer should explain the trade-off rather than simply naming one strategy.

### How would you choose between rolling and immutable deployment?

**Answer:**

| Requirement | Rolling | Immutable |
|---|---:|---:|
| Minimize temporary capacity | Strong | Weak |
| Deployment isolation | Moderate | Strong |
| Cost efficiency | Strong | Moderate |
| Production safety | Moderate | Strong |
| Simple rollback | Moderate | Strong |
| Mixed-version exposure | Possible | Reduced |
| Suitable for critical APIs | Depends | Often preferable |

Rolling deployments can be appropriate when cost and capacity efficiency matter.

Immutable deployments are attractive when release isolation and rollback safety are more important.

## Zero-Downtime Deployments

### How do you achieve zero-downtime deployment?

**Answer:**

Zero-downtime deployment is a system property, not simply a deployment setting.

It requires:

- Multiple application instances
- Load-balancer health checks
- Capacity remaining available during deployment
- Graceful application startup
- Backward-compatible changes
- Safe database migrations
- Proper connection draining
- Automated health validation
- Fast rollback

A typical flow is:

```text
Existing Healthy Fleet
          |
          v
Create / update new capacity
          |
          v
Application startup
          |
          v
Health checks
          |
          v
Healthy?
      /        \
    No          Yes
    |             |
 Rollback      Receive traffic
                  |
                  v
             Complete release
```

### Can a single-instance environment provide zero downtime?

**Answer:**

Not reliably.

If the only instance is being replaced or restarted, there may be no capacity available to serve requests.

For production zero-downtime requirements, multiple application instances are generally necessary.

### Why are health checks important during deployment?

**Answer:**

A process can be running while the application is still unusable.

For example:

```text
Process: Running
Port: Open
HTTP: 500
Database: Unavailable
```

A meaningful health check should validate enough of the application to determine whether it is capable of serving production traffic.

Avoid making health checks so deep that they create unnecessary load or fail because of non-critical dependencies.

## CI/CD

### How would you integrate Elastic Beanstalk with CI/CD?

**Answer:**

A typical pipeline is:

```mermaid
flowchart LR
    Commit[Git Commit] --> Build[Build Artifact]
    Build --> Test[Automated Tests]
    Test --> Security[Security Checks]
    Security --> Stage[Deploy Staging]
    Stage --> Validate[Health Validation]
    Validate --> Approval[Production Approval]
    Approval --> Prod[Deploy Production]
    Prod --> Monitor[Monitor Release]
    Monitor --> Rollback[Rollback if Required]
```

A production pipeline should automate repetitive operations while retaining appropriate approval controls for high-risk releases.

### What should happen before a production deployment?

**Answer:**

At minimum:

1. Source code validation.
2. Unit and integration tests.
3. Dependency/security checks.
4. Artifact creation.
5. Staging deployment.
6. Smoke tests.
7. Configuration validation.
8. Database migration validation.
9. Production deployment.
10. Post-deployment health verification.

The exact pipeline should reflect the application's risk profile.

### Should the CI pipeline build the artifact separately for staging and production?

**Answer:**

Prefer building once and promoting the same artifact.

```text
Git
 |
 v
Build
 |
 v
Artifact v42
 |
 +--> Staging
 |
 +--> Production
```

This provides stronger release reproducibility.

### Where should AWS credentials be stored in CI/CD?

**Answer:**

Avoid hardcoding long-lived AWS access keys in the repository.

Prefer short-lived credentials and workload identity mechanisms where supported by the CI/CD platform.

For GitHub Actions, an AWS IAM role accessed through OpenID Connect is generally preferable to storing persistent IAM access keys as repository secrets.

## Environment Configuration

### How should environment-specific configuration be managed?

**Answer:**

Separate configuration from application code.

```text
Application Artifact
        |
        +--> Development Configuration
        |
        +--> Staging Configuration
        |
        +--> Production Configuration
```

Configuration can include:

- Database endpoints
- Feature flags
- Logging levels
- External service endpoints
- Application settings

Secrets should be managed through dedicated secret-management mechanisms rather than committed to source control.

### Should production configuration be stored in Git?

**Answer:**

Non-sensitive declarative configuration may be version controlled where appropriate.

Sensitive values such as:

- Database passwords
- API tokens
- Private keys
- OAuth secrets

should not be committed to the repository.

Use managed secret storage or an appropriate secure configuration mechanism.

### What is configuration drift?

**Answer:**

Configuration drift occurs when environments gradually become different even though they are expected to be equivalent.

For example:

```text
Staging:
DATABASE_POOL_SIZE=20

Production:
DATABASE_POOL_SIZE=50
```

Some differences are intentional, but undocumented manual changes create operational risk.

Infrastructure and configuration should be managed through repeatable automation wherever practical.

## Database Migrations

### How should database migrations be handled during deployment?

**Answer:**

Database changes should be designed for compatibility with both the old and new application versions when deployments can temporarily run multiple versions.

A safer pattern is:

```text
Old Application
      |
      v
Add compatible schema
      |
      v
Deploy new application
      |
      v
Backfill data
      |
      v
Switch application behavior
      |
      v
Remove obsolete schema later
```

This is commonly called an **expand-and-contract** migration strategy.

### Why are destructive migrations dangerous during deployment?

**Answer:**

Suppose version 1 expects:

```text
users.email_address
```

and version 2 expects:

```text
users.email
```

If the column is renamed immediately, version 1 may fail while old instances are still serving traffic.

A deployment can therefore fail even though the new application itself is correct.

### Should migrations run on every Elastic Beanstalk instance?

**Answer:**

Usually no.

If every instance executes the migration concurrently:

```text
Instance A -> migrate
Instance B -> migrate
Instance C -> migrate
Instance D -> migrate
```

you can create race conditions, lock contention, or duplicate migration attempts.

Use a controlled migration mechanism with clear ownership and concurrency behavior.

### Should database migrations be part of application startup?

**Answer:**

Generally avoid automatically running potentially expensive or destructive migrations every time an application instance starts.

Instance startup should remain predictable.

A safer operational model is to treat database migrations as an explicit deployment step with monitoring and rollback planning.

## Rollbacks

### How would you roll back an Elastic Beanstalk deployment?

**Answer:**

The exact mechanism depends on the deployment strategy, but the fundamental approach is to restore a known-good application version.

Conceptually:

```text
Production
   |
   v
Version 43
   |
   | Incident
   v
Version 42
   |
   v
Known-good release
```

The rollback process should be automated or documented enough that engineers can execute it quickly during an incident.

### Is application rollback enough?

**Answer:**

No.

Database changes may not be reversible in the same way as application code.

For example:

```text
Application v2
      |
      v
Database migration
      |
      v
Application rollback to v1
```

If the migration removed data or changed the schema incompatibly, v1 may still fail.

This is why backward-compatible database migrations are critical.

### What makes a rollback safe?

**Answer:**

A rollback should have:

- A known-good artifact
- Compatible database schema
- Clear deployment history
- Automated health checks
- Monitoring
- Defined ownership
- A tested rollback procedure

Rollback should be considered during design, not after deployment failure.

## Failed Deployments

### What would you do if an Elastic Beanstalk deployment fails?

**Answer:**

First determine whether the failure is:

- Build-related
- Configuration-related
- Dependency-related
- Application startup-related
- Health-check-related
- Database-related
- Networking-related
- Capacity-related

A practical investigation sequence is:

```text
Deployment Failure
       |
       v
Check Deployment Events
       |
       v
Check Environment Health
       |
       v
Check Application Logs
       |
       v
Check Load Balancer Health
       |
       v
Check Dependencies
       |
       v
Determine Rollback / Fix
```

Avoid immediately retrying the same deployment without understanding the failure.

### What if the application starts but health checks fail?

**Answer:**

Check:

- Application startup logs
- Environment variables
- Database connectivity
- Port configuration
- Security groups
- Health-check path
- Dependency initialization
- Application timeouts
- Recent code changes

The important distinction is:

```text
Deployment successful
        !=
Application healthy
```

### What if only the new application version returns HTTP 500 errors?

**Answer:**

First stop or reverse the rollout if the deployment strategy permits it.

Then investigate:

- Application logs
- Error rates
- Stack traces
- Dependency changes
- Configuration differences
- Database migrations
- External API behavior

Do not allow a known-bad version to continue receiving production traffic merely because the deployment process itself completed successfully.

## Health Checks

### What should a production health endpoint return?

**Answer:**

A health endpoint should provide a meaningful signal about whether the application can serve traffic.

For example:

```text
GET /health

200 OK
```

The implementation should be lightweight and predictable.

A separate readiness check can be used when the application needs to distinguish:

- Process is running
- Application is ready to receive traffic

### Should a health check query every dependency?

**Answer:**

Not necessarily.

A health check that performs expensive database, Redis, Kafka, and external API operations on every probe can create additional load and false failures.

A better design distinguishes between:

- Liveness
- Readiness
- Dependency health
- Deep diagnostic checks

For example:

```text
Liveness
    |
    +--> Process is functioning

Readiness
    |
    +--> Application can serve requests

Deep diagnostics
    |
    +--> Database
    +--> Redis
    +--> External services
```

## Platform Updates During Deployment

### How are platform updates different from application deployments?

**Answer:**

An application deployment changes application code.

A platform update can change the underlying Elastic Beanstalk platform/runtime components, such as:

- Operating system components
- Language runtime
- Web server
- Platform dependencies
- Security patches

The risk profile is therefore different.

### How should platform updates be handled in production?

**Answer:**

Use a controlled process:

```text
New Platform Version
        |
        v
Test Environment
        |
        v
Application Validation
        |
        v
Staging
        |
        v
Production Rollout
        |
        v
Monitor
```

Do not treat platform upgrades as routine application deployments.

### Why should platform upgrades be tested?

**Answer:**

Runtime changes can introduce:

- Dependency incompatibilities
- Python runtime behavior changes
- OS-level differences
- Web server configuration changes
- TLS behavior changes
- Native library incompatibilities

An application that worked on the previous platform version may not behave identically after the upgrade.

## Deployment Observability

### What should you monitor immediately after deployment?

**Answer:**

Compare production behavior before and after deployment.

Monitor:

| Signal | What it tells you |
|---|---|
| HTTP 5xx | Application failures |
| HTTP 4xx | Client/API behavior changes |
| Latency | Performance regression |
| Request count | Traffic behavior |
| CPU | Compute pressure |
| Memory | Resource pressure |
| Database connections | Connection pressure |
| Database latency | Query/dependency impact |
| Queue depth | Background processing impact |
| Error logs | Root-cause evidence |
| Business metrics | Actual user impact |

A deployment should be considered successful only after the application demonstrates healthy behavior under real traffic.

### What is a deployment health gate?

**Answer:**

A health gate prevents the pipeline from progressing when defined release criteria are not met.

For example:

```text
Deploy
  |
  v
Smoke Tests
  |
  v
5xx < threshold?
  |
  +---- No ---> Rollback
  |
 Yes
  |
  v
Latency within threshold?
  |
  +---- No ---> Rollback
  |
 Yes
  |
  v
Continue
```

This converts deployment validation from a manual judgment into a repeatable engineering control.

## Blue/Green Deployment

### How does blue/green deployment work with Elastic Beanstalk?

**Answer:**

Maintain two environments:

```text
Blue
v1
 |
 +--> Current Production

Green
v2
 |
 +--> Candidate
```

Deploy and test the new version in green.

After validation, switch production traffic from blue to green.

If problems occur:

```text
Green unhealthy
      |
      v
Switch back
      |
      v
Blue becomes production
```

### What are the main benefits?

**Answer:**

- Strong environment isolation
- Independent testing
- Fast traffic rollback
- Reduced deployment blast radius
- Easier validation of a new platform/runtime

### What are the main limitations?

**Answer:**

- Additional infrastructure cost
- Duplicate environments
- Configuration drift risk
- Shared database compatibility requirements
- Cache/session considerations
- External side-effect considerations

Blue/green is strongest when the application and dependencies support running two versions safely.

## Deployment Safety

### What is the safest way to deploy a backward-incompatible API change?

**Answer:**

Avoid making the API change backward-incompatible in a single release.

Prefer staged compatibility:

```text
Version 1
   |
   v
Support old + new contract
   |
   v
Deploy clients
   |
   v
Migrate traffic
   |
   v
Remove old contract later
```

This reduces the risk caused by rolling deployments, blue/green environments, and independently deployed clients.

### How should feature flags be used during deployment?

**Answer:**

Feature flags can separate code deployment from feature activation.

```text
Deploy code
    |
    v
Feature disabled
    |
    v
Validate infrastructure
    |
    v
Enable for small audience
    |
    v
Monitor
    |
    v
Enable broadly
```

Feature flags should have ownership, lifecycle management, and removal plans.

Permanent unmanaged flags create technical debt and configuration complexity.

## Security During Deployment

### What security checks should exist in a CI/CD pipeline?

**Answer:**

Depending on the application, consider:

- Dependency vulnerability scanning
- Secret scanning
- Static analysis
- Container/image scanning where applicable
- Infrastructure-as-code scanning
- Unit and integration tests
- IAM policy review
- Artifact integrity controls

Security should be integrated into the release process rather than performed only after deployment.

### Should developers deploy directly to production?

**Answer:**

This depends on organizational controls and risk requirements.

For production systems, a stronger model is:

```text
Developer
   |
   v
Pull Request
   |
   v
Automated Checks
   |
   v
Build Artifact
   |
   v
Staging
   |
   v
Approval / Release Policy
   |
   v
Production
```

The important principle is controlled, auditable access to production.

## Deployment Performance

### How can you reduce deployment time?

**Answer:**

First measure where time is spent.

Possible optimizations include:

- Reduce unnecessary dependencies
- Cache dependency installation where supported
- Keep artifacts focused
- Parallelize CI checks
- Pre-build artifacts
- Avoid unnecessary instance replacement
- Optimize startup time
- Reduce migration duration
- Separate long-running tasks from startup

Do not optimize deployment speed by removing critical validation.

### Why is application startup time important?

**Answer:**

During scaling or deployment, new instances must become healthy before they can reliably contribute capacity.

If startup takes several minutes:

```text
Traffic increases
    |
    v
Auto Scaling
    |
    v
New instance
    |
    | 4-minute startup
    v
Ready
```

The environment may remain under-capacity during that period.

Startup should therefore be deterministic and as lightweight as practical.

## Common Deployment Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Deploying directly to production | Manual process is convenient | Use CI/CD |
| Using all-at-once for critical systems | It is simple and fast | Use safer rollout strategies |
| Rebuilding artifacts per environment | Pipeline is poorly structured | Build once, promote the artifact |
| Running migrations on every instance | Startup logic is overloaded | Use controlled migration execution |
| Storing secrets in Git | Configuration is mixed with code | Use managed secrets |
| Ignoring health checks | Deployment success is confused with health | Validate application behavior |
| Making destructive schema changes | Database migration is treated separately | Use backward-compatible migrations |
| Manual production changes | Immediate fixes seem faster | Automate and audit changes |
| No rollback plan | Deployment is considered complete after upload | Define rollback before release |
| Testing only application code | Platform behavior is ignored | Test platform/runtime changes |
| Ignoring startup time | Local startup is fast | Measure production startup |
| Monitoring only CPU | Infrastructure metrics are easy to see | Monitor application and business metrics |
| Deploying untested platform updates | Platform upgrades appear routine | Validate in lower environments |
| Using local filesystem for state | Works on one instance | Externalize persistent state |

## Interview Traps

### Is a successful Elastic Beanstalk deployment proof that production is healthy?

**Answer:**

No.

Deployment success means the deployment operation completed.

Production health requires validating:

- Application responses
- Error rates
- Latency
- Dependencies
- Database connectivity
- Resource utilization
- Business behavior

### Can you roll back any deployment instantly?

**Answer:**

No.

Application rollback can be fast if a known-good version exists, but database migrations, external side effects, and data transformations may make rollback difficult or impossible.

This is why backward-compatible changes are important.

### Is rolling deployment always zero downtime?

**Answer:**

No.

Downtime can still occur due to:

- Insufficient remaining capacity
- Unhealthy instances
- Incorrect health checks
- Application startup failures
- Database migrations
- Connection exhaustion
- Dependency failures

Deployment strategy alone does not guarantee zero downtime.

### Does blue/green eliminate deployment risk?

**Answer:**

No.

It reduces certain infrastructure and application rollout risks but does not eliminate risks involving shared dependencies such as databases, caches, queues, and external systems.

### Should every deployment automatically run database migrations?

**Answer:**

Not blindly.

Migration execution should be controlled, observable, and designed for the application's deployment model.

### Is increasing the deployment batch size always faster and better?

**Answer:**

No.

Larger batches can reduce deployment time but increase the blast radius of a failure.

The correct batch size depends on:

- Fleet size
- Availability requirements
- Deployment duration
- Application startup time
- Risk tolerance

## Scenario-Based Deployment Questions

### A deployment succeeds, but HTTP 5xx errors increase. What do you do?

**Answer:**

1. Confirm the increase is correlated with the deployment.
2. Inspect application logs and traces.
3. Check environment and load-balancer health.
4. Check database and dependency metrics.
5. Stop further rollout if applicable.
6. Roll back to the known-good version if customer impact is significant.
7. Investigate the root cause after service stability is restored.

The priority during an incident is to restore service before performing an exhaustive root-cause analysis.

### A new version requires a database column that does not exist yet. How would you deploy it?

**Answer:**

Use an expand-and-contract sequence.

```text
Deploy schema addition
        |
        v
Deploy application that can use new column
        |
        v
Backfill if required
        |
        v
Enable new behavior
```

The old application should remain compatible with the expanded schema during the transition.

### You need to rename a production database column. What is your approach?

**Answer:**

Avoid an immediate rename if old and new application versions may coexist.

Instead:

```text
Add new column
      |
      v
Write to both columns if required
      |
      v
Backfill new column
      |
      v
Deploy application reading new column
      |
      v
Stop using old column
      |
      v
Remove old column later
```

This minimizes deployment coupling.

### A new release causes memory usage to increase gradually. What would you investigate?

**Answer:**

Look for:

- Memory leaks
- Increased object retention
- Larger caches
- Changed request payloads
- New background tasks
- Dependency changes
- Connection handling
- Worker configuration

Compare pre-deployment and post-deployment metrics rather than assuming the instance type is too small.

### A production deployment takes 20 minutes. Is that necessarily a problem?

**Answer:**

Not necessarily.

Deployment duration should be evaluated against:

- Availability requirements
- Release frequency
- Capacity impact
- Rollback time
- Deployment risk
- Business requirements

A 20-minute deployment with strong safety controls may be preferable to a 5-minute deployment that creates significant production risk.

## Production Deployment Checklist

### Before Deployment

- [ ] Application artifact is immutable and traceable.
- [ ] Automated tests have passed.
- [ ] Security checks have passed.
- [ ] Configuration has been validated.
- [ ] Database migrations are backward-compatible.
- [ ] Rollback version is identified.
- [ ] Deployment strategy is appropriate for the workload.
- [ ] Monitoring and alerts are operational.
- [ ] Required approvals are complete.

### During Deployment

- [ ] Monitor deployment events.
- [ ] Monitor application health.
- [ ] Monitor HTTP 4xx/5xx rates.
- [ ] Monitor latency.
- [ ] Monitor CPU and memory.
- [ ] Monitor database connections and latency.
- [ ] Monitor queue and cache behavior where applicable.
- [ ] Stop rollout if defined health thresholds are breached.

### After Deployment

- [ ] Smoke tests pass.
- [ ] Error rates remain within normal limits.
- [ ] Latency remains within expected limits.
- [ ] Critical business flows work.
- [ ] Background jobs are processing normally.
- [ ] Database behavior is healthy.
- [ ] No unexpected resource saturation is observed.
- [ ] Deployment version is recorded.

## Key Takeaways

- Elastic Beanstalk deployment is not simply uploading code; it is a controlled change to a running production system.
- Choose deployment policies based on availability, cost, deployment duration, and rollback requirements.
- Rolling deployments reduce deployment blast radius but can temporarily run multiple application versions.
- Immutable deployments provide stronger isolation by creating new capacity before replacing existing capacity.
- Traffic splitting allows controlled exposure of a new version but requires compatibility between old and new versions.
- Blue/green deployment provides strong environment isolation and fast traffic rollback, but shared dependencies still need careful design.
- Build artifacts once and promote the same artifact through environments.
- Never confuse deployment success with application health.
- Health checks, smoke tests, metrics, logs, and business signals should participate in release validation.
- Database migrations are one of the biggest sources of deployment risk; prefer backward-compatible expand-and-contract patterns.
- Do not automatically execute potentially conflicting migrations from every application instance.
- A rollback plan must exist before deployment begins.
- Application rollback does not necessarily mean database rollback is safe.
- Keep secrets outside source control and use least-privilege deployment identities.
- Platform upgrades require the same production discipline as application releases because runtime changes can affect application behavior.
- Optimize deployment speed without removing safety controls.
- A strong deployment architecture minimizes blast radius, preserves service availability, makes releases reproducible, and provides a tested path back to a known-good state.