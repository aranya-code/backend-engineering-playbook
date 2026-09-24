# 03- Docker MongoDB Deployment

## Overview

Docker provides a reproducible way to run MongoDB locally and in controlled development or test environments without installing MongoDB directly on the host operating system.

A Docker-based MongoDB deployment separates:

- MongoDB server lifecycle
- Database storage
- Network configuration
- Authentication
- Application configuration
- Environment reproducibility

A typical backend architecture is:

```text
┌──────────────────────────────────────────────┐
│ Docker Compose                               │
│                                              │
│  ┌──────────────┐       ┌─────────────────┐ │
│  │ FastAPI /    │       │ MongoDB         │ │
│  │ Django       │──────>│ Container       │ │
│  │ API          │       │                 │ │
│  └──────────────┘       └───────┬─────────┘ │
│                                 │           │
│                                 v           │
│                         MongoDB Volume      │
└──────────────────────────────────────────────┘
```

Docker is particularly useful for:

- Local development
- Integration testing
- CI environments
- Reproducible development environments
- Running MongoDB alongside application services
- Testing replica-set-dependent features

Docker should not automatically be treated as a production MongoDB architecture. For production, managed MongoDB platforms or carefully operated infrastructure should generally be evaluated against availability, backup, security, observability, and operational requirements.

## Docker MongoDB Architecture

A MongoDB container normally contains the database server process, while persistent data is stored outside the container filesystem.

```text
MongoDB Container
       |
       | /data/db
       v
Docker Volume
       |
       v
Persistent Database Files
```

This separation is important because containers are disposable.

```text
Container Lifecycle
-------------------

Create
  ↓
Run
  ↓
Stop
  ↓
Remove
  ↓
Create New Container
```

The database data should have an independent lifecycle:

```text
Container
    X

Volume
    |
    v
Database Data
```

## MongoDB Docker Image

Use an explicitly controlled MongoDB image version.

Example:

```yaml
services:
  mongo:
    image: mongo:8.0
```

Avoid:

```yaml
services:
  mongo:
    image: mongo:latest
```

A floating tag can cause an environment to change unexpectedly when the image is updated.

Version selection should consider:

- Application compatibility
- PyMongo compatibility
- MongoDB feature requirements
- Existing production version
- Upgrade testing
- Team standards

For production-like development, the local MongoDB major version should generally match the major version used by the target environment.

## Basic Docker Deployment

A minimal MongoDB container can be started with:

```bash
docker run -d \
  --name mongodb \
  -p 127.0.0.1:27017:27017 \
  -v mongodb_data:/data/db \
  mongo:8.0
```

Verify the container:

```bash
docker ps
```

View logs:

```bash
docker logs mongodb
```

Connect with `mongosh`:

```bash
mongosh "mongodb://127.0.0.1:27017"
```

Verify MongoDB:

```javascript
db.runCommand({ ping: 1 })
```

Expected result:

```javascript
{ ok: 1 }
```

## Docker Compose

Docker Compose is usually more useful than a standalone `docker run` command for backend projects.

A minimal deployment:

```yaml
services:
  mongo:
    image: mongo:8.0
    restart: unless-stopped
    ports:
      - "127.0.0.1:27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

Start MongoDB:

```bash
docker compose up -d
```

Check status:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f mongo
```

Stop containers:

```bash
docker compose down
```

The named volume remains after `docker compose down`.

## Named Volumes

A named volume provides persistent storage independent of the MongoDB container.

```yaml
volumes:
  mongodb_data:
```

and:

```yaml
services:
  mongo:
    volumes:
      - mongodb_data:/data/db
```

The relationship is:

```mermaid
flowchart LR
    Container[MongoDB Container]
    Mount["/data/db"]
    Volume[Docker Named Volume]
    Data[(MongoDB Data)]

    Container --> Mount
    Mount --> Volume
    Volume --> Data
```

This means:

```bash
docker compose down
```

does not normally remove the database volume.

However:

```bash
docker compose down -v
```

removes the declared volumes and therefore destroys the local database state.

