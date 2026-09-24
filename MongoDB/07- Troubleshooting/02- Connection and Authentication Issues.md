# 02- Connection and Authentication Issues

## Overview

MongoDB connection and authentication failures occur at different layers and should not be diagnosed as a single problem category.

A backend application must establish a complete path before it can execute a database operation:

```text
Application
    ↓
MongoDB Driver
    ↓
DNS / Service Discovery
    ↓
TCP Connection
    ↓
TLS
    ↓
MongoDB Server Selection
    ↓
Authentication
    ↓
Authorization
    ↓
Database Operation
```

A failure at any layer can surface as a generic application error such as:

```text
ServerSelectionTimeoutError
Authentication failed
Connection refused
Connection timed out
TLS handshake failed
not authorized on database
```

The important engineering distinction is:

- **Connectivity** — can the application reach a suitable MongoDB server?
- **Authentication** — can MongoDB verify the client identity?
- **Authorization** — does the authenticated identity have the required privileges?
- **Topology** — can the driver discover and select an appropriate MongoDB member?
- **Configuration** — are the application, driver, TLS, credentials, and environment settings consistent?

A senior troubleshooting workflow isolates these layers before changing configuration.

## Connection Lifecycle

A typical application connection follows this sequence:

```mermaid
sequenceDiagram
    participant App as Application
    participant Driver as MongoDB Driver
    participant DNS as DNS / Service Discovery
    participant DB as MongoDB

    App->>Driver: Create / reuse MongoClient
    Driver->>DNS: Resolve MongoDB hostname
    DNS-->>Driver: IP address
    Driver->>DB: Establish TCP connection
    Driver->>DB: TLS handshake
    DB-->>Driver: TLS established
    Driver->>DB: Discover topology
    DB-->>Driver: Replica set / server information
    Driver->>DB: Authenticate
    DB-->>Driver: Authentication result
    App->>Driver: Execute database operation
    Driver->>DB: Query / write
    DB-->>Driver: Result
    Driver-->>App: Result
```

A failure before authentication is fundamentally different from an authentication failure.

For example:

```text
DNS failure
```

means the driver may never reach MongoDB.

Whereas:

```text
Authentication failed
```

means MongoDB was reachable far enough to process the authentication attempt.

## Connection Failure Categories

| Layer | Typical failure | Example |
|---|---|---|
| Configuration | Invalid URI | Wrong hostname or port |
| DNS | Host cannot resolve | `NXDOMAIN` |
| Network | TCP blocked | Firewall/security group |
| TLS | Certificate mismatch | Untrusted CA |
| Topology | No suitable server | Replica-set discovery failure |
| Authentication | Invalid identity | Bad username/password |
| Authorization | Insufficient privileges | `not authorized` |
| Driver | Pool exhaustion | Requests waiting for connections |
| Application | Incorrect usage | New client per request |

This classification significantly reduces troubleshooting time.

## MongoDB Connection Strings

A typical connection string contains:

```text
mongodb://username:password@hostname:27017/database
```

A replica-set connection may include:

```text
mongodb://user:password@mongo-1:27017,mongo-2:27017,mongo-3:27017/app?replicaSet=rs0
```

MongoDB Atlas commonly uses an SRV connection string:

```text
mongodb+srv://username:password@cluster.example.mongodb.net/app
```

The connection string can define important behavior such as:

- Hosts
- Port
- Database
- Authentication database
- Replica set
- TLS
- Read preference
- Write concern
- Retry behavior
- Timeouts

Do not treat the connection string as merely a hostname and password.

## Connection String Components

| Component | Purpose |
|---|---|
| Scheme | `mongodb://` or `mongodb+srv://` |
| Credentials | Username and password |
| Hosts | MongoDB servers or SRV hostname |
| Database | Default application database |
| `authSource` | Database containing the authenticated user |
| `replicaSet` | Expected replica-set name |
| `tls` | Enables TLS |
| `readPreference` | Controls eligible read nodes |
| `w` | Write acknowledgement configuration |
| `serverSelectionTimeoutMS` | Server-selection timeout |
| `connectTimeoutMS` | Connection establishment timeout |
| `socketTimeoutMS` | Socket operation timeout |

