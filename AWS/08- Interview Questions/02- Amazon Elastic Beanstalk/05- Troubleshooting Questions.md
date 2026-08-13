# 05- Troubleshooting Questions

## Overview

Amazon Elastic Beanstalk troubleshooting questions evaluate whether an engineer can diagnose failures systematically rather than relying on trial-and-error configuration changes.

A strong troubleshooting approach separates the system into layers:

```text
Client
  |
  v
DNS
  |
  v
Load Balancer
  |
  v
Elastic Beanstalk Environment
  |
  +--> EC2 Instance
  |      |
  |      +--> Application
  |      +--> Web Server
  |      +--> Platform Runtime
  |
  +--> Security Groups
  +--> IAM
  +--> VPC / Subnets
  +--> RDS / Redis / S3
  +--> CloudWatch
```

The first objective is to identify **where the failure occurs** before changing configuration.

A practical troubleshooting sequence is:

```text
Observe
  |
  v
Identify failing layer
  |
  v
Check recent changes
  |
  v
Inspect health and metrics
  |
  v
Inspect logs
  |
  v
Validate networking / IAM / configuration
  |
  v
Reproduce
  |
  v
Apply smallest safe fix
  |
  v
Verify
  |
  v
Document root cause
```

## General Troubleshooting Methodology

### What is the first thing you should do when an Elastic Beanstalk application fails?

**Answer:**

Do not immediately restart instances or redeploy.

First determine:

- What changed?
- When did the failure begin?
- Is the failure affecting all instances?
- Is the load balancer healthy?
- Is the application process running?
- Are requests reaching the application?
- Is a dependency failing?
- Is the problem configuration-specific?
- Is the problem environment-wide or instance-specific?

A useful first classification is:

| Symptom | Likely layer |
|---|---|
| DNS does not resolve | DNS |
| Connection timeout | Network / security group / load balancer |
| 4xx response | Application / authentication / routing |
| 5xx response | Application / dependency / infrastructure |
| Health turns red | Application / instance / load balancer |
| Deployment fails | Platform / application / IAM / configuration |
| Application starts then exits | Runtime / dependency / configuration |
| Database connection fails | Network / credentials / database |
| High latency | Application / database / external dependency |
| Instances repeatedly replaced | Health checks / startup / resource exhaustion |

### What is the most important troubleshooting principle?

**Answer:**

Separate **symptom** from **root cause**.

For example:

```text
Symptom:
HTTP 502

Possible causes:
- Application process unavailable
- Incorrect application port
- Failed health check
- Web server failure
- Instance startup failure
- Load balancer configuration problem
```

A `502` is evidence about the request path, not necessarily the root cause.

## Elastic Beanstalk Health

### How would you troubleshoot an environment showing Red health?

**Answer:**

Start by determining why the health system considers the environment unhealthy.

Inspect:

1. Environment health status.
2. Recent health events.
3. Instance health.
4. Load balancer health.
5. Application logs.
6. Web server logs.
7. CPU, memory, and disk metrics.
8. Recent deployments or configuration changes.

The important question is:

> Is the environment unhealthy because the application is failing, because instances are failing, or because the health check cannot reach the application?

### What is the difference between environment health and application health?

**Answer:**

Environment health is an operational view of the overall Elastic Beanstalk environment.

Application health is concerned with whether the application itself is functioning correctly.

For example:

```text
Application responds with 500
        |
        v
Load balancer can reach instance
        |
        v
Instance is technically running
        |
        v
Application health degrades
```

An EC2 instance being `running` does not mean the application is healthy.

### Why can an EC2 instance be running while Elastic Beanstalk reports poor health?

**Answer:**

The operating system can be healthy while the application is not.

Possible causes include:

- Application process crashed
- Application port is wrong
- Health endpoint returns an error
- Dependency failure
- Database unavailable
- Memory exhaustion
- Startup failure
- Incorrect environment variables
- Application timeout

Think in layers:

```text
EC2 Running
   !=
Web Server Healthy
   !=
Application Healthy
   !=
Business Logic Healthy
```

### How would you investigate a sudden health degradation?

**Answer:**

Compare the health change with recent events.

Check:

```text
Health degradation
       |
       +--> Deployment?
       |
       +--> Configuration change?
       |
       +--> Platform update?
       |
       +--> Traffic increase?
       |
       +--> Dependency failure?
       |
       +--> Resource exhaustion?
```