Treat this command as destructive.

## Container Filesystem vs Volume

| Storage | Survives container removal | Recommended for MongoDB |
|---|---:|---:|
| Container writable layer | No | No |
| Named volume | Yes | Yes |
| Bind mount | Yes | Sometimes |
| Temporary filesystem | No | No |

For most local development environments, a named volume is the simplest choice.

## Docker Networking

Docker Compose automatically creates a network for services in the same project.

For example:

```yaml
services:
  api:
    build: .
    depends_on:
      - mongo

  mongo:
    image: mongo:8.0
```

The application can connect to MongoDB using:

```text
mongodb://mongo:27017/orders
```

The hostname:

```text
mongo
```

is the Compose service name.

## `localhost` Inside Containers

This is one of the most common Docker networking mistakes.

Consider:

```text
Host
 |
 +-- API Container
 |
 +-- MongoDB Container
```

Inside the API container:

```text
localhost
```

means:

```text
The API container itself
```

It does not mean the MongoDB container.

Therefore this is usually incorrect from the API container:

```text
mongodb://localhost:27017/orders
```

Use:

```text
mongodb://mongo:27017/orders
```

when `mongo` is the MongoDB service name.

## Host-to-Container Access

When the MongoDB port is published:

```yaml
ports:
  - "127.0.0.1:27017:27017"
```

the host can connect using:

```text
mongodb://127.0.0.1:27017/orders
```

The distinction is:

| Client location | MongoDB hostname |
|---|---|
| Host machine | `127.0.0.1:27017` |
| Another Compose service | `mongo:27017` |
| External machine | Depends on published network configuration |

## Avoid Unnecessary Port Exposure

If only the application container needs MongoDB, the MongoDB port does not need to be published to the host.

```yaml
services:
  api:
    build: .

  mongo:
    image: mongo:8.0
    volumes:
      - mongodb_data:/data/db
```

The API can still connect using:

```text
mongodb://mongo:27017/orders
```

This reduces unnecessary host exposure.

If host access is required, bind the port to loopback:

```yaml
ports:
  - "127.0.0.1:27017:27017"
```

Avoid unnecessarily exposing MongoDB to all host interfaces.

## Docker Compose With FastAPI

A practical backend environment might contain:

```yaml
services:
  api:
    build:
      context: .
    environment:
      MONGODB_URI: mongodb://mongo:27017/orders
    depends_on:
      - mongo
    ports:
      - "8000:8000"

  mongo:
    image: mongo:8.0
    restart: unless-stopped
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

The architecture is:

```mermaid
flowchart LR
    Client[HTTP Client]
    API[FastAPI Container]
    Driver[PyMongo]
    Mongo[MongoDB Container]
    Volume[(MongoDB Volume)]

    Client --> API
    API --> Driver
    Driver --> Mongo
    Mongo --> Volume
```

## Application Configuration

Do not hard-code MongoDB connection strings inside application code.

Prefer:

```yaml
environment:
  MONGODB_URI: mongodb://mongo:27017/orders
```

and application code:

```python
import os

from pymongo import MongoClient

client = MongoClient(
    os.environ["MONGODB_URI"],
    serverSelectionTimeoutMS=5000,
)

db = client["orders"]
```

For local development, `.env` can be used.

```dotenv
MONGODB_URI=mongodb://mongo:27017/orders
```

Example Compose configuration:

```yaml
services:
  api:
    build: .
    env_file:
      - .env
```

Do not commit a real `.env` containing credentials.

## Authentication

For simple local development, authentication may not be necessary.

For production-like testing, enable authentication.

Example:

```yaml
services:
  mongo:
    image: mongo:8.0
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
    volumes:
      - mongodb_data:/data/db
```

The root credentials should not be used by the application.

Instead:

```text
MongoDB Root User
       |
       +-- Database Administration
       |
       +-- Application User
               |
               +-- Application Database