## Secure Connection Configuration

Do not hard-code credentials:

```python
MONGODB_URI = "mongodb://admin:password123@localhost:27017/app"
```

Prefer environment-backed configuration:

```python
import os

MONGODB_URI = os.environ["MONGODB_URI"]
```

For production systems, credentials should normally come from a secret-management system such as:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- Kubernetes Secrets integrated with an appropriate secret-management strategy
- A dedicated enterprise secret manager

Environment variables are a configuration mechanism, not inherently a secure secret-management solution.

## DNS Troubleshooting

DNS is one of the first layers to verify.

From Linux:

```bash
getent hosts mongodb.example.internal
```

Or:

```bash
nslookup mongodb.example.internal
```

For SRV-based connections:

```bash
dig SRV _mongodb._tcp.cluster.example.mongodb.net
```

A DNS problem may produce errors that look like MongoDB availability problems.

### Diagnostic Pattern

```text
Connection failure
↓
Can hostname resolve?
↓
No → DNS / service discovery problem
↓
Yes
↓
Can TCP connection be established?
↓
No → Network / firewall problem
↓
Yes
↓
Continue with TLS and MongoDB topology
```

## TCP Connectivity

Test the target port independently of the application.

Linux:

```bash
nc -vz mongodb.example.internal 27017
```

Windows PowerShell:

```powershell
Test-NetConnection mongodb.example.internal -Port 27017
```

A successful TCP connection does not prove that MongoDB authentication or authorization will succeed.

It only establishes that the network path is open enough to establish a TCP connection.

## Docker Networking

A frequent mistake is using:

```text
mongodb://localhost:27017/app
```

from inside an application container.

Inside a container:

```text
localhost
```

refers to the current container.

With Docker Compose, the MongoDB service name is typically used:

```text
mongodb://mongodb:27017/app
```

Example:

```yaml
services:
  api:
    build: .
    environment:
      MONGODB_URI: mongodb://mongodb:27017/app
    depends_on:
      - mongodb

  mongodb:
    image: mongo:latest
```

The actual production configuration should pin an appropriate MongoDB image version rather than relying on `latest`.

## Kubernetes Networking

In Kubernetes, the application should normally connect through the appropriate Service or stable database endpoint rather than a Pod IP.

Typical flow:

```text
Application Pod
      ↓
Kubernetes DNS
      ↓
Service
      ↓
MongoDB Endpoint
```

Useful diagnostics:

```bash
kubectl get svc
```

```bash
kubectl get endpoints
```

```bash
kubectl exec -it <pod-name> -- getent hosts <mongodb-service>
```

A connection that works from a developer laptop but fails from Kubernetes should immediately raise questions about:

- DNS
- NetworkPolicy
- Security groups
- Routing
- Service configuration
- TLS
- Secrets
- Environment-specific connection strings

## TLS Troubleshooting

TLS protects MongoDB traffic in transit and may be required in production.

A TLS failure can occur because of:

- Incorrect CA certificate
- Expired certificate
- Hostname mismatch
- Missing client certificate
- Incorrect certificate chain
- Incorrect TLS settings
- Unsupported TLS configuration
- Clock skew affecting certificate validation

The important distinction is:

```text
TCP connection succeeds
        ↓
TLS handshake fails
        ↓
MongoDB authentication has not necessarily occurred
```

Do not debug TLS failures by permanently disabling certificate validation.

## TLS Diagnostics

For an appropriate TLS endpoint, certificate information can be inspected with:

```bash
openssl s_client \
  -connect mongodb.example.internal:27017 \
  -servername mongodb.example.internal
```

For production systems, validate:

- Certificate expiration
- Subject / SAN
- Trusted CA
- Certificate chain
- Server hostname
- Client certificate requirements
- Rotation procedures

## MongoDB Authentication