Time correlation is extremely valuable during incident investigation.

## HTTP 4xx Errors

### How would you troubleshoot HTTP 400 errors?

**Answer:**

A `400 Bad Request` generally indicates that the server rejected the request because it was malformed or invalid.

Check:

- Request format
- Required parameters
- Content-Type
- Request body
- API validation
- Proxy behavior
- Application logs

For a REST API:

```text
Client
  |
  | Invalid JSON
  v
API
  |
  v
400 Bad Request
```

The exact cause should be confirmed through application logs and request validation.

### How would you troubleshoot HTTP 401 errors?

**Answer:**

Check authentication.

Potential causes include:

- Missing token
- Expired token
- Invalid token
- Incorrect authentication scheme
- Incorrect credentials
- Authentication middleware failure

The first distinction should be:

```text
401 = Authentication problem
403 = Authorization problem
```

### How would you troubleshoot HTTP 403 errors?

**Answer:**

Investigate authorization and access controls.

Possible causes:

- User lacks required permission
- IAM-related access restriction
- Application authorization logic
- CSRF protection
- WAF rule
- Security policy
- Resource-level authorization

Do not assume every `403` comes from IAM.

### How would you troubleshoot HTTP 404 errors?

**Answer:**

Determine which layer generated the response.

Possible sources include:

```text
Load Balancer
      |
      v
Web Server
      |
      v
Application Router
      |
      v
Django / FastAPI Endpoint
```

Check:

- URL path
- HTTP method
- Routing configuration
- Reverse-proxy configuration
- Application routes
- Deployment artifact
- Static files
- Host/path-based routing

## HTTP 5xx Errors

### How would you troubleshoot HTTP 500 errors?

**Answer:**

A `500` generally indicates an application-side failure.

Check:

1. Application logs.
2. Python traceback.
3. Recent deployment.
4. Environment variables.
5. Dependency versions.
6. Database connectivity.
7. External service calls.
8. Runtime exceptions.

For Django or FastAPI, the traceback usually provides the most direct indication of the application failure.

### How would you troubleshoot HTTP 502 errors?

**Answer:**

A `502 Bad Gateway` often means the proxy or load balancer could not obtain a valid response from the backend.

Investigate:

- Application process
- Application port
- Web server
- Reverse-proxy configuration
- Instance health
- Health checks
- Application startup
- Connection resets

Typical flow:

```text
Client
  |
  v
Load Balancer
  |
  X---- Application unavailable
  |
  v
502
```

### How would you troubleshoot HTTP 503 errors?

**Answer:**

A `503 Service Unavailable` indicates that the service cannot currently handle the request.

Possible causes include:

- No healthy instances
- Deployment in progress
- Application unavailable
- Auto Scaling activity
- Load balancer health-check failure
- Resource exhaustion

Check the environment's instance and load-balancer state before changing application configuration.

### How would you troubleshoot HTTP 504 errors?

**Answer:**

A `504 Gateway Timeout` generally indicates that a gateway or proxy did not receive a timely response from the backend.

Investigate:

- Slow application requests
- Database queries
- External API calls
- Network connectivity
- Connection pools
- Application timeouts
- Load balancer timeout configuration

A useful diagnostic question is:

> Is the application slow, or is the application unreachable?

## Application Startup Failures

### The application deploys successfully but immediately crashes. What do you check?

**Answer:**

Check the startup path.

```text
Deployment
   |
   v
Instance Provisioned
   |
   v
Dependencies Installed
   |
   v
Application Started
   |
   X
Startup Failure
```

Common causes:

- Missing environment variable
- Incorrect start command
- Missing dependency
- Python import error
- Database initialization failure
- Incorrect working directory
- Incorrect WSGI/ASGI configuration
- Runtime version mismatch
- File permission problem

Inspect deployment and application logs first.

### A Django application fails with `ModuleNotFoundError`. What would you investigate?

**Answer:**

Check:

- `requirements.txt`
- Deployment artifact
- Virtual environment
- Python runtime
- Working directory
- `PYTHONPATH`
- Application startup command
- Project structure

For example, if the application expects:

```text
project/
├── manage.py
├── config/
│   ├── settings.py
│   └── wsgi.py
└── requirements.txt
```