```

The application should use a dedicated least-privilege account.

## Authentication Database

MongoDB users belong to an authentication database.

For example, if an application user is created in the `orders` database:

```text
mongodb://app_user:password@mongo:27017/orders?authSource=orders
```

If the user is created in `admin`:

```text
mongodb://app_user:password@mongo:27017/orders?authSource=admin
```

A common authentication failure is specifying the wrong `authSource`.

## Initialization Scripts

The official MongoDB image supports initialization scripts placed under:

```text
/docker-entrypoint-initdb.d/
```

Example project:

```text
docker/
└── mongo/
    └── init/
        └── 01-init.js
```

Compose:

```yaml
services:
  mongo:
    image: mongo:8.0
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
    volumes:
      - mongodb_data:/data/db
      - ./docker/mongo/init:/docker-entrypoint-initdb.d:ro
```

Example initialization script:

```javascript
db = db.getSiblingDB("orders");

db.createUser({
  user: "orders_app",
  pwd: process.env.MONGO_APP_PASSWORD,
  roles: [
    {
      role: "readWrite",
      db: "orders"
    }
  ]
});
```

Initialization behavior should be understood carefully.

The initialization scripts are primarily intended for first-time database initialization. If the database directory already contains initialized MongoDB data, they are not automatically rerun on every container start.

This means:

```text
Empty Volume
    ↓
MongoDB Initialization
    ↓
Users / Databases / Seed Setup
```

is different from:

```text
Existing Volume
    ↓
Container Restart
    ↓
Existing Database State
```

## Seed Data

Development seed data can be loaded during initialization or through a dedicated application command.

For example:

```text
scripts/
└── seed.py
```

A dedicated seed workflow is often easier to control than putting large application datasets into container initialization scripts.

Example:

```bash
python scripts/seed.py
```

Seed data should be:

- Deterministic
- Non-sensitive
- Reproducible
- Small enough for development
- Representative of important application states

## MongoDB Health Checks

Container health should distinguish between:

```text
Process Running
```

and:

```text
MongoDB Accepting Requests
```

A Compose health check can use `mongosh`:

```yaml
services:
  mongo:
    image: mongo:8.0
    healthcheck:
      test:
        [
          "CMD-SHELL",
          "mongosh --quiet --eval 'db.runCommand({ ping: 1 }).ok' | grep 1"
        ]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
```

Health checks become especially useful when multiple services depend on MongoDB.

## Startup Ordering

This configuration:

```yaml
depends_on:
  - mongo
```

controls container startup ordering but does not by itself guarantee that MongoDB is ready to accept application connections.

A better approach is to combine:

- MongoDB health check
- Application retry behavior
- Appropriate connection timeout
- Dependency-aware startup

Example:

```yaml
services:
  api:
    build: .
    depends_on:
      mongo:
        condition: service_healthy

  mongo:
    image: mongo:8.0
    healthcheck:
      test:
        [
          "CMD-SHELL",
          "mongosh --quiet --eval 'db.runCommand({ ping: 1 }).ok' | grep 1"
        ]
      interval: 10s
      timeout: 5s
      retries: 5
```

The application should still handle transient database unavailability gracefully.

## PyMongo Connection Management

A long-running application should generally create one `MongoClient` per process and reuse it.

Prefer:

```python
import os

from pymongo import MongoClient

client = MongoClient(
    os.environ["MONGODB_URI"],
    serverSelectionTimeoutMS=5000,
)
```

rather than:

```python
def get_order(order_id):
    client = MongoClient(os.environ["MONGODB_URI"])
    return client.orders.orders.find_one({"_id": order_id})
```

`MongoClient` manages a connection pool internally.

The application should not create a new client for every request.

## FastAPI Lifecycle

A FastAPI application can manage the MongoDB client through its application lifespan.

```python
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import MongoClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = MongoClient(
        os.environ["MONGODB_URI"],
        serverSelectionTimeoutMS=5000,
    )

    client.admin.command("ping")

    app.state.mongo_client = client
    app.state.mongo_db = client["orders"]

    try:
        yield
    finally:
        client.close()