Authentication establishes the identity of the client.

Common MongoDB authentication mechanisms include:

- SCRAM-SHA-256
- SCRAM-SHA-1
- X.509
- AWS IAM authentication in supported deployment configurations

The appropriate mechanism depends on the deployment and security architecture.

Authentication is separate from authorization.

```text
Authentication
    ↓
Who are you?
    ↓
Authorization
    ↓
What are you allowed to do?
```

## Authentication Database

One of the most common configuration errors is misunderstanding `authSource`.

For example:

```text
mongodb://app_user:password@mongodb:27017/orders?authSource=admin
```

The application operates against:

```text
orders
```

but authenticates the user against:

```text
admin
```

If the user was created in `admin`, omitting the correct authentication database can cause authentication failures.

## Inspecting Authentication State

After connecting with appropriate privileges:

```javascript
db.runCommand({
  connectionStatus: 1,
  showPrivileges: true
})
```

This can help determine:

- Authenticated users
- Authentication mechanisms
- Effective privileges

Do not expose this output through public health endpoints.

## SCRAM Authentication

SCRAM authentication verifies a username and password without sending the plaintext password over the network.

Production considerations include:

- Use TLS.
- Use strong credentials.
- Rotate credentials through controlled procedures.
- Avoid sharing administrative credentials with applications.
- Use separate identities for applications, migrations, and operations.
- Grant only required privileges.

## Application Identity

An application should normally have a dedicated MongoDB identity.

For example:

```text
orders-api
payments-api
reporting-worker
migration-job
```

Avoid using:

```text
root
admin
```

as the identity for normal application traffic.

A dedicated identity provides:

- Least privilege
- Better auditability
- Safer credential rotation
- Reduced blast radius

## Authorization

After authentication, MongoDB evaluates whether the identity can perform the requested operation.

For example:

```text
Authenticated successfully
        ↓
find on orders
        ↓
Allowed?
        ↓
Yes → execute
No  → authorization error
```

A typical authorization error resembles:

```text
not authorized on orders to execute command
```

This is not a connectivity problem.

## Role Troubleshooting

Investigate:

- Username
- Authentication database
- Assigned roles
- Target database
- Target collection
- Required action

For administrative diagnosis, inspect the user's information with appropriate privileges.

Avoid fixing authorization problems with:

```text
dbOwner
readWriteAnyDatabase
root
```

unless the workload genuinely requires those privileges.

## Least-Privilege Application Roles

A service that only needs application CRUD should not normally have unrestricted administrative privileges.

Example conceptual permission:

```text
orders-api
    ├── read orders
    ├── insert orders
    ├── update orders
    └── no user-management privileges
```

Separate administrative operations from normal application traffic.

## Authentication vs Authorization

| Problem | Meaning | First investigation |
|---|---|---|
| Connection refused | TCP connection failed | Network / process |
| Server selection timeout | No suitable MongoDB server selected | DNS / topology / network |
| TLS handshake failure | Secure connection failed | Certificates / TLS |
| Authentication failed | Identity verification failed | Username / password / authSource |
| Not authorized | Identity lacks permission | Roles / privileges |
| Query timeout | Operation exceeded timeout | Query / resources / network |

## Server Selection

MongoDB drivers do not simply connect to the first hostname and execute requests.

The driver maintains knowledge of MongoDB topology and selects an appropriate server based on:

- Server type
- Replica-set membership
- Read preference
- Server health
- Latency
- Connection state
- Configuration

A common error is:

```text
ServerSelectionTimeoutError
```

This means the driver could not select a suitable server within the configured selection timeout.

It does not necessarily mean:

```text
MongoDB process is down.
```

## Server Selection Troubleshooting

Use this sequence:

```text
ServerSelectionTimeoutError
↓
Check DNS
↓
Check TCP
↓
Check TLS
↓
Check replica-set name
↓
Check advertised member hostnames
↓
Check replica-set health
↓
Check read preference
↓
Check network reachability to all required members
```