the WSGI configuration must point to the correct module.

A common failure is deploying the correct files but configuring the application server to import the wrong module.

### A FastAPI application starts locally but fails in Elastic Beanstalk. What could cause this?

**Answer:**

Investigate differences between local and production environments.

Possible causes:

- Python runtime mismatch
- Missing dependencies
- Incorrect start command
- Incorrect port
- Missing environment variables
- Incorrect working directory
- ASGI server configuration
- Network dependency failures

Local success proves only that the local environment works.

## Port and Process Problems

### How would you troubleshoot an application that is running but unreachable?

**Answer:**

Follow the request path:

```text
Client
  |
  v
Load Balancer
  |
  v
Security Group
  |
  v
EC2
  |
  v
Web Server
  |
  v
Application Process
  |
  v
Application Port
```

Check each layer.

Verify:

- Application process exists.
- Application listens on the expected interface.
- Correct port is configured.
- Web server forwards to the correct port.
- Security groups allow required traffic.
- Load balancer health checks succeed.

### Why can binding an application to `127.0.0.1` cause problems?

**Answer:**

`127.0.0.1` means the process listens only on the local loopback interface.

A reverse proxy or load balancer may need to reach the application through the instance network interface.

For example:

```text
127.0.0.1
   |
   X
External network cannot directly reach it
```

The correct binding depends on the Elastic Beanstalk platform and proxy configuration.

### How do you determine whether the application process is running?

**Answer:**

Inspect the running processes on the instance and correlate them with application and web-server logs.

Typical investigation:

```text
Process exists?
      |
      +--> No --> Startup / crash investigation
      |
      +--> Yes
             |
             v
Listening on expected port?
             |
             +--> No --> Configuration / startup investigation
             |
             +--> Yes
                    |
                    v
              Test locally
```

## Deployment Failures

### A deployment fails. What should you check first?

**Answer:**

Determine the deployment phase that failed.

Possible phases include:

```text
Upload Artifact
      |
      v
Instance Deployment
      |
      v
Dependency Installation
      |
      v
Application Startup
      |
      v
Health Verification
```

A deployment can fail after the application has been copied successfully.

### How would you troubleshoot a failed deployment caused by dependency installation?

**Answer:**

Check:

- Dependency file
- Package versions
- Python version
- Native system dependencies
- Package repository availability
- Build logs
- Platform compatibility

Python packages with native extensions can fail when required system libraries or compilers are unavailable.

### Why can a package work locally but fail in Elastic Beanstalk?

**Answer:**

The local machine may have system-level dependencies that are absent from the Elastic Beanstalk platform.

For example:

```text
Local Machine
Python Package
   +
System Library
   +
Compiler
   |
   v
Works

Elastic Beanstalk
Python Package
   +
Missing System Library
   |
   v
Build Failure
```

Production dependencies must be explicitly identified and supported by the selected platform.

### How would you troubleshoot a deployment that succeeds but the application is unhealthy afterward?

**Answer:**

Separate deployment success from runtime success.

```text
Deployment Completed
        |
        X
Application Unhealthy
```

Check:

- Startup logs
- Health checks
- Environment variables
- Application port
- Database connectivity
- Runtime compatibility
- Application exceptions
- Recent configuration changes

The artifact can be deployed successfully while the application itself fails at runtime.

## Configuration Problems

### An application works in staging but fails in production. What would you compare?

**Answer:**

Compare configuration systematically.

| Area | Staging | Production |
|---|---|---|
| Runtime | | |
| Environment variables | | |
| IAM role | | |
| Security groups | | |
| Subnets | | |
| Database endpoint | | |
| Database credentials | | |
| Redis endpoint | | |
| External APIs | | |
| Application settings | | |
| Platform version | | |
| Dependency versions | | |

Avoid assuming the application code is the only difference.

### How would you troubleshoot a missing environment variable?

**Answer:**

First determine whether the application expects the variable.

For example:

```python
import os

database_url = os.environ["DATABASE_URL"]
```

If `DATABASE_URL` is missing, startup may fail immediately.

Check:

- Elastic Beanstalk environment configuration
- Deployment configuration
- Variable name spelling
- Environment-specific configuration
- Secret retrieval mechanism
- Application startup logs

Avoid printing secret values while debugging.

### What is a dangerous configuration mistake during troubleshooting?