app = FastAPI(lifespan=lifespan)
```

For asynchronous applications, use an appropriate asynchronous MongoDB API rather than assuming synchronous PyMongo operations are non-blocking.

## Django Integration

A Dockerized Django application can connect to the MongoDB service through the Compose network.

```yaml
services:
  web:
    build: .
    environment:
      MONGODB_URI: mongodb://mongo:27017/orders
    depends_on:
      mongo:
        condition: service_healthy

  mongo:
    image: mongo:8.0
```

A repository-oriented architecture is useful when Django's primary relational database and MongoDB coexist:

```text
Django
  |
  +-- API / Views
  |
  +-- Service Layer
  |
  +-- MongoDB Repository
  |
  +-- PyMongo
  |
  +-- MongoDB
```

Do not assume that MongoDB provides the same ORM semantics as Django's relational database backends.

## Dockerized Multi-Service Backend

A realistic local backend may contain:

```yaml
services:
  api:
    build:
      context: .
    environment:
      MONGODB_URI: mongodb://mongo:27017/orders
      REDIS_URL: redis://redis:6379/0
    depends_on:
      mongo:
        condition: service_healthy
      redis:
        condition: service_started
    ports:
      - "8000:8000"

  mongo:
    image: mongo:8.0
    volumes:
      - mongodb_data:/data/db
    healthcheck:
      test:
        [
          "CMD-SHELL",
          "mongosh --quiet --eval 'db.runCommand({ ping: 1 }).ok' | grep 1"
        ]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7

volumes:
  mongodb_data:
```

The application now has a service-discovery model:

```text
api
 |
 +-- mongo:27017
 |
 +-- redis:6379
```

No hard-coded container IP addresses are required.

## Replica Set Deployment

A standalone MongoDB container is insufficient when the application needs to reproduce replica-set behavior.

Replica sets are relevant to:

- Multi-document transactions
- Change streams
- Majority write concerns
- Elections
- Failover behavior
- Replication testing

A local single-node replica set is useful when the application needs replica-set semantics without running multiple MongoDB containers.

## Single-Node Replica Set

Example Compose configuration:

```yaml
services:
  mongo:
    image: mongo:8.0
    command:
      - mongod
      - --replSet
      - rs0
      - --bind_ip_all
    ports:
      - "127.0.0.1:27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

Start MongoDB:

```bash
docker compose up -d mongo
```

Initialize the replica set:

```bash
mongosh "mongodb://127.0.0.1:27017" --eval \
  'rs.initiate({_id:"rs0",members:[{_id:0,host:"localhost:27017"}]})'
```

Inspect status:

```bash
mongosh "mongodb://127.0.0.1:27017" --eval \
  'rs.status()'
```

The exact hostname used in `rs.initiate()` must be reachable by clients that discover the replica-set topology.

For applications running inside Docker, using container-resolvable hostnames is generally more appropriate than advertising `localhost`.

## Multi-Node Replica Set

A development replica set can contain multiple MongoDB containers.

Conceptually:

```mermaid
flowchart TB
    API[Backend Application]
    P[MongoDB Primary]
    S1[MongoDB Secondary]
    S2[MongoDB Secondary]
    V1[(Volume 1)]
    V2[(Volume 2)]
    V3[(Volume 3)]

    API --> P
    P --> S1
    P --> S2
    P --> V1
    S1 --> V2
    S2 --> V3
```

A multi-node replica set is useful for testing:

- Election behavior
- Failover
- Replication lag
- Read preference
- Majority writes
- Application reconnect behavior

However, a Docker development replica set is not equivalent to production infrastructure with independent hosts and failure domains.

## Replica Set Hostnames

Replica-set members advertise addresses to clients.

A common mistake is:

```javascript
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "localhost:27017" }
  ]
})
```

when the application is running in another container.

The application container interprets:

```text
localhost
```

as itself.

Container-aware deployments should use Docker DNS names that are resolvable from the client.

For example:

```text
mongo1:27017
mongo2:27017
mongo3:27017
```

The exact topology should be designed so that all required clients can resolve and reach the advertised MongoDB member addresses.