This is especially important with replica sets.

## Replica-Set Hostname Problems

A classic production failure occurs when the application can reach the initial MongoDB endpoint but cannot reach the hostnames advertised by the replica set.

For example:

```text
Application
    ↓
mongo-router.example.com
    ↓
MongoDB responds:
    mongo-1.internal
    mongo-2.internal
    mongo-3.internal
```

If the application cannot resolve or reach those internal hostnames, server selection can fail after the initial connection.

The important diagnostic question is:

> Can the application reach every MongoDB endpoint that the driver is expected to use?

## Replica-Set Name Mismatch

If the connection string specifies:

```text
replicaSet=rs0
```

but the server reports a different replica-set name, topology discovery can fail.

Inspect the topology:

```javascript
rs.status()
```

and configuration:

```javascript
rs.conf()
```

Verify:

- Replica-set name
- Member hostnames
- Ports
- Member states

## Connection Timeouts

MongoDB applications use multiple timeout concepts.

| Setting | Purpose |
|---|---|
| `serverSelectionTimeoutMS` | Maximum time to select a suitable server |
| `connectTimeoutMS` | Maximum time to establish a connection |
| `socketTimeoutMS` | Maximum time waiting for socket operations |
| `waitQueueTimeoutMS` | Maximum time waiting for a pooled connection |

These solve different problems.

Increasing every timeout is not a troubleshooting strategy.

For example:

```text
Pool exhausted
    ↓
Requests wait for connection
    ↓
waitQueueTimeoutMS exceeded
```

Increasing `serverSelectionTimeoutMS` will not necessarily fix pool exhaustion.

## Connection Pool Exhaustion

PyMongo maintains connection pools internally.

A common architecture is:

```text
API Instance
    ├── Process 1 → MongoClient → Pool
    ├── Process 2 → MongoClient → Pool
    └── Process 3 → MongoClient → Pool
```

Across multiple instances:

```text
Application Fleet
    ↓
Many processes
    ↓
Many MongoDB connection pools
    ↓
MongoDB
```

A pool size that appears reasonable for one process can become excessive across an entire fleet.

For example:

```text
20 pods × 4 processes × 100 max connections
= up to 8,000 pool connections
```

The exact active connection count depends on workload and topology, but the multiplication illustrates why fleet-level capacity planning matters.

## PyMongo Client Lifecycle

A common mistake is creating a new client per request:

```python
def get_orders():
    client = MongoClient(MONGODB_URI)
    return client["orders"].orders.find({})
```

This can cause unnecessary connection establishment and resource consumption.

Prefer a long-lived client per process:

```python
from pymongo import MongoClient

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=3000,
)
```

Then reuse:

```python
db = client["orders"]
orders = db["orders"]
```

For pre-fork application servers, create the client in the appropriate child-process lifecycle rather than sharing a client across a fork boundary.

## Python Connection Health Check

A safe application-level health check can test connectivity:

```python
from pymongo import MongoClient
from pymongo.errors import PyMongoError


def mongodb_is_healthy(client: MongoClient) -> bool:
    try:
        client.admin.command("ping")
        return True
    except PyMongoError:
        return False
```

Health endpoints should distinguish between:

- Liveness
- Readiness
- Dependency health

A database outage should not necessarily cause Kubernetes to restart every application process.

## FastAPI Connection Troubleshooting

A typical FastAPI architecture is:

```text
FastAPI
   ↓
Dependency / Repository
   ↓
MongoClient
   ↓
Connection Pool
   ↓
MongoDB
```

A synchronous PyMongo client should not be treated as an async client merely because the surrounding application uses `async def`.

For workloads requiring asynchronous MongoDB access, use the currently supported asynchronous MongoDB driver/API appropriate to the PyMongo version and application architecture.

Do not mix incompatible synchronous and asynchronous connection-management patterns.

## FastAPI Startup Configuration

Connection configuration should be validated during application startup without exposing secrets.

Example:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import MongoClient

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    client.admin.command("ping")
    yield
    client.close()


app = FastAPI(lifespan=lifespan)
```

In a real production application, startup failure policy should be deliberate. Some systems should fail fast if MongoDB is mandatory; others may require degraded startup behavior.

## Django Connection Troubleshooting

Django applications can introduce another configuration layer.

Investigate:

- Django settings
- Environment variables
- Repository/service configuration
- MongoDB client lifecycle
- Authentication settings
- Serialization
- Deployment environment

Do not assume that a MongoDB integration behaves exactly like Django's native relational database backend.

If PyMongo is used directly, diagnose the PyMongo client and repository layer separately from Django itself.

## Authentication in Background Workers

A common production issue is:

```text
API works
Worker fails
```

Possible reasons:

- Different environment variables
- Different Kubernetes Secret
- Different IAM identity
- Different network path
- Different MongoDB URI
- Different authentication database
- Different application version

Compare sanitized configuration rather than assuming the worker has the same environment as the API.

## AWS Connectivity

When MongoDB is deployed in AWS or accessed from AWS workloads, investigate:

```text
Application
    ↓
VPC routing
    ↓
Security Group / Network ACL
    ↓
Private endpoint / Load Balancer / MongoDB host
    ↓
MongoDB
```

For MongoDB Atlas, investigate the configured network access and private connectivity architecture where applicable.

Common causes include:

- Incorrect IP access configuration
- Security group rules
- VPC routing
- Private DNS
- NAT configuration
- Peering / private connectivity configuration
- Incorrect application subnet

Do not expose MongoDB publicly merely to test connectivity.

## Credential Rotation Failures

Credential rotation can produce sudden authentication failures even when application code has not changed.

Typical sequence:

```text
Credential rotated
      ↓
Secret updated
      ↓
Application still uses old secret
      ↓
Authentication fails
```

A safe rotation process should account for:

- Secret propagation
- Application restart/reload
- Connection pool lifecycle
- Overlapping credentials where supported
- Rollback
- Verification

Avoid manually editing credentials on individual production hosts.

## Secret Management Failures

Check whether the application is receiving the expected secret without logging its value.

Useful diagnostic metadata:

```text
Secret source
Secret version
Configuration load timestamp
Credential username
Authentication database
TLS enabled
```

Never log:

```text
password
full MongoDB URI
private key
client certificate contents
```

## Common Connection Mistakes

### Using `localhost` From a Container

```text
mongodb://localhost:27017
```

may point to the application container instead of MongoDB.

Use the appropriate Docker or Kubernetes service endpoint.

### Wrong `authSource`

The user may exist in `admin` while the application database is `orders`.

Use:

```text
authSource=admin
```

when appropriate.

### Wrong Replica-Set Name

A mismatch can prevent topology discovery.

Verify with:

```javascript
rs.status()
```

### Incorrect Advertised Hostnames

The MongoDB server may advertise addresses that the application cannot resolve.

### Missing TLS Configuration

A production cluster requiring TLS will reject clients configured for plaintext connections.

### Expired Certificates

Certificate rotation should be monitored and tested before expiration.

### Hard-Coded Credentials

Credentials embedded in source code are difficult to rotate safely and can leak through Git history.

### Creating a Client Per Request

This creates unnecessary connection overhead and can exhaust database resources.

## Common Authentication Mistakes

### Using Administrative Users for Applications

This violates least privilege and increases blast radius.

### Sharing One Credential Across Services

A shared identity makes auditing and credential rotation harder.

Prefer:

```text
orders-api
payments-api
reporting-worker
```

with separate identities where practical.

### Granting Broad Roles to Fix Errors

Do not solve:

```text
not authorized
```

with:

```text
root
```

Determine the exact required privilege.

### Logging Credentials

Connection strings are frequently logged accidentally through:

- Startup configuration
- Exception messages
- Debug logging
- CI/CD output
- Health checks

Sanitize secrets before logging.

## Diagnostic Decision Tree

```mermaid
flowchart TD
    A[Application cannot access MongoDB] --> B{Hostname resolves?}

    B -->|No| C[Fix DNS / Service Discovery]
    B -->|Yes| D{TCP connection works?}

    D -->|No| E[Check Firewall / Security Group / Network]
    D -->|Yes| F{TLS succeeds?}

    F -->|No| G[Check CA / Certificate / TLS Configuration]
    F -->|Yes| H{Suitable MongoDB server selected?}

    H -->|No| I[Check Replica Set / Topology / Read Preference]
    H -->|Yes| J{Authentication succeeds?}

    J -->|No| K[Check Username / Password / authSource / Mechanism]
    J -->|Yes| L{Authorization succeeds?}

    L -->|No| M[Check Roles / Privileges]
    L -->|Yes| N[Investigate Query / Application Behavior]
```

## Production Troubleshooting Workflow

### Step 1: Capture the Exact Error

Record:

- Exception type
- Error message
- Timestamp
- Service
- Host/pod
- Application version
- MongoDB endpoint
- Request or trace ID

Do not redact the useful diagnostic information while accidentally preserving credentials.

### Step 2: Identify the Failure Layer

Classify the error:

```text
DNS
Network
TLS
Topology
Authentication
Authorization
Application
```

### Step 3: Test Outside the Application

Use `mongosh` or appropriate network diagnostics from the same environment.

For example:

```bash
mongosh "$MONGODB_URI" \
  --eval 'db.runCommand({ ping: 1 })'
```

If the same connection fails outside the application, investigate infrastructure or MongoDB configuration.

If it succeeds outside the application, investigate:

- Driver configuration
- Application environment
- Connection pool
- Application lifecycle
- Credential loading

### Step 4: Compare Environments

Compare:

```text
Local
Development
Staging
Production
```

Focus on configuration differences rather than copying production credentials into lower environments.

### Step 5: Inspect MongoDB Topology

For replica sets:

```javascript
rs.status()
```

Verify:

- Primary
- Secondaries
- Member health
- Replica-set name
- Advertised hostnames
- Replication state

### Step 6: Verify Authentication

Confirm:

- Username
- Authentication database
- Authentication mechanism
- Credential validity
- TLS requirements

### Step 7: Verify Authorization

Determine the exact MongoDB operation that fails and whether the application identity has the required privilege.

### Step 8: Verify Application Behavior

Inspect:

- MongoClient lifecycle
- Pool settings
- Number of processes
- Number of application instances
- Timeouts
- Retry behavior
- Connection creation patterns

## Symptom-Based Diagnosis

| Symptom | Likely area | First diagnostic action |
|---|---|---|
| `ECONNREFUSED` | Network / MongoDB process | TCP connectivity and server state |
| DNS resolution error | DNS | Resolve hostname from application environment |
| `ServerSelectionTimeoutError` | Topology / network | Check topology and endpoint reachability |
| TLS handshake error | TLS | Inspect certificate and TLS configuration |
| Authentication failure | Credentials | Verify username, password, auth source |
| `not authorized` | Authorization | Inspect roles and privileges |
| API pool timeout | Driver / application | Inspect pool size and process count |
| Works locally but not production | Environment | Compare network and configuration |
| API works but worker fails | Worker environment | Compare worker credentials/network/config |
| Works against one node but not replica set | Topology | Check advertised member addresses |
| Failures after credential rotation | Secret lifecycle | Verify secret propagation and client lifecycle |

## Observability Recommendations

Monitor authentication and connection failures separately.

Useful metrics include:

- Connection attempts
- Connection failures
- Authentication failures
- Server selection failures
- Pool wait time
- Active connections
- Connection creation rate
- MongoDB operation latency
- Replica-set topology changes
- TLS certificate expiration

Alerting should distinguish:

```text
Database unavailable
```

from:

```text
Application credentials invalid
```

because the remediation paths are completely different.

## Security Considerations

Connection troubleshooting should never weaken production security controls unnecessarily.

Avoid:

```text
Allow 0.0.0.0/0
Disable TLS
Disable authentication
Use root credentials
Print passwords
Expose MongoDB publicly
```

Instead:

- Test from the actual application network.
- Use least-privilege identities.
- Use TLS.
- Restrict network access.
- Rotate credentials safely.
- Monitor certificate expiration.
- Audit authentication failures.
- Keep secrets outside source control.

## Reliability Considerations

A production application should tolerate expected MongoDB topology changes without converting every transient event into an outage.

Consider:

- Appropriate server-selection timeout
- Appropriate connection timeout
- Appropriate socket timeout
- Driver retry behavior
- Idempotency of retried operations
- Replica-set failover
- Connection-pool capacity
- Application readiness behavior
- Dependency health monitoring

Timeouts should be designed from the application's latency budget rather than copied from another service.

## Troubleshooting Checklist

### Connectivity

- [ ] Confirm the exact hostname.
- [ ] Resolve DNS from the application environment.
- [ ] Test TCP connectivity.
- [ ] Verify the MongoDB port.
- [ ] Check security groups and firewall rules.
- [ ] Check Kubernetes NetworkPolicy where applicable.
- [ ] Verify private connectivity or routing.

### TLS

- [ ] Confirm TLS is enabled when required.
- [ ] Verify CA configuration.
- [ ] Verify certificate validity.
- [ ] Verify hostname/SAN.
- [ ] Check certificate expiration.
- [ ] Check client certificate requirements.

### Authentication

- [ ] Verify username.
- [ ] Verify password through the secret-management system.
- [ ] Verify `authSource`.
- [ ] Verify authentication mechanism.
- [ ] Confirm the user exists in the expected authentication database.

### Authorization

- [ ] Identify the exact failing operation.
- [ ] Identify the authenticated user.
- [ ] Inspect assigned roles.
- [ ] Verify target database and collection.
- [ ] Apply least privilege.

### Driver

- [ ] Reuse `MongoClient` appropriately.
- [ ] Review pool configuration.
- [ ] Review server-selection timeout.
- [ ] Review connection timeout.
- [ ] Review socket timeout.
- [ ] Review retry behavior.
- [ ] Check process and instance count.

### Replica Set

- [ ] Check `rs.status()`.
- [ ] Verify the replica-set name.
- [ ] Verify advertised hostnames.
- [ ] Check member reachability.
- [ ] Check primary availability.
- [ ] Check recent elections.

## Interview Traps

### "Authentication and authorization are the same."

They are different.

```text
Authentication → identity verification
Authorization  → permission evaluation
```

### "A server-selection timeout means MongoDB is down."

Not necessarily.

The driver may be unable to select a suitable server because of:

- DNS
- Network
- TLS
- Replica-set discovery
- Read preference
- Incorrect topology
- Unreachable advertised hosts

### "If `mongosh` connects, the application is configured correctly."

Not necessarily.

The application may use:

- Different credentials
- Different URI
- Different environment
- Different TLS settings
- Different driver options
- Different network path

### "Increasing the timeout fixes connection problems."

It may only delay the error.

Determine whether the problem is:

```text
DNS
Network
TLS
Topology
Authentication
Pool exhaustion
MongoDB latency
```

before changing timeout values.

### "Use `root` to fix authorization errors."

This creates unnecessary privilege and security risk.

Determine the required privilege instead.

## Key Takeaways

- **MongoDB connection failures should be isolated across DNS, TCP, TLS, server selection, authentication, authorization, driver pooling, and application configuration.**
- **Authentication verifies identity while authorization determines permissions; treating them as the same problem leads to incorrect and overly broad fixes.**
- **Replica-set topology matters because the driver must be able to reach the MongoDB hosts advertised during topology discovery, not merely the initial connection endpoint.**
- **Production Python applications should reuse appropriately scoped `MongoClient` instances and size connection pools based on the entire application fleet.**
- **Never weaken TLS, network restrictions, or least-privilege controls to troubleshoot connectivity; diagnose the actual failure layer and correct the underlying configuration.**