**Answer:**

Disabling security controls simply to make the application work.

Examples:

- Making RDS public
- Opening `0.0.0.0/0`
- Disabling authentication
- Turning off TLS
- Granting AdministratorAccess
- Making S3 buckets public

A temporary debugging change can become a permanent security vulnerability.

## Database Connectivity

### The application cannot connect to PostgreSQL. How would you troubleshoot it?

**Answer:**

Use a layered approach:

```text
Application
    |
    v
DNS Resolution
    |
    v
Network Route
    |
    v
Security Group
    |
    v
RDS
    |
    v
Authentication
    |
    v
Database
```

Check:

1. Database endpoint.
2. DNS resolution.
3. VPC/subnet routing.
4. Security-group rules.
5. Database port.
6. Credentials.
7. Database availability.
8. SSL requirements.
9. Connection limits.

### How would you distinguish a network failure from an authentication failure?

**Answer:**

A network failure usually prevents establishing the connection.

An authentication failure means the database was reached but rejected the credentials or authentication method.

Conceptually:

```text
Cannot establish connection
        |
        v
Network / DNS / routing / SG

Connection established
        |
        v
Authentication rejected
        |
        v
Credentials / database authorization
```

This distinction significantly narrows the investigation.

### The application suddenly receives PostgreSQL connection timeout errors. What do you check?

**Answer:**

Check:

- RDS availability
- Security groups
- Network routes
- DNS
- Subnet configuration
- Connection count
- Application connection pool
- Database resource utilization
- Recent infrastructure changes

A timeout is different from an immediate authentication error.

### The database connection limit is exhausted. What would you investigate?

**Answer:**

Look at:

- Number of Elastic Beanstalk instances
- Application worker count
- Database connection pool size
- Long-running queries
- Connection leaks
- Idle connections
- Auto Scaling events

A common scaling problem is:

```text
Instances
   x
Workers per instance
   x
Connections per worker
   =
Potential DB connections
```

Adding application instances can therefore make a database connection problem worse.

## Performance Problems

### Users report that the application became slow. How would you investigate?

**Answer:**

Do not immediately increase instance size.

Start with:

```text
Latency
  |
  +--> CPU?
  +--> Memory?
  +--> Database?
  +--> External API?
  +--> Network?
  +--> Application code?
  +--> Garbage collection?
  +--> Connection pool?
```

Compare:

- Request latency
- Throughput
- Error rate
- CPU
- Memory
- Database latency
- External dependency latency
- Recent deployments

### CPU usage is consistently high. What could cause it?

**Answer:**

Possible causes include:

- Increased traffic
- CPU-intensive application code
- Serialization overhead
- Encryption/compression work
- Excessive logging
- Inefficient algorithms
- Background tasks
- Memory pressure causing additional CPU activity

Determine whether the problem is load-related or code-related.

### Memory usage keeps increasing. What could be happening?

**Answer:**

Possible causes include:

- Memory leak
- Unbounded in-memory caching
- Large request payloads
- Excessive worker count
- Large query results
- Background task accumulation
- Application objects retained unexpectedly

A common symptom is:

```text
Memory
  |
  |       /\
  |      /  \
  |     /    \
  |____/      \____
             Restart
```

If memory repeatedly grows until the process or instance is restarted, investigate application-level retention rather than treating restarts as the fix.

### How would you troubleshoot high response latency?

**Answer:**

Break the request into components.

```text
Request
  |
  +--> Load Balancer
  |
  +--> Application
  |      |
  |      +--> Database
  |      |
  |      +--> Redis
  |      |
  |      +--> External API
  |
  +--> Response
```

Measure each dependency rather than looking only at total latency.

For example:

```text
Total = 900 ms

Database = 600 ms
External API = 200 ms
Application = 100 ms
```

The application code itself may not be the primary bottleneck.

## Auto Scaling Problems

### Instances keep scaling out unexpectedly. What would you investigate?

**Answer:**

Check:

- Scaling policies
- CPU utilization
- Request count
- Network traffic
- Queue depth where applicable
- Health failures
- Traffic spikes
- Deployment activity

Determine whether scaling is responding correctly to actual workload.

### Why can Auto Scaling make a database problem worse?

**Answer:**

More application instances can create more concurrent database connections.

```text
2 Instances
   |
   v
20 DB connections

10 Instances
   |
   v
100+ DB connections
```

If the database has a finite connection capacity, horizontal application scaling can exhaust it.

### Instances are repeatedly terminated and replaced. What could cause this?

**Answer:**

Possible causes include:

- Failed health checks
- Application startup failure
- Instance-level resource exhaustion
- Failed deployments
- Auto Scaling policies
- Platform issues
- Underlying instance failures

Look at environment events and health information before assuming EC2 itself is defective.

## Load Balancer and Health Checks

### The load balancer reports instances as unhealthy. How do you troubleshoot it?

**Answer:**

Check:

- Health-check path
- Health-check port
- Expected response code
- Security groups
- Application process
- Application startup
- Application response time

For example:

```text
ALB
 |
 | GET /health
 v
Application
 |
 +--> 200 = Healthy
 |
 +--> 500 = Unhealthy
 |
 +--> Timeout = Unhealthy
```

### Why should health-check endpoints be lightweight?

**Answer:**

Health checks execute frequently.

A health endpoint should avoid expensive operations such as:

- Large database queries
- Complex business logic
- External API calls
- Heavy computation

A common pattern is to distinguish:

```text
/health/live
/health/ready
```

A liveness check answers whether the process is alive.

A readiness check answers whether the application is capable of serving traffic.

The exact implementation should match the application's architecture.

### What happens if the health endpoint depends on an external API?

**Answer:**

A temporary external dependency failure can make otherwise healthy application instances appear unhealthy.

For example:

```text
Health Check
     |
     v
Application
     |
     v
External API
     |
     X
Failure
     |
     v
Instance marked unhealthy
```

This can cause unnecessary instance replacement or traffic removal.

Health checks should represent the application's ability to serve traffic without creating unnecessary coupling to non-critical dependencies.

## Logging Troubleshooting

### Where should you look when an Elastic Beanstalk deployment fails?

**Answer:**

Start with Elastic Beanstalk deployment and environment logs, then inspect application and web-server logs as appropriate.

A useful hierarchy is:

```text
Environment Events
       |
       v
Deployment Logs
       |
       v
Application Logs
       |
       v
Web Server Logs
       |
       v
System Logs
```

The exact log location depends on the platform and configuration.

### What is the difference between application logs and web-server logs?

**Answer:**

Application logs describe application behavior.

Examples:

```text
Python traceback
Database exception
Business logic error
```

Web-server logs describe HTTP/proxy behavior.

Examples:

```text
Request received
Response status
Upstream connection failure
Request timeout
```

You often need both to diagnose a `502` or `504`.

### How should you troubleshoot missing logs?

**Answer:**

Check:

- Whether the application is actually writing logs.
- Logging configuration.
- Log destinations.
- File permissions.
- Elastic Beanstalk log collection.
- CloudWatch integration.
- Instance state.
- Log rotation.

Do not assume that "no logs" means "no error."

## IAM and Permission Failures

### The application suddenly receives `AccessDenied`. How do you troubleshoot it?

**Answer:**

Identify:

1. Which AWS API call failed.
2. Which IAM identity made the call.
3. Which resource was accessed.
4. Which policy should authorize the operation.
5. Whether an explicit deny exists.

Conceptually:

```text
Application
    |
    v
IAM Role
    |
    v
AWS API
    |
    X
AccessDenied
```

Check both identity-based and resource-based policies where applicable.

### How would you troubleshoot an S3 `AccessDenied` error?

**Answer:**

Check:

- EC2 instance profile
- IAM policy
- S3 bucket policy
- Object ownership/access model
- Resource ARN
- Region
- Explicit denies
- Encryption/KMS permissions where applicable

A common mistake is checking only the IAM role and ignoring the bucket policy or KMS permissions.

### Why might an application have S3 permission but still fail to retrieve an encrypted object?

**Answer:**

If the object uses a KMS key, the application may require appropriate KMS permissions in addition to S3 permissions.

Conceptually:

```text
GetObject
   |
   +--> S3 authorization
   |
   +--> KMS authorization
```

Both layers can affect the final operation.

## DNS Problems

### The application cannot resolve an RDS hostname. What would you check?

**Answer:**

Check:

- VPC DNS settings
- Route configuration
- Resolver behavior
- Subnet configuration
- Correct database endpoint
- Security and network configuration

Distinguish DNS failure from TCP connectivity failure.

```text
Hostname
   |
   v
DNS Resolution
   |
   +--> Failure
   |
   +--> IP Address
          |
          v
       TCP Connection
```

### The application resolves the hostname but cannot connect. What does that indicate?

**Answer:**

DNS is probably functioning, so investigate the network path.

Check:

- Security groups
- Network ACLs where relevant
- Routes
- Subnets
- Ports
- Service availability

This distinction prevents wasting time investigating DNS when the actual problem is network access.

## Redis and External Dependencies

### The application cannot connect to Redis. How would you troubleshoot it?

**Answer:**

Use the same layered approach:

```text
Application
    |
    v
Redis hostname resolution
    |
    v
Network routing
    |
    v
Security group
    |
    v
Redis port
    |
    v
Authentication / TLS
    |
    v
Redis
```

Check the Redis endpoint, port, security groups, authentication, TLS requirements, and network placement.

### How can Redis failure affect a Django application?

**Answer:**

It depends on how Redis is used.

If Redis is only a cache:

```text
Redis Failure
     |
     v
Cache Misses
     |
     v
Database Load Increases
```

If Redis is also used for:

- Sessions
- Celery broker
- Distributed locks
- Rate limiting

then the impact can be much larger.

A senior engineer should understand the role of each dependency before deciding whether it is safe to degrade gracefully.

## Deployment Rollback

### A deployment causes errors immediately after release. What would you do?

**Answer:**

First determine whether rollback is safer than debugging in production.

If the failure is clearly associated with the deployment:

```text
Previous Version
      |
      v
Healthy

New Version
      |
      v
Errors
```

rollback may be the fastest way to restore service.

Then investigate the root cause separately.

### Should you always roll back a failed deployment?

**Answer:**

No.

Rollback depends on:

- Severity
- Data compatibility
- Migration state
- Dependency changes
- Backward compatibility
- Availability of the previous artifact

Database migrations are particularly important.

For example:

```text
Application v1
     |
     v
Database Schema v1

Deploy v2
     |
     v
Database Schema v2
```

If v2 requires irreversible schema changes, simply deploying v1 again may not restore compatibility.

### What is the risk of incompatible database migrations?

**Answer:**

A deployment can create a state where the old application cannot operate against the new schema.

Prefer backward-compatible migration strategies.

For example:

```text
Add new column
      |
      v
Deploy code using both schemas
      |
      v
Backfill data
      |
      v
Remove old column later
```

This reduces rollback risk.

## Configuration Rollback

### A configuration change breaks the application. What should you do?

**Answer:**

Identify the exact configuration change and revert it if safe.

Configuration should be treated like code:

```text
Configuration Change
        |
        v
Validation
        |
        v
Deployment
        |
        v
Health Verification
```

Avoid manually changing unrelated settings during the incident.

### Why is configuration drift dangerous?

**Answer:**

If production differs from the expected configuration, reproducing and troubleshooting problems becomes difficult.

```text
Git / Desired State
        |
        X
Production State
```

The larger the difference, the harder it is to determine what actually runs in production.

## Resource Exhaustion

### Disk usage reaches 100%. What happens?

**Answer:**

Potential consequences include:

- Application writes failing
- Log writes failing
- Temporary file failures
- Package installation failures
- Database-related local operations failing
- Instance health degradation

Investigate:

- Application-generated files
- Logs
- Temporary files
- Core dumps
- Disk growth
- Rotation configuration

### How would you troubleshoot high disk usage?

**Answer:**

Identify which directories or files consume the space.

Typical causes include:

- Unrotated logs
- Uploaded files
- Temporary files
- Application-generated artifacts
- Crash dumps
- Large caches

Do not blindly delete files from production without understanding their purpose.

### What happens if memory is exhausted?

**Answer:**

The operating system may terminate processes or the application may become unstable.

Symptoms can include:

- Worker crashes
- Request failures
- Instance health degradation
- Restart loops
- Increased latency

Check memory metrics and application behavior rather than simply increasing instance size.

## Security-Related Troubleshooting

### The application suddenly receives a large number of suspicious requests. What would you investigate?

**Answer:**

Investigate:

- Source patterns
- Request paths
- User agents
- Request rates
- Authentication failures
- WAF events
- Application logs
- Error rates
- Resource utilization

Determine whether the traffic is:

- Legitimate traffic spike
- Bot activity
- Brute-force attack
- Vulnerability scanning
- Application-layer abuse

### What should you avoid doing during a security incident?

**Answer:**

Avoid making broad emergency changes such as:

- Opening all ports
- Disabling authentication
- Making databases public
- Granting AdministratorAccess
- Disabling TLS
- Removing security-group restrictions

Emergency troubleshooting must preserve security controls wherever possible.

## Incident Scenarios

### Scenario: The API suddenly returns 502 errors.

**Answer:**

Investigate in this order:

```text
502
 |
 +--> Are instances healthy?
 |
 +--> Is the application process running?
 |
 +--> Is the expected port listening?
 |
 +--> Is the web server healthy?
 |
 +--> Can the proxy reach the application?
 |
 +--> Did a deployment occur?
 |
 +--> Did configuration change?
```

Inspect load-balancer and web-server logs together with application logs.

### Scenario: Every request returns 503 after deployment.

**Answer:**

Likely areas include:

- No healthy instances
- Application startup failure
- Failed health checks
- Incorrect port
- Missing environment variables
- Deployment incompatibility

Check environment health and instance-level logs first.

### Scenario: The application works but database requests time out.

**Answer:**

Check:

1. RDS availability.
2. DNS.
3. Security groups.
4. Network routes.
5. Database port.
6. Connection count.
7. Database resource utilization.
8. Application connection pool.

A timeout strongly suggests investigating connectivity before application SQL syntax.

### Scenario: Application latency doubled after a traffic increase.

**Answer:**

Determine whether the bottleneck is:

```text
Traffic Increase
      |
      +--> CPU saturation
      |
      +--> Memory pressure
      |
      +--> DB saturation
      |
      +--> Connection exhaustion
      |
      +--> External API saturation
      |
      +--> Application bottleneck
```

Check metrics before scaling.

If CPU is low but database latency is high, adding more application instances may increase database pressure without solving the root cause.

### Scenario: Instances continuously become unhealthy and are replaced.

**Answer:**

Investigate:

- Health-check path
- Health-check response
- Application startup
- Application crashes
- Resource exhaustion
- Deployment failures
- Dependency availability

The key question is:

> Why is the instance failing the health criteria?

### Scenario: A deployment works in one environment but fails in another.

**Answer:**

Compare:

- Platform versions
- Python versions
- Dependencies
- Environment variables
- IAM roles
- Security groups
- Network topology
- Database configuration
- External dependencies

Avoid changing production blindly until the environmental difference is identified.

## Production Troubleshooting Principles

### Why should recent changes be investigated first?

Most incidents correlate strongly with a recent change:

- Application deployment
- Configuration change
- Platform update
- IAM change
- Security-group modification
- Database migration
- Dependency upgrade

A useful incident timeline is:

```text
Healthy
   |
   | Change
   v
Degraded
   |
   v
Failure
```

If the timing aligns, investigate the change before unrelated infrastructure.

### Why should you change one thing at a time during troubleshooting?

**Answer:**

Changing multiple variables destroys causal information.

For example:

```text
Change IAM
Change Security Group
Change Database
Change Application
Restart Instances
```

If the system recovers, you do not know which change fixed the issue.

Prefer:

```text
Hypothesis
   |
   v
Small Change
   |
   v
Observe
   |
   v
Confirm / Reject
```

### Why are logs and metrics both necessary?

**Answer:**

Metrics show **what is happening**.

Logs often explain **why it is happening**.

For example:

```text
Metric:
Latency increased from 200 ms to 2 s

Logs:
Database query timeout
```

Neither source should be treated as sufficient for every incident.

### Why should production troubleshooting be hypothesis-driven?

**Answer:**

A hypothesis narrows the investigation.

Instead of:

> Something is wrong with Elastic Beanstalk.

Use:

> The application is probably failing health checks because the deployment changed the application port.

Then verify that hypothesis through:

- Health events
- Configuration
- Process state
- Logs
- Network behavior

This reduces random configuration changes.

## Common Troubleshooting Mistakes

| Mistake | Why it is dangerous | Better approach |
|---|---|---|
| Restarting everything immediately | Destroys useful evidence | Inspect first |
| Rebuilding instances without investigation | Can hide the root cause | Identify failure mechanism |
| Opening all security-group ports | Creates security exposure | Allow only required traffic |
| Granting AdministratorAccess | Increases blast radius | Fix specific IAM permission |
| Making RDS public | Creates unnecessary exposure | Keep database private |
| Increasing instance size immediately | May hide application defects | Identify bottleneck |
| Blaming Elastic Beanstalk for application errors | Wrong troubleshooting layer | Trace request path |
| Ignoring recent deployments | Misses common root cause | Build incident timeline |
| Changing many settings simultaneously | Removes causal evidence | Change one variable at a time |
| Deleting logs | Destroys forensic evidence | Preserve evidence |
| Ignoring database connections | Scaling can amplify DB pressure | Calculate connection capacity |
| Disabling health checks | Hides failures | Fix health-check cause |
| Logging secrets for debugging | Creates credential exposure | Redact sensitive values |
| Treating rollback as universally safe | Schema changes may be incompatible | Check data compatibility |
| Debugging only from the application layer | Infrastructure may be failing | Trace all layers |
| Assuming no logs means no error | Logging may itself be broken | Verify log pipeline |

## Interview Traps

### Is an Elastic Beanstalk deployment failure always an application-code problem?

**Answer:**

No.

It can result from:

- Application code
- Dependencies
- Platform version
- IAM
- Networking
- Environment variables
- Deployment configuration
- Resource exhaustion

### If an EC2 instance is running, should the application be considered healthy?

**Answer:**

No.

EC2 instance state only confirms that the instance is running.

The application can still be:

- Crashed
- Unresponsive
- Listening on the wrong port
- Failing health checks
- Returning HTTP 5xx responses

### If increasing instance size fixes the problem, was the root cause CPU?

**Answer:**

Not necessarily.

The larger instance may have masked:

- Memory pressure
- Worker exhaustion
- Connection limits
- Application inefficiency
- Traffic-related saturation

Always determine why the previous instance size was insufficient.

### If restarting an instance fixes the problem, what does that prove?

**Answer:**

Only that restarting temporarily changed the system state.

It does not prove that the restart was the root-cause fix.

Investigate:

- Memory leaks
- Resource exhaustion
- Process deadlocks
- Connection leaks
- Temporary dependency failures
- Kernel or platform issues

### Is a 502 always caused by the load balancer?

**Answer:**

No.

The load balancer may only be reporting that it could not obtain a valid response from the backend.

The actual problem may be:

- Application crash
- Incorrect port
- Web-server failure
- Connection reset
- Health-check failure
- Instance problem

### Is a 504 always a database timeout?

**Answer:**

No.

A `504` indicates a gateway timeout, but the slow component could be:

- Application code
- Database
- Redis
- External API
- Network
- Another downstream service

Measure each dependency.

## Key Takeaways

- Troubleshoot Elastic Beanstalk from the outside in: DNS, load balancer, network, instance, web server, application, and dependencies.
- Start with symptoms and environment health, then identify the failing layer.
- Always correlate incidents with recent deployments, configuration changes, platform updates, and infrastructure changes.
- A running EC2 instance does not mean the application is healthy.
- A `502` generally indicates a problem obtaining a valid backend response, while a `504` indicates a timeout somewhere in the request path.
- A `500` usually requires application-level investigation, including logs and stack traces.
- Deployment success does not guarantee runtime success.
- Configuration differences between environments are a common source of production failures.
- Database troubleshooting should distinguish DNS, network, security-group, authentication, connection-pool, and database-capacity failures.
- Horizontal application scaling can increase database connection pressure.
- High latency should be decomposed into application, database, cache, network, and external-service latency.
- Health checks should be lightweight and should not unnecessarily depend on fragile external services.
- Application logs explain behavior; metrics reveal system-level trends and saturation.
- Do not restart or replace instances before collecting useful evidence unless immediate mitigation is required.
- Do not use broad security changes as a debugging shortcut.
- Never grant AdministratorAccess simply to resolve an `AccessDenied` error.
- Rollbacks must consider database-schema compatibility and backward compatibility.
- Production troubleshooting should be hypothesis-driven rather than based on random configuration changes.
- Change one variable at a time when practical so that cause and effect remain observable.
- The best troubleshooting answer identifies both the immediate mitigation and the underlying root cause.