## MongoDB and Persistent Storage

MongoDB writes database files under its configured data directory, commonly:

```text
/data/db
```

For Docker:

```yaml
volumes:
  - mongodb_data:/data/db
```

The volume should be considered part of the database deployment.

Important properties include:

- Persistence
- Available disk capacity
- Filesystem behavior
- Backup requirements
- Cleanup behavior

Do not treat the container filesystem as durable database storage.

## Bind Mounts

A bind mount can map a host directory to MongoDB's data directory:

```yaml
volumes:
  - ./mongo-data:/data/db
```

This provides direct access to host files but introduces platform-specific behavior.

Potential issues include:

- File permissions
- Filesystem performance
- Windows/macOS virtualization overhead
- Accidental modification of database files
- Host backup interactions

For general development, named volumes are often simpler.

## Backup Considerations

A Docker volume is not a backup.

This:

```text
MongoDB
   ↓
Docker Volume
```

provides persistence, not disaster recovery.

A real backup workflow is:

```text
MongoDB
   ↓
Backup Process
   ↓
Backup Artifact
   ↓
Independent Storage
   ↓
Validation
   ↓
Restore Test
```

For local development, backups may not be necessary if the database is disposable.

For important shared Docker environments, backup requirements should be evaluated explicitly.

## Import and Export

MongoDB Database Tools can be used against a Dockerized MongoDB instance.

Export:

```bash
mongodump \
  --uri="mongodb://127.0.0.1:27017/orders" \
  --out=./dump
```

Restore:

```bash
mongorestore \
  --uri="mongodb://127.0.0.1:27017" \
  ./dump
```

JSON import:

```bash
mongoimport \
  --uri="mongodb://127.0.0.1:27017/orders" \
  --collection=orders \
  --file=orders.json \
  --jsonArray
```

These commands should be used against appropriate development data.

Do not accidentally restore production data into a developer environment without considering security and privacy requirements.

## Docker and MongoDB Compass

MongoDB Compass can connect to a published MongoDB port.

For:

```yaml
ports:
  - "127.0.0.1:27017:27017"
```

Compass can use:

```text
mongodb://127.0.0.1:27017
```

For a container-only deployment with no published port, Compass running on the host cannot directly use the Docker service name:

```text
mongodb://mongo:27017
```

because `mongo` is resolved inside the Docker network, not normally by the host operating system.

## Docker Resource Limits

Docker resource constraints can make local MongoDB behave differently from an unconstrained host.

Relevant resources include:

- CPU
- Memory
- Disk
- I/O

A memory-constrained MongoDB container can experience behavior that does not represent a production cluster.

This is useful for testing resource pressure but should be intentional.

## Performance Considerations

Dockerized MongoDB performance depends on:

- Host hardware
- Container resources
- Docker storage driver
- Volume type
- Dataset size
- Working set
- CPU allocation
- Memory allocation
- Filesystem virtualization

On macOS and Windows, Docker often runs Linux containers inside a virtualized environment, which can introduce filesystem performance differences compared with native Linux.

Therefore:

```text
Local Docker Performance
        ≠
Production MongoDB Performance
```

Use Docker for functional and integration testing, not as the sole source of production capacity estimates.

## Query Performance Testing

Docker is still useful for validating query behavior.

Example:

```javascript
db.orders.find({
  customer_id: ObjectId("64b000000000000000000001"),
  status: "PAID"
}).sort({
  created_at: -1
}).explain("executionStats")
```

Inspect:

```text
nReturned
totalKeysExamined
totalDocsExamined
executionTimeMillis
```

Use realistic test data when evaluating index choices.

A collection containing 500 documents does not meaningfully validate the behavior of a production collection containing hundreds of millions of documents.

## CI Integration

Docker is particularly useful for CI because the database can be created and destroyed as part of the test environment.

Example workflow:

```text
CI Job
  ↓
Start MongoDB Container
  ↓
Wait for Health
  ↓
Initialize Database
  ↓
Run Migrations / Index Setup
  ↓
Run Integration Tests
  ↓
Collect Logs
  ↓
Destroy Environment
```

A CI environment should generally use isolated database state.

Example:

```bash
docker compose up -d mongo
```

Run tests:

```bash
pytest -m integration
```

Clean up:

```bash
docker compose down -v
```

The destructive volume removal is appropriate for an ephemeral CI environment when no database state needs to survive.

## Docker Compose Profiles

Different development scenarios can be represented using Compose profiles.

For example:

```yaml
services:
  mongo:
    image: mongo:8.0

  mongo-replica:
    image: mongo:8.0
    profiles:
      - replica-set
    command:
      - mongod
      - --replSet
      - rs0
      - --bind_ip_all
```

A team can maintain a lightweight default environment while enabling more complex database topology only when needed.

The exact Compose structure should be designed carefully so that services do not accidentally share incompatible storage or network assumptions.

## Environment Separation

Docker configuration should distinguish between:

```text
Development
Test
CI
Production
```

A useful structure is:

```text
docker/
├── mongo/
│   └── init/
├── compose.yml
├── compose.dev.yml
└── compose.test.yml
```

Avoid maintaining one huge Compose file containing every environment-specific behavior unless there is a clear operational reason.

## Security

A Dockerized MongoDB instance should still be treated as a database server.

Security considerations include:

- Authentication
- Network exposure
- Credentials
- Container permissions
- Image provenance
- Image versioning
- Secrets
- Host access
- Backup data
- Production data handling

Do not assume:

```text
Inside Docker = Secure
```

Docker provides isolation mechanisms, not complete database security.

## Secrets

For local development, environment variables or `.env` files may be acceptable.

For CI and production, use the secret-management mechanisms provided by the deployment platform.

Avoid:

```yaml
environment:
  MONGO_INITDB_ROOT_PASSWORD: supersecret
```

in committed production configuration.

Prefer:

```yaml
environment:
  MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
```

with the secret injected by the execution environment.

## Image Security

The MongoDB image is part of the software supply chain.

Production-oriented practices include:

- Pin supported image versions
- Regularly update images
- Scan images where appropriate
- Avoid unnecessary customizations
- Track MongoDB version changes
- Test upgrades before deployment

Do not blindly upgrade the MongoDB major version in development and assume production behavior will remain unchanged.

## Upgrade Strategy

MongoDB upgrades should be tested independently from Docker image upgrades.

A controlled process is:

```text
Current MongoDB Version
        ↓
Test New Version
        ↓
Validate Driver Compatibility
        ↓
Validate Queries
        ↓
Validate Indexes
        ↓
Validate Transactions
        ↓
Validate Application
        ↓
Deploy Upgrade
```

The Docker image is only one part of the upgrade.

Database compatibility and operational behavior must also be validated.

## Production Considerations

Docker is appropriate for:

- Local development
- CI
- Integration environments
- Disposable test environments
- Controlled development infrastructure

Running MongoDB in Docker can also be part of production infrastructure, but doing so requires much more than:

```bash
docker run mongo
```

Production requirements include:

- Persistent storage
- Replica-set topology
- Independent failure domains
- Automated backups
- Restore testing
- Monitoring
- Alerting
- Security
- Capacity planning
- Upgrade procedures
- Disaster recovery
- Operational ownership

A production deployment should be evaluated against managed MongoDB services such as MongoDB Atlas and against the organization's infrastructure capabilities.

## Kubernetes Considerations

If MongoDB eventually moves from Docker Compose to Kubernetes, do not simply convert the Compose file into Kubernetes manifests.

MongoDB requires stateful infrastructure considerations:

```text
Kubernetes
    |
    +-- Stateful MongoDB Nodes
    |
    +-- Persistent Volumes
    |
    +-- Stable Network Identity
    |
    +-- Replica Set
    |
    +-- Backup
    |
    +-- Monitoring
```

For production Kubernetes deployments, managed MongoDB is often operationally simpler than self-managing the database cluster.

## Common Mistakes

### Using `localhost` Between Containers

Incorrect:

```text
mongodb://localhost:27017/orders
```

Correct for Compose service-to-service communication:

```text
mongodb://mongo:27017/orders
```

### Forgetting Persistent Storage

Incorrect:

```yaml
services:
  mongo:
    image: mongo:8.0
```

with the expectation that database data will survive container replacement.

Use:

```yaml
volumes:
  - mongodb_data:/data/db
```

### Running `docker compose down -v` Carelessly

This removes named volumes declared by the Compose project.

Use it intentionally when resetting disposable environments.

### Treating `depends_on` as Readiness

Container startup order does not automatically mean MongoDB is ready.

Use health checks and application-level connection handling.

### Using `latest`

Floating image versions create environment drift.

Pin the MongoDB version.

### Exposing MongoDB Publicly

Avoid unnecessary:

```yaml
ports:
  - "0.0.0.0:27017:27017"
```

Prefer no published port or loopback-only access for local development.

### Using Root Credentials From the Application

Create an application-specific database user with minimum required privileges.

### Assuming Volumes Are Backups

A Docker volume protects against some container lifecycle events but does not provide a complete backup or disaster-recovery strategy.

### Using Docker for Production Without a Database Operations Plan

Containerization does not automatically provide:

- High availability
- Backups
- Disaster recovery
- Monitoring
- Database upgrades
- Capacity management

## Troubleshooting

### MongoDB Container Exits

```text
Symptom
↓
MongoDB container stops immediately
↓
Possible causes
↓
Invalid configuration
Permission problem
Corrupted data directory
Unsupported configuration
Image/version issue
↓
Isolation strategy
↓
Inspect container status and logs
↓
Diagnostic commands
```

```bash
docker compose ps
```

```bash
docker compose logs mongo
```

```bash
docker inspect <container>
```

```text
Root cause
↓
Container startup or MongoDB configuration failure
↓
Corrective action
↓
Fix configuration, storage, or image compatibility
↓
Prevention
↓
Validate Compose configuration and MongoDB startup in CI
```

### Data Disappears After Container Recreation

```text
Symptom
↓
MongoDB data is missing after container replacement
↓
Possible causes
↓
No persistent volume
Wrong volume
Volume removed
Different Compose project
↓
Isolation strategy
↓
Inspect mounts and volumes
↓
Diagnostic commands
```

```bash
docker volume ls
```

```bash
docker inspect <container>
```

```text
Root cause
↓
Database files were not stored in the expected persistent volume
↓
Corrective action
↓
Mount a named volume at /data/db
↓
Prevention
↓
Define storage explicitly in Compose and test recreation behavior
```

### Application Cannot Connect

```text
Symptom
↓
API cannot connect to MongoDB
↓
Possible causes
↓
Wrong hostname
Wrong port
MongoDB not ready
Network mismatch
Authentication failure
↓
Isolation strategy
↓
Check service names, networks, health, and URI
↓
Diagnostic commands
```

```bash
docker compose ps
```

```bash
docker compose logs mongo
```

From the API container, test the configured MongoDB hostname using the networking tools available in the image.

```text
Root cause
↓
Networking, readiness, or authentication configuration
↓
Corrective action
↓
Fix the connection configuration or service readiness
↓
Prevention
↓
Use service discovery, health checks, and environment-specific URIs
```

### Authentication Failure

```text
Symptom
↓
MongoServerError: Authentication failed
↓
Possible causes
↓
Wrong username
Wrong password
Wrong authSource
User does not exist
Initialization did not run
Existing volume preserved old credentials
↓
Isolation strategy
↓
Verify users and authentication database
↓
Diagnostic commands
```

```javascript
use admin
db.getUsers()
```

```text
Root cause
↓
Application credentials do not match the initialized MongoDB state
↓
Corrective action
↓
Correct credentials or intentionally recreate the development database
↓
Prevention
↓
Understand initialization-on-first-start behavior and manage credentials explicitly
```

### Replica Set Connection Failure

```text
Symptom
↓
Application connects initially but fails after topology discovery
↓
Possible causes
↓
Replica-set members advertise unreachable hostnames
localhost advertised from inside Docker
Incorrect replica-set name
Network isolation
↓
Isolation strategy
↓
Inspect replica-set configuration and advertised member addresses
↓
Diagnostic commands
```

```javascript
rs.status()
```

```javascript
rs.conf()
```

```text
Root cause
↓
Replica-set topology advertised to the client is not reachable
↓
Corrective action
↓
Configure container-resolvable and client-reachable member addresses
↓
Prevention
↓
Design Docker networking and replica-set hostnames together
```

## Production Readiness Checklist

### Docker Configuration

- [ ] MongoDB image version is explicitly controlled.
- [ ] MongoDB data is stored in persistent storage.
- [ ] Container networking is documented.
- [ ] Health checks are configured where appropriate.
- [ ] Service dependencies are understood.

### Application Integration

- [ ] MongoDB URI is externalized.
- [ ] PyMongo client is reused.
- [ ] Connection timeouts are configured.
- [ ] Application retry behavior is defined.
- [ ] Database indexes are reproducible.
- [ ] Seed data is deterministic where required.

### Security

- [ ] Authentication is configured when required.
- [ ] Application users use least privilege.
- [ ] Credentials are not committed to Git.
- [ ] MongoDB is not unnecessarily exposed.
- [ ] Sensitive production data is not casually copied into development.
- [ ] Container images are maintained and reviewed.

### Persistence

- [ ] Named or equivalent persistent storage is configured.
- [ ] Data reset behavior is documented.
- [ ] Destructive Docker commands are understood.
- [ ] Backup requirements are explicitly defined for non-disposable environments.

### Replica Set

- [ ] Replica-set requirements are identified.
- [ ] Member hostnames are reachable by clients.
- [ ] Transactions are tested when required.
- [ ] Change streams are tested when required.
- [ ] Failover behavior is tested where relevant.

### Operations

- [ ] MongoDB logs are accessible.
- [ ] Container health is observable.
- [ ] Resource constraints are understood.
- [ ] MongoDB version upgrades are tested.
- [ ] Recovery procedures exist for environments where data is important.

## Interview Focus

| Question | Key point |
|---|---|
| Why use Docker for MongoDB? | Reproducibility, isolation, and easy environment lifecycle management |
| Why use a Docker volume? | Database state should survive container replacement |
| Why does `localhost` fail between containers? | `localhost` refers to the current container |
| What is the difference between a volume and a backup? | A volume provides persistence; a backup provides an independent recovery mechanism |
| Why is `depends_on` insufficient for database readiness? | Startup ordering does not guarantee service readiness |
| Why use health checks? | They provide an explicit readiness signal for dependent services |
| Why pin MongoDB image versions? | Prevent unexpected environment changes |
| Why use a replica set locally? | Transactions, change streams, elections, and majority semantics require replica-set behavior |
| Why can a replica set work initially and then fail? | The driver may discover advertised member addresses that it cannot reach |
| Should MongoDB always expose port 27017? | No; only publish it when host/external access is actually required |
| Are Docker volumes backups? | No; they are persistent storage, not independent disaster recovery |
| Is Docker MongoDB production-ready by default? | No; production requires deliberate HA, storage, backup, security, monitoring, and recovery design |

## Key Takeaways

- **Use Docker Compose to make MongoDB development environments reproducible, and store database files in explicit persistent volumes rather than the container filesystem.**
- **Understand Docker networking: containers should normally reach MongoDB through the Compose service name, while host access requires an intentionally published port.**
- **Use health checks, connection timeouts, and application retry behavior because container startup order does not guarantee MongoDB readiness.**
- **Use replica-set Docker deployments when testing transactions, change streams, failover, or other topology-dependent MongoDB behavior, and ensure advertised member addresses are reachable by clients.**
- **Treat Docker as a deployment mechanism rather than a complete database operations strategy; production MongoDB still requires deliberate security, HA, backup, monitoring, capacity, and recovery design.**