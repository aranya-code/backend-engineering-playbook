# 03- Connecting to a Database

## Overview

Connecting to PostgreSQL from the CLI means establishing a client session between `psql` and a specific PostgreSQL server and database.

The connection itself involves several layers:

```text
Terminal
   ↓
psql
   ↓
DNS / Network
   ↓
TCP
   ↓
TLS, if enabled
   ↓
PostgreSQL authentication
   ↓
Database authorization
   ↓
PostgreSQL session
```

For backend engineers, understanding database connectivity is important because the same concepts appear in application connections:

```text
Django / FastAPI
      ↓
psycopg / SQLAlchemy
      ↓
TCP/TLS
      ↓
PostgreSQL
```

A large class of production failures are connection failures rather than SQL failures:

- DNS resolution problems
- Network reachability
- Security groups
- Kubernetes networking
- Incorrect ports
- Authentication failures
- TLS certificate problems
- Database selection errors
- Connection exhaustion
- Pool exhaustion
- Replica/primary confusion

The CLI provides a controlled way to isolate these problems.

---

## Connection Architecture

A typical production connection looks like:

```mermaid
flowchart LR
    Engineer[Engineer] --> PSQL[psql]
    PSQL --> DNS[DNS]
    DNS --> Network[Private Network]
    Network --> TLS[TLS]
    TLS --> PG[PostgreSQL]
    PG --> Auth[Authentication]
    Auth --> Session[Database Session]
```

For an application:

```mermaid
flowchart LR
    API[Django / FastAPI] --> Pool[Connection Pool]
    Pool --> Driver[psycopg / SQLAlchemy]
    Driver --> DNS[DNS]
    DNS --> Network[VPC / Private Network]
    Network --> TLS[TLS]
    TLS --> PG[(PostgreSQL)]
```

The important distinction is that `psql` is a **client connection**, while an application may maintain many connections through a pool.

---

## What a PostgreSQL Connection Contains

A PostgreSQL connection establishes a session associated with:

```text
Host
Port
Database
Role
Authentication method
Session settings
Transaction state
```

Once connected, PostgreSQL creates a backend session for the client.

The session can then execute:

```sql
SELECT current_user;
```

```sql
SELECT current_database();
```

```sql
SHOW server_version;
```

The connection therefore establishes more than network connectivity. It establishes a database session with a specific security and execution context.

---

## Connection Parameters

The most important `psql` parameters are:

| Parameter | CLI option | Purpose |
|---|---|---|
| Host | `-h` | PostgreSQL server hostname or address |
| Port | `-p` | PostgreSQL TCP port |
| User | `-U` | PostgreSQL role |
| Database | `-d` | Database to connect to |
| Password | `-W` | Prompt for password |
| Command | `-c` | Execute SQL and exit |
| File | `-f` | Execute SQL file |

Example:

```bash
psql \
  -h db.internal.example.com \
  -p 5432 \
  -U app_readonly \
  -d orders
```

---

## Host

The host identifies the PostgreSQL server endpoint.

Example:

```bash
psql -h db.internal.example.com -d orders
```

The hostname may represent:

```text
PostgreSQL server
Load-balanced endpoint
RDS endpoint
Database proxy
Kubernetes Service
Internal DNS record
```

Do not assume the hostname directly identifies a physical database node.

In high-availability environments, a stable endpoint may redirect clients to the current primary.

---

## Port

PostgreSQL commonly listens on:

```text
5432
```

Example:

```bash
psql -h db.internal.example.com -p 5432 -d orders
```

The port is configurable.

A connection failure can therefore result from:

```text
Wrong port
Firewall
Security group
Network policy
PostgreSQL not listening
Load balancer configuration
```

Do not diagnose every connection failure as an authentication problem.

---

## User

The `-U` option selects the PostgreSQL role:

```bash
psql \
  -h db.internal \
  -U app_readonly \
  -d orders
```

The role determines the database session's privileges.

For production investigation, prefer a dedicated read-only role where possible.

Avoid using:

```text
postgres
```

or another highly privileged role for routine application investigation.

---

## Database

The `-d` option selects the database:

```bash
psql -h db.internal -U app_readonly -d orders
```

The role may be allowed to connect to multiple databases.

The connection itself, however, is established against one specific database.

Verify the current database after connecting:

```sql
SELECT current_database();
```

or:

```text
\conninfo
```

---

## The PostgreSQL Connection Lifecycle

Conceptually:

```text
psql starts
   ↓
Resolve hostname
   ↓
Establish TCP connection
   ↓
Negotiate TLS if configured
   ↓
PostgreSQL startup message
   ↓
Authentication
   ↓
Database connection authorization
   ↓
Session initialization
   ↓
Ready for queries
```

The exact protocol details are handled by `libpq`, the PostgreSQL client library used by `psql`.

---

## DNS Resolution

When connecting to:

```bash
psql -h db.internal.example.com -d orders
```

the client may first resolve:

```text
db.internal.example.com
        ↓
IP address
```

For troubleshooting:

```bash
nslookup db.internal.example.com
```

or:

```bash
dig db.internal.example.com
```

DNS resolution problems occur before PostgreSQL authentication.

This distinction is useful when debugging:

```text
Could not resolve host
```

versus:

```text
password authentication failed
```

---

## TCP Connectivity

PostgreSQL normally communicates over TCP.

A basic connectivity test can use:

```bash
nc -vz db.internal.example.com 5432
```

or:

```bash
telnet db.internal.example.com 5432
```

where available.

A successful TCP connection only proves network reachability.

It does **not** prove:

```text
PostgreSQL authentication
Database authorization
Correct database
Correct role
TLS configuration
```

---

## Connection Testing Layers

A useful diagnostic model is:

```text
DNS
 ↓
TCP
 ↓
TLS
 ↓
PostgreSQL authentication
 ↓
Database authorization
 ↓
SQL execution
```

Test from the bottom upward.

For example:

| Layer | Example failure |
|---|---|
| DNS | Host cannot be resolved |
| TCP | Connection refused / timeout |
| TLS | Certificate validation failure |
| Authentication | Password authentication failed |
| Authorization | Permission denied |
| SQL | Query or schema error |

This prevents jumping directly to SQL debugging when the database session was never established correctly.

---

## TLS Connections

Remote production PostgreSQL connections should generally use TLS where required by the security architecture.

Example:

```bash
psql \
  "host=db.internal port=5432 dbname=orders user=app_readonly sslmode=require"
```

For stronger certificate and hostname verification:

```bash
psql \
  "host=db.internal port=5432 dbname=orders user=app_readonly sslmode=verify-full"
```

The exact certificate configuration depends on the PostgreSQL deployment and certificate authority.

---

## `sslmode`

Common PostgreSQL SSL modes include:

| Mode | General behavior |
|---|---|
| `disable` | Do not use TLS |
| `allow` | Prefer non-TLS, fall back to TLS |
| `prefer` | Prefer TLS, fall back to non-TLS |
| `require` | Require TLS |
| `verify-ca` | Require TLS and verify CA |
| `verify-full` | Require TLS, verify CA and hostname |

For production systems where certificate validation is required, `verify-full` is generally the stronger client configuration.

`require` provides encryption but does not provide the same server identity verification as `verify-full`.

---

## Certificate Verification

With:

```text
sslmode=verify-full
```

the client verifies both:

```text
Certificate chain
+
Server hostname
```

This helps prevent connecting securely to the wrong endpoint.

TLS security therefore involves:

```text
Encryption
+
Authentication of the server
```

not encryption alone.

---

## Authentication

After network and TLS setup, PostgreSQL authenticates the client.

Authentication may involve:

```text
Password
SCRAM
Certificate
GSSAPI
Peer authentication
Other configured mechanisms
```

The exact mechanism depends on PostgreSQL configuration, especially `pg_hba.conf`.

Authentication answers:

```text
Who is this client?
```

Authorization answers:

```text
What can this role do?
```

---

## `pg_hba.conf`

PostgreSQL uses `pg_hba.conf` to control client authentication rules.

Conceptually:

```text
Connection
   ↓
Match pg_hba.conf rule
   ↓
Authentication method
   ↓
Role verification
   ↓
Database access
```

A rule may consider:

```text
Connection type
Client address
Database
User
Authentication method
```

For example, a deployment may require SCRAM authentication for application connections.

The exact configuration belongs to the PostgreSQL server and should be managed carefully.

---

## Peer Authentication

Local PostgreSQL installations may use peer authentication.

Conceptually:

```text
Operating-system user
        ↓
PostgreSQL local connection
        ↓
Matching database role
```

This can explain why:

```bash
psql
```

works locally while:

```bash
psql -h localhost
```

behaves differently.

The second command may use TCP and therefore match a different `pg_hba.conf` rule.

---

## Password Authentication

A password-authenticated connection may look like:

```bash
psql \
  -h db.internal \
  -U app_readonly \
  -d orders \
  -W
```

PostgreSQL's authentication configuration determines the actual password mechanism.

Modern PostgreSQL deployments commonly use SCRAM rather than older MD5-based password authentication.

---

## Database Connection Authorization

Successful authentication is not always sufficient.

The role also needs permission to connect to the requested database.

For example:

```sql
GRANT CONNECT
ON DATABASE orders
TO app_readonly;
```

Therefore:

```text
Valid credentials
    +
CONNECT privilege
    ↓
Database session
```

A role can exist and authenticate successfully but still be unable to connect to a particular database.

---

## Schema Authorization

After connecting, the role may still lack schema access.

For example:

```sql
GRANT USAGE
ON SCHEMA app
TO app_readonly;
```

Without appropriate schema privileges, table access may fail even though the connection itself succeeds.

This creates an important troubleshooting distinction:

```text
Connection failure
vs
Schema authorization failure
```

---

## Table Authorization

The role may also need table privileges:

```sql
GRANT SELECT
ON app.orders
TO app_readonly;
```

A complete access path can therefore look like:

```text
Connect to database
        ↓
USAGE on schema
        ↓
SELECT on table
        ↓
Optional RLS policy
        ↓
Rows accessible
```

---

## Verifying the Session

After connecting:

```text
\conninfo
```

Then:

```sql
SELECT
    current_database(),
    current_user,
    session_user,
    inet_server_addr(),
    inet_server_port();
```

For replica-aware environments:

```sql
SELECT pg_is_in_recovery();
```

This provides useful operational context before running queries.

---

## `current_user` vs `session_user`

These values can differ.

```sql
SELECT
    session_user,
    current_user;
```

Conceptually:

```text
session_user
    ↓
Identity that established the session

current_user
    ↓
Effective role for authorization
```

`SET ROLE` can change the effective `current_user`.

This distinction matters when investigating PostgreSQL permissions.

---

## Checking Server Identity

A useful operational query is:

```sql
SELECT
    current_database() AS database,
    current_user AS current_user,
    session_user,
    inet_server_addr() AS server_ip,
    inet_server_port() AS server_port,
    pg_is_in_recovery() AS is_replica;
```

This can be saved as a standard diagnostic query.

---

## Connecting Through a PostgreSQL Endpoint

A production application may use:

```text
db.internal.example.com
```

instead of directly targeting:

```text
10.0.12.42
```

The endpoint may represent:

```text
Primary database
Database proxy
HA endpoint
Load balancer
Managed database service
```

Prefer the documented stable endpoint rather than bypassing it unless the operational procedure specifically requires node-level access.

---

## Primary vs Replica

In a replicated system:

```text
                +--> Replica A
                |
Application --> Primary
                |
                +--> Replica B
```

A CLI session may accidentally connect to a replica.

Check:

```sql
SELECT pg_is_in_recovery();
```

Results:

```text
false → primary
true  → standby/recovery
```

This is critical before performing a mutation.

---

## Replica Read Consistency

Replicas can lag behind the primary:

```text
Primary
  ↓
WAL generation
  ↓
Replication
  ↓
Replay
  ↓
Replica query
```

Therefore:

```text
Primary write
    ↓
Immediate replica query
    ↓
May not see the write yet
```

When investigating a data discrepancy, always identify the server you are connected to.

---

## Connecting to Amazon RDS PostgreSQL

A managed PostgreSQL service typically provides a DNS endpoint.

Example:

```bash
psql \
  -h orders-db.example.region.rds.amazonaws.com \
  -p 5432 \
  -U app_readonly \
  -d orders
```

The actual endpoint, credentials, networking, and TLS requirements depend on the AWS environment.

Typical architecture:

```text
Engineer
   ↓
Approved access path
   ↓
VPC
   ↓
RDS PostgreSQL
```

RDS security groups and network routing determine reachability before PostgreSQL authentication occurs.

---

## AWS Connectivity Layers

A connection to RDS may require:

```text
DNS resolution
    ↓
VPC routing
    ↓
Security Group
    ↓
Network ACL where applicable
    ↓
TCP 5432
    ↓
TLS
    ↓
PostgreSQL authentication
    ↓
Database authorization
```

A PostgreSQL password cannot solve a security-group problem.

Likewise, a correct security group cannot solve invalid PostgreSQL credentials.

---

## Kubernetes Connectivity

A Kubernetes application may connect using:

```text
orders-db.database.svc.cluster.local
```

or an external managed database endpoint.

The path may be:

```text
Pod
 ↓
Kubernetes DNS
 ↓
Service / Endpoint
 ↓
NetworkPolicy
 ↓
Database
```

If the database is external:

```text
Pod
 ↓
Cluster networking
 ↓
VPC / Network
 ↓
RDS / PostgreSQL
```

Connectivity troubleshooting should identify which path is actually in use.

---

## Docker Connectivity

Docker networking frequently causes confusion around `localhost`.

Inside a container:

```text
localhost
```

means:

```text
the current container
```

not the host machine or another container.

For example:

```text
API container
    ↓
postgres container
```

The application should generally use the PostgreSQL service/container name rather than `localhost`.

Example:

```bash
psql -h postgres -U app -d orders
```

---

## Docker Compose Example

A simplified architecture:

```yaml
services:
  api:
    build: .
    environment:
      DATABASE_HOST: postgres

  postgres:
    image: postgres:17
```

From the `api` container:

```text
DATABASE_HOST=postgres
```

is appropriate because Docker Compose provides service-name-based networking.

---

## Kubernetes Port Forwarding

For controlled development access:

```bash
kubectl port-forward service/postgres 5432:5432
```

Then:

```bash
psql \
  -h localhost \
  -p 5432 \
  -U app_readonly \
  -d orders
```

This changes the network path:

```text
psql
 ↓
localhost:5432
 ↓
kubectl port-forward
 ↓
Kubernetes service
 ↓
PostgreSQL
```

Port forwarding should not replace production access controls.

---

## Connection URIs

A PostgreSQL connection URI can represent the connection parameters in one value:

```text
postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

Example without a password:

```bash
psql 'postgresql://app_readonly@db.internal:5432/orders'
```

With SSL configuration:

```bash
psql 'postgresql://app_readonly@db.internal:5432/orders?sslmode=verify-full'
```

Be careful when logging or displaying connection URIs because they can contain credentials.

---

## Environment Variables

PostgreSQL clients support connection-related environment variables:

```bash
export PGHOST=db.internal
export PGPORT=5432
export PGUSER=app_readonly
export PGDATABASE=orders
```

Then:

```bash
psql
```

This is convenient for controlled environments.

For production credentials, use an approved secret-management mechanism rather than committing environment files to source control.

---

## `.pgpass`

PostgreSQL clients can use a password file for non-interactive authentication.

The file uses entries in the form:

```text
hostname:port:database:username:password
```

Example:

```text
db.internal:5432:orders:app_readonly:REDACTED
```

The file must be appropriately protected.

On Unix-like systems, restrictive file permissions are important.

Do not use `.pgpass` as a substitute for proper production secret management when stronger mechanisms are available.

---

## Application Connections vs `psql`

A CLI connection:

```text
psql
 ↓
One session
 ↓
PostgreSQL
```

An application commonly uses:

```text
Application replicas
       ↓
Connection pools
       ↓
Multiple PostgreSQL sessions
```

For example:

```text
5 API pods
 ×
10 pooled connections
 =
Potentially 50 database connections
```

This is why database connection capacity must be considered across the entire deployment.

---

## Connection Pooling

Applications commonly use:

```text
Django
SQLAlchemy
PgBouncer
```

to control database connections.

`psql` normally establishes an individual connection.

Therefore, if an application reports:

```text
too many connections
```

investigate:

```text
Application replicas
Pool sizes
Overflow connections
PgBouncer
Background workers
Administrative sessions
```

rather than only checking one application instance.

---

## Connection Timeouts

A connection can fail because of network or server conditions.

Differentiate:

```text
Connection timeout
```

from:

```text
Query timeout
```

and:

```text
Lock timeout
```

They occur at different stages.

Conceptually:

```text
Connection timeout
    ↓
Could not establish session

Statement timeout
    ↓
Session exists, query exceeded limit

Lock timeout
    ↓
Query exists, waiting too long for a lock
```

---

## Debugging Connection Failures

Use a layered workflow.

### DNS

```bash
nslookup db.internal.example.com
```

### TCP

```bash
nc -vz db.internal.example.com 5432
```

### PostgreSQL

```bash
psql \
  -h db.internal.example.com \
  -p 5432 \
  -U app_readonly \
  -d orders
```

### Session

```text
\conninfo
```

### Authorization

```sql
SELECT current_user;
```

### Query

```sql
SELECT 1;
```

This sequence narrows the failure domain.

---

## `SELECT 1`

A simple database connectivity test is:

```sql
SELECT 1;
```

If this succeeds:

```text
Network
+
TLS
+
Authentication
+
Database connection
+
Basic SQL execution
```

have all succeeded sufficiently for that query.

It does not prove that the role has access to every schema or table.

---

## Connection Failure Decision Tree

```mermaid
flowchart TD
    Start[Cannot connect] --> DNS{DNS resolves?}

    DNS -->|No| DNSFix[Fix DNS / hostname]
    DNS -->|Yes| TCP{TCP reachable?}

    TCP -->|No| NetFix[Check network / SG / firewall / port]
    TCP -->|Yes| TLS{TLS succeeds?}

    TLS -->|No| TLSFix[Check CA / certificate / hostname / sslmode]
    TLS -->|Yes| Auth{Authentication succeeds?}

    Auth -->|No| AuthFix[Check role / credentials / pg_hba]
    Auth -->|Yes| DBAuth{Can connect to database?}

    DBAuth -->|No| DBFix[Check CONNECT privilege / database]
    DBAuth -->|Yes| Query{Can execute required SQL?}

    Query -->|No| PermFix[Check schema / table / RLS privileges]
    Query -->|Yes| Success[Connection path is healthy]
```

This approach avoids random configuration changes.

---

## Common Connection Errors

### Connection Refused

Usually indicates that nothing is accepting connections at the target address and port, or an intermediary is actively rejecting the connection.

Investigate:

```text
Host
Port
PostgreSQL listener
Security groups
Firewall
Service state
```

### Connection Timed Out

Usually indicates that packets cannot complete the connection path.

Investigate:

```text
Routing
Security groups
Network ACLs
Firewall
NetworkPolicy
VPN / bastion path
```

### Could Not Translate Host Name

This is generally a DNS or hostname issue.

Investigate:

```bash
nslookup HOST
```

### Password Authentication Failed

The server was reached, but authentication failed.

Investigate:

```text
Username
Password
Authentication method
pg_hba.conf
Credential rotation
Secret configuration
```

### Database Does Not Exist

The server was reached, but the requested database is unavailable.

Check:

```text
-d DATABASE
```

and:

```text
\l
```

### Permission Denied

The session exists, but the role lacks required privileges.

Investigate:

```text
Role membership
Database CONNECT
Schema USAGE
Table privileges
RLS
Ownership
```

---

## Checking the PostgreSQL Listener

On the database server, administrators can inspect listening sockets with:

```bash
ss -lntp | grep 5432
```

The exact command depends on the operating system.

PostgreSQL's `listen_addresses` configuration controls which network interfaces accept connections.

A server configured to listen only on localhost will not accept remote TCP connections.

---

## `listen_addresses`

PostgreSQL can be configured with:

```text
listen_addresses
```

Conceptually:

```text
listen_addresses = localhost
```

means the server listens locally.

A production configuration may use a private network interface or appropriate wildcard binding combined with network controls.

Do not expose PostgreSQL publicly merely to make connectivity easier.

Network-level restriction remains essential.

---

## Security Considerations

Database connectivity should follow:

```text
Private network
      ↓
Restricted network access
      ↓
TLS
      ↓
Strong authentication
      ↓
Least-privilege role
      ↓
Database authorization
```

Avoid:

```text
Public PostgreSQL
+
Weak credentials
+
No TLS
+
Superuser application role
```

Successful connectivity is not the goal by itself.

The goal is **secure, authorized connectivity**.

---

## Production Access Pattern

A mature production workflow might be:

```text
Engineer
   ↓
SSO / Identity
   ↓
Approved access path
   ↓
Private network / bastion / controlled proxy
   ↓
PostgreSQL endpoint
   ↓
TLS
   ↓
Read-only role
   ↓
psql
```

For administrative changes, use stronger controls:

```text
Change / Incident
      ↓
Authorization
      ↓
Privileged access
      ↓
Audited operation
      ↓
Verification
```

---

## Connecting With a Read-Only Role

Routine investigation should use a role such as:

```text
app_readonly
```

Example:

```bash
psql \
  -h production-db.internal \
  -U app_readonly \
  -d orders
```

Then verify:

```text
\conninfo
```

and:

```sql
SELECT current_user;
```

This limits the blast radius of accidental commands.

---

## Production Connection Checklist

Before connecting:

- [ ] Verify hostname.
- [ ] Verify port.
- [ ] Verify database.
- [ ] Verify role.
- [ ] Verify environment.
- [ ] Verify access authorization.
- [ ] Verify TLS requirements.

After connecting:

- [ ] Run `\conninfo`.
- [ ] Check `current_database()`.
- [ ] Check `current_user`.
- [ ] Check `pg_is_in_recovery()` when relevant.
- [ ] Run `SELECT 1`.
- [ ] Use the least-privileged role necessary.

Before modifying data:

- [ ] Confirm the target is the intended primary.
- [ ] Inspect the schema.
- [ ] Preview affected rows.
- [ ] Understand transaction and locking behavior.
- [ ] Confirm rollback/recovery strategy.

---

## Connecting in a Production Incident

A disciplined workflow is:

```text
Incident
   ↓
Identify environment
   ↓
Identify database endpoint
   ↓
Verify network path
   ↓
Connect using read-only role
   ↓
\conninfo
   ↓
Inspect database state
   ↓
Escalate privilege only when required
   ↓
Perform controlled operation
   ↓
Verify result
```

Do not start an incident by connecting with the highest available privilege.

---

## Reliability Considerations

Database connections are stateful resources.

Failures can occur because:

```text
Database restarted
Network interrupted
Failover occurred
Connection became stale
Credentials rotated
Pool exhausted
Database reached connection limit
Proxy failed
TLS certificate expired
```

Applications should therefore use:

- Connection pooling
- Connection health checks where appropriate
- Connection timeouts
- Retry strategies with backoff
- Idempotent operations
- Stable database endpoints

The CLI is useful for reproducing and isolating these failures.

---

## High Availability

In an HA architecture:

```text
                 +--> Replica
                 |
Application --> HA Endpoint --> Current Primary
                 |
                 +--> Standby
```

A failover can change which node is primary while the endpoint remains stable.

Directly connecting to a specific node can therefore behave differently from connecting through the application's normal HA endpoint.

When troubleshooting failover, determine:

```text
Which endpoint?
Which server?
Primary or replica?
Current recovery state?
Replication status?
```

---

## Disaster Recovery

A DR environment may have:

```text
Different hostname
Different network
Different credentials
Different certificates
Different DNS
```

Therefore, a connection string that works in production may not work in DR.

Document and test:

```text
DR endpoint
Network route
TLS configuration
Credentials
Database names
Roles
Permissions
```

Recovery procedures should not depend on undocumented CLI knowledge.

---

## Monitoring Connections

Once connected, PostgreSQL exposes session information through:

```sql
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    backend_start
FROM pg_stat_activity
ORDER BY backend_start;
```

This helps correlate:

```text
Which clients are connected?
Which roles are used?
Where are connections coming from?
How many sessions exist?
```

For application troubleshooting, combine database-side data with:

```text
Application pool metrics
Load balancer metrics
Kubernetes pod counts
Celery worker counts
PgBouncer metrics
```

---

## Connection Scaling

Suppose:

```text
20 API pods
10 connections per pod
5 Celery workers
5 connections per worker
```

Potential database sessions could approach:

```text
20 × 10 + 5 × 5
= 225 connections
```

Additional connections may come from:

```text
Monitoring
Migrations
Admins
Reporting
Other services
```

Therefore, database connection capacity must be planned across the entire system.

---

## Cost Considerations

Poor connection management can increase infrastructure requirements.

Excessive connections may require:

```text
Larger database instance
More memory
Connection pooling infrastructure
Database proxies
Additional replicas
```

The solution is not always increasing `max_connections`.

Often the better solution is:

```text
Right-size pools
+
Reduce unnecessary sessions
+
Use PgBouncer where appropriate
+
Control application replica scaling
```

---

## Common Mistakes

### Using `localhost` From a Container

Inside a container:

```text
localhost
```

usually refers to the same container.

Use the appropriate Docker or Kubernetes service name instead.

### Forgetting the Database Name

This:

```bash
psql -h db.internal -U app
```

may connect to a different default database than expected.

Prefer explicit:

```bash
psql -h db.internal -U app -d orders
```

### Not Verifying the Connection

Always use:

```text
\conninfo
```

before production operations.

### Assuming Network Access Means Database Access

TCP reachability does not imply:

```text
Authentication
CONNECT privilege
Schema access
Table access
RLS access
```

### Disabling TLS to Fix a Certificate Problem

Do not solve certificate configuration problems by removing encryption or validation requirements.

Fix:

```text
CA
Certificate
Hostname
Trust configuration
sslmode
```

instead.

### Using Superuser Credentials

Routine CLI work should not require unrestricted database privileges.

### Confusing Primary and Replica

Always check:

```sql
SELECT pg_is_in_recovery();
```

when the target role matters.

---

## Interview Traps

### What happens when `psql` connects to PostgreSQL?

At a high level:

```text
DNS
 ↓
TCP
 ↓
TLS
 ↓
PostgreSQL startup/authentication
 ↓
Database authorization
 ↓
Session
```

### What is the difference between authentication and authorization?

Authentication establishes identity.

Authorization determines what that identity can do.

### Why can `psql -h localhost` behave differently from `psql`?

They can use different connection mechanisms and therefore different PostgreSQL authentication rules.

### Why does a connection succeed but `SELECT` fail?

The role may lack:

```text
Schema privileges
Table privileges
Column privileges
RLS access
```

### Why is `\conninfo` important?

Because a valid connection can still point to the wrong:

```text
Host
Database
Role
Environment
```

### Why can an application run out of connections while `psql` works?

The application may have too many pooled connections or too many application/worker replicas.

A single CLI session does not represent the application's aggregate connection demand.

### Why can a replica return stale data?

Because replication is often asynchronous and replay can lag behind primary WAL generation.

---

## Recommended Connection Diagnostic Query

Keep a standard diagnostic query available:

```sql
SELECT
    current_database() AS database,
    current_user AS current_user,
    session_user,
    inet_server_addr() AS server_ip,
    inet_server_port() AS server_port,
    pg_is_in_recovery() AS is_replica,
    current_setting('server_version') AS server_version;
```

It quickly establishes:

```text
Where am I?
Who am I?
Which server am I using?
Is it a replica?
Which PostgreSQL version is running?
```

This is especially useful in environments with multiple databases, replicas, and deployment stages.

---

## Practical Connection Workflow

A reliable workflow for PostgreSQL CLI access is:

```bash
psql \
  -h db.internal \
  -p 5432 \
  -U app_readonly \
  -d orders
```

Then:

```text
\conninfo
```

Verify:

```sql
SELECT
    current_database(),
    current_user,
    pg_is_in_recovery();
```

Test:

```sql
SELECT 1;
```

Inspect:

```text
\dn
\dt
\d+ app.orders
```

Then perform the required diagnostic or operational task.

This simple workflow prevents many common environment and authorization errors.

---

## Key Takeaways

- **Database connectivity is a layered process:** DNS, TCP, TLS, PostgreSQL authentication, database authorization, and SQL execution should be diagnosed separately.
- **Always verify the session before production work:** use `\conninfo`, `current_database()`, `current_user`, and `pg_is_in_recovery()` when primary/replica identity matters.
- **Network reachability is not authorization:** a successful TCP connection does not imply valid authentication, `CONNECT` privilege, schema access, table access, or RLS access.
- **Application connectivity differs from CLI connectivity:** applications use pools and multiple replicas, so connection capacity must be designed across APIs, workers, proxies, and administrative clients.
- **Secure connectivity is the goal:** prefer private networking, appropriate TLS verification, managed credentials, least-privilege roles, stable HA endpoints, and controlled production access.