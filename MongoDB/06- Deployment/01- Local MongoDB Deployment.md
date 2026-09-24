# 01- Local MongoDB Deployment

## Overview

Local MongoDB deployment provides an isolated environment for developing, debugging, testing, and validating backend applications before they are deployed to shared or production infrastructure.

For backend engineers, local MongoDB should reproduce the important characteristics of the application's expected database environment without unnecessarily reproducing production infrastructure.

Typical local architectures include:

```text
Python / Django / FastAPI
          |
          | MongoDB URI
          v
     Local MongoDB
          |
          v
    Local Persistent Data
```

For containerized development:

```text
┌──────────────────────────────┐
│ Docker Compose               │
│                              │
│  ┌────────────┐              │
│  │ API        │              │
│  │ FastAPI    │              │
│  │ / Django   │              │
│  └─────┬──────┘              │
│        │                     │
│        │ mongodb://mongo     │
│        v                     │
│  ┌────────────┐              │
│  │ MongoDB    │              │
│  │ Container  │              │
│  └─────┬──────┘              │
│        │                     │
│        v                     │
│   Named Volume               │
└──────────────────────────────┘
```

The goal is not simply to install MongoDB. A useful local deployment should provide:

- Repeatable startup and shutdown
- Persistent development data where appropriate
- Predictable connection configuration
- Authentication when required by the application
- A setup close enough to production to expose important integration issues
- Easy reset and recreation
- Clear separation between local and production configuration

## Local Deployment Options

MongoDB can be deployed locally in several ways.

| Approach | Best use | Persistence | Isolation | Operational effort |
|---|---|---:|---:|---:|
| Native installation | Direct local development | Yes | Low | Low |
| Docker | Repeatable development environments | Yes | High | Low |
| Docker Compose | Multi-service backend development | Yes | High | Low |
| MongoDB Atlas | Cloud integration testing | Yes | High | Medium |
| Kubernetes | Kubernetes-specific development | Yes | High | High |

For most backend development workflows, native MongoDB and Docker Compose are the two practical choices.

## Native MongoDB Installation

A native installation runs MongoDB directly on the developer's operating system.

The general architecture is:

```text
Operating System
       |
       +-- mongod
       |
       +-- MongoDB Data Directory
       |
       +-- MongoDB Log Directory
       |
       +-- mongosh
```

This approach is useful when:

- MongoDB is the primary technology being developed
- Low startup overhead is important
- The developer wants direct access to MongoDB processes
- Docker is unavailable or unnecessary

Its main limitation is environment drift. Different developers may install different MongoDB versions, configuration files, or supporting tools.

## MongoDB Server and Shell

A local MongoDB environment generally consists of:

| Component | Responsibility |
|---|---|
| `mongod` | MongoDB database server |
| `mongosh` | MongoDB interactive shell |
| MongoDB Database Tools | Import, export, backup, and restore tooling |
| Application driver | Connects backend application to MongoDB |

The application does not normally communicate with `mongosh`.

```text
FastAPI / Django
       |
       v
    PyMongo
       |
       v
    MongoDB
```

`mongosh` is primarily an operational and development interface:

```text
Developer
    |
    v
 mongosh
    |
    v
 MongoDB
```

## Verify MongoDB Installation

After installing MongoDB, verify the server and shell independently.

```bash
mongod --version
```

```bash
mongosh --version
```

Connect to the local server:

```bash
mongosh
```

A successful connection should provide an interactive MongoDB shell.

Inspect the server:

```javascript
db.runCommand({ ping: 1 })
```

Expected result:

```javascript
{ ok: 1 }
```

## Local Connection URI

A common local URI is:

```text
mongodb://localhost:27017/
```

A database can be specified directly:

```text
mongodb://localhost:27017/myapp
```

The URI should normally be supplied through application configuration rather than hard-coded in source code.

Example:

```text
MONGODB_URI=mongodb://localhost:27017/myapp
```

For a Docker Compose service named `mongo`, the application container should use:

```text
mongodb://mongo:27017/myapp
```

The hostname is different because containers communicate through the Docker network rather than the host's loopback interface.

## Localhost vs Docker Networking

One of the most common MongoDB development mistakes is confusing `localhost`.

Consider:

```text
Host machine
    |
    +-- localhost:27017
    |
    +-- Docker container: API
```

Inside the API container:

```text
localhost
```

means:

```text
The API container itself
```

It does **not** mean the host machine or MongoDB container.

With Docker Compose:

```text
API container
      |
      | mongodb://mongo:27017
      v
MongoDB container
```

Therefore:

```text
MONGODB_URI=mongodb://mongo:27017/myapp
```

is normally correct for container-to-container communication.

## Docker-Based MongoDB

Docker is often preferable for backend teams because the MongoDB version and configuration can be defined as code.

Basic architecture:

```text
Docker Host
   |
   +-- mongo container
          |
          +-- /data/db
                 |
                 v
            Named Volume
```

A simple development container can be started with:

```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:8
```

The exact MongoDB image version should be pinned rather than relying on a floating `latest` tag.

For example:

```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:8.0
```

## Why Use a Named Volume

Without persistent storage, deleting the MongoDB container can delete the database's writable container filesystem.

A named volume separates database data from the container lifecycle.

```text
MongoDB Container
       |
       v
/data/db
       |
       v
mongodb_data volume
```

Container replacement:

```text
Old MongoDB Container
        X
        |
        v
mongodb_data
        |
        v
New MongoDB Container
```

The database data can therefore survive container recreation.

## Docker Compose

For a backend application, Docker Compose provides a more repeatable environment.

Example:

```yaml
services:
  mongo:
    image: mongo:8.0
    restart: unless-stopped
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

Start MongoDB:

```bash
docker compose up -d mongo
```

Check the container:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f mongo
```

Stop the environment:

```bash
docker compose down
```

The named volume remains unless explicitly removed.

## Complete Local Backend Environment

A realistic Python backend can run alongside MongoDB.

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

The networking flow is:

```mermaid
flowchart LR
    Client[HTTP Client]
    API[FastAPI / Django]
    DRIVER[PyMongo]
    MONGO[(MongoDB)]
    VOLUME[(Docker Volume)]

    Client --> API
    API --> DRIVER
    DRIVER --> MONGO
    MONGO --> VOLUME
```

The application should connect to:

```text
mongodb://mongo:27017/orders
```

not:

```text
mongodb://localhost:27017/orders
```

because both services run inside the Compose network.

## Local Authentication

A local MongoDB environment does not necessarily need authentication for every development workflow, but enabling authentication can make local behavior closer to production.

Example Compose configuration:

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

The application should generally **not** use the root account.

A production-like local setup should create an application-specific user with only the required permissions.

Conceptually:

```text
Root / Administrative User
            |
            +-- Database Administration
            |
            +-- Create Application User
                         |
                         v
                 Backend Application
```

## Environment Variables

Do not hard-code credentials or connection strings in application source code.

Example `.env`:

```dotenv
MONGODB_URI=mongodb://app_user:local_password@mongo:27017/orders?authSource=orders
```

Application configuration:

```python
import os

MONGODB_URI = os.environ["MONGODB_URI"]
```

For local development, `.env` can be loaded through the application's configuration system.

Do not commit:

```text
.env
```

when it contains credentials.

A safer repository structure is:

```text
project/
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
└── src/
```

`.env.example` should contain placeholders:

```dotenv
MONGODB_URI=mongodb://username:password@mongo:27017/database
```

## Python and PyMongo

A basic production-oriented local connection should reuse a `MongoClient` rather than creating a new client for every request.

```python
import os

from pymongo import MongoClient

client = MongoClient(
    os.environ["MONGODB_URI"],
    serverSelectionTimeoutMS=5000,
)

db = client["orders"]
orders = db["orders"]
```

Test connectivity:

```python
client.admin.command("ping")
```

The important architectural principle is:

```text
Application Process
       |
       +-- Shared MongoClient
              |
              +-- Connection Pool
                     |
                     +-- MongoDB
```

Creating a new client for every HTTP request unnecessarily increases connection-management overhead.

## FastAPI Local Configuration

A typical FastAPI application can create one client during application startup and close it during shutdown.

```python
import os

from fastapi import FastAPI
from pymongo import MongoClient

app = FastAPI()

client = MongoClient(
    os.environ["MONGODB_URI"],
    serverSelectionTimeoutMS=5000,
)

db = client["orders"]


@app.get("/health")
def health():
    client.admin.command("ping")
    return {"status": "ok"}
```

For larger applications, place database lifecycle and repository logic into dedicated modules rather than keeping everything in `main.py`.

A common structure is:

```text
app/
├── main.py
├── config.py
├── database.py
├── repositories/
│   └── orders.py
├── services/
│   └── orders.py
└── api/
    └── orders.py
```

## Django Local Configuration

Django can use MongoDB through an appropriate integration strategy such as PyMongo or a MongoDB-specific Django backend.

A PyMongo-based architecture commonly separates MongoDB access from Django's relational ORM:

```text
Django
  |
  +-- Views / API
  |
  +-- Service Layer
  |
  +-- Repository Layer
  |
  +-- PyMongo
  |
  +-- MongoDB
```

This is important because MongoDB does not automatically provide the same ORM semantics as Django's native relational database backends.

Do not assume that:

```python
Model.objects.filter(...)
```

has the same semantics or capabilities when working with MongoDB through a different integration layer.

## Local Replica Set

A standalone MongoDB instance is sufficient for many basic CRUD workflows.

However, some MongoDB features require a replica-set deployment, including important production-like scenarios such as:

- Transactions spanning multiple documents
- Change streams
- Replica-set behavior
- Failover testing
- Majority write behavior

A local replica set can therefore provide a more realistic development environment.

Architecture:

```text
              ┌───────────────┐
              │ MongoDB Node  │
              │ Primary       │
              └───────┬───────┘
                      │
             Replication
                ┌─────┴─────┐
                v           v
        ┌────────────┐ ┌────────────┐
        │ Secondary  │ │ Secondary  │
        └────────────┘ └────────────┘
```

A single-node replica set can also be useful when the application only needs replica-set semantics locally.

## Single-Node Replica Set with Docker

Example:

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
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

After starting MongoDB:

```bash
docker compose up -d mongo
```

Initialize the replica set:

```bash
mongosh "mongodb://localhost:27017" --eval \
  'rs.initiate({_id:"rs0", members:[{_id:0, host:"localhost:27017"}]})'
```

The exact replica-set host configuration must be reachable from the clients that connect to the replica set. When the application itself runs inside Docker, container DNS names are generally more appropriate than `localhost`.

## Docker Networking and Replica Sets

A common mistake is configuring:

```text
host = localhost:27017
```

for a MongoDB node that is accessed by another container.

Inside Docker:

```text
api container
     |
     | localhost
     v
api container
```

The MongoDB container is reached through its service name:

```text
api
 |
 | mongo:27017
 v
mongo
```

For a multi-container replica set, configure replica-set members using names that are resolvable from the application network.

## Local Health Checks

A database process being alive does not necessarily mean the application can use it correctly.

A useful health check verifies MongoDB connectivity:

```javascript
db.runCommand({ ping: 1 })
```

For a replica set:

```javascript
rs.status()
```

For database statistics:

```javascript
db.stats()
```

For collection statistics:

```javascript
db.orders.stats()
```

From Docker:

```bash
docker compose ps
```

```bash
docker compose logs --tail=100 mongo
```

## Application Health Checks

Separate liveness and readiness concepts.

### Liveness

Answers:

> Is the application process running?

### Readiness

Answers:

> Can the application currently serve requests using its dependencies?

For a backend service:

```text
GET /health/live
    |
    +-- Process running

GET /health/ready
    |
    +-- MongoDB reachable
    +-- Required dependencies available
```

Do not make every health endpoint perform expensive database queries.

## Local Database Initialization

Initialization should be deterministic.

Possible initialization steps include:

1. Start MongoDB.
2. Create required users.
3. Create application databases.
4. Apply schema validation.
5. Create required indexes.
6. Load optional development data.
7. Run application health checks.

Example:

```text
MongoDB Startup
      ↓
Authentication
      ↓
Database Initialization
      ↓
Schema Validation
      ↓
Indexes
      ↓
Seed Data
      ↓
Application Ready
```

Initialization scripts should be idempotent where practical.

## Index Initialization

Indexes should be part of application/database setup rather than manually recreated by every developer.

Example:

```javascript
db.orders.createIndex(
  { customer_id: 1, created_at: -1 }
)
```

For a unique business identifier:

```javascript
db.orders.createIndex(
  { order_number: 1 },
  { unique: true }
)
```

Local environments should contain the indexes required to reproduce realistic query behavior.

Otherwise, developers may benchmark an application against a collection scan while production uses indexes.

## Seed Data

Seed data should represent meaningful application states.

For example:

```text
customers
orders
products
payments
```

A useful development dataset can include:

- Normal records
- Missing optional fields
- Multiple related documents
- Large arrays
- Different status values
- Boundary timestamps
- Duplicate-looking business identifiers
- Records used by integration tests

Avoid using production data unless it has been appropriately sanitized and authorized for local use.

## Resetting Local MongoDB

A local database often needs to be reset during development.

With Docker Compose:

```bash
docker compose down -v
```

This removes containers and named volumes defined by the Compose project.

Because this deletes persistent local database data, it should be treated as a destructive operation.

An alternative is to drop only a development database:

```javascript
use orders
db.dropDatabase()
```

For automated development environments, a reset script can be preferable to manually deleting the entire Docker environment.

## Importing Development Data

MongoDB Database Tools can load JSON or BSON data into a local environment.

For JSON:

```bash
mongoimport \
  --uri="mongodb://localhost:27017/orders" \
  --collection=orders \
  --file=orders.json \
  --jsonArray
```

For BSON backups:

```bash
mongorestore \
  --uri="mongodb://localhost:27017" \
  ./dump
```

Do not assume that importing production data locally is safe.

Consider:

- PII
- Credentials
- Tokens
- Payment information
- Internal identifiers
- Regulatory requirements

## Local Configuration vs Production Configuration

Local configuration should be similar enough to expose integration issues but should not reuse production secrets.

| Configuration | Local | Production |
|---|---|---|
| MongoDB URI | Local service | Managed/private endpoint |
| Credentials | Development credentials | Secret manager |
| TLS | Optional depending on setup | Required |
| Authentication | Recommended for realistic testing | Required |
| Backup | Usually not required | Required |
| Replica set | Optional but useful | Common |
| Monitoring | Basic | Comprehensive |
| Network exposure | Local/private | Restricted |
| Data | Synthetic/sanitized | Production |

## Local Security

Even local MongoDB should not be exposed unnecessarily.

Avoid binding MongoDB publicly:

```yaml
ports:
  - "0.0.0.0:27017:27017"
```

Prefer limiting exposure to the host when host access is required:

```yaml
ports:
  - "127.0.0.1:27017:27017"
```

If the application and MongoDB both run inside Docker, the database often does not need to publish port `27017` to the host at all.

```yaml
services:
  api:
    build: .

  mongo:
    image: mongo:8.0
    volumes:
      - mongodb_data:/data/db
```

The API can access:

```text
mongodb://mongo:27017/orders
```

without exposing MongoDB externally.

## Local TLS

TLS is generally unnecessary for a simple single-developer localhost environment, but TLS can be useful when the goal is to reproduce production security behavior.

Testing TLS locally can expose:

- Certificate validation problems
- Incorrect CA configuration
- TLS hostname issues
- Driver configuration problems
- Secret distribution problems

This is particularly useful for teams whose production MongoDB requires TLS.

## Connection Timeouts

Local development should still use explicit connection timeouts.

Example:

```python
from pymongo import MongoClient

client = MongoClient(
    mongodb_uri,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
)
```

Without appropriate timeouts, an unavailable MongoDB instance can cause backend requests or startup operations to wait much longer than expected.

Timeout configuration should be appropriate for the application and environment rather than copied blindly from another system.

## Connection Pooling

PyMongo manages connection pooling internally.

A backend application should generally create one `MongoClient` per process and reuse it.

Avoid:

```python
def get_order():
    client = MongoClient(MONGODB_URI)
    ...
```

for every request.

Prefer:

```python
client = MongoClient(MONGODB_URI)

def get_order():
    return client.orders.orders.find_one(...)
```

This allows the driver to manage reusable connections efficiently.

## Performance Considerations

Local MongoDB performance differs from production because of:

- Local CPU
- Local RAM
- Disk type
- Docker filesystem behavior
- Dataset size
- Working set size
- Network latency
- Replica-set configuration
- Production hardware
- Production concurrency

Therefore:

> Local performance measurements should not be treated as production capacity measurements.

Local environments are excellent for:

- Query correctness
- Index verification
- Functional testing
- Query-plan inspection
- Application integration
- Failure simulation

They are poor substitutes for production-like load testing.

## Testing Query Plans Locally

Use realistic data volumes when testing query behavior.

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

A local query that works correctly can still be poorly indexed.

## Local Deployment Troubleshooting

### Connection Refused

```text
Symptom
↓
Connection refused on localhost:27017
↓
Possible causes
↓
MongoDB is stopped
Wrong port
Wrong hostname
Container is not running
Port is not published
↓
Isolation strategy
↓
Check MongoDB process and Docker container
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
mongosh "mongodb://localhost:27017"
```

```text
Root cause
↓
MongoDB process or networking configuration is unavailable
↓
Corrective action
↓
Start MongoDB or correct the connection URI
↓
Prevention
↓
Use health checks and deterministic environment configuration
```

### Authentication Failure

```text
Symptom
↓
Authentication failed
↓
Possible causes
↓
Incorrect username/password
Wrong authSource
User does not exist
Wrong database
↓
Isolation strategy
↓
Verify URI and authentication database
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
Application credentials do not match MongoDB authentication configuration
↓
Corrective action
↓
Correct credentials or create the required application user
↓
Prevention
↓
Manage credentials through environment configuration and initialization
```

### Application Cannot Reach MongoDB in Docker

```text
Symptom
↓
API container cannot connect to MongoDB
↓
Possible causes
↓
Using localhost
Different Docker networks
MongoDB not ready
Incorrect service name
↓
Isolation strategy
↓
Inspect Compose networking and container configuration
↓
Diagnostic commands
```

```bash
docker compose ps
```

```bash
docker compose logs mongo
```

From the API container, test the configured hostname using the tools available in that image.

```text
Root cause
↓
Container networking or service discovery configuration
↓
Corrective action
↓
Use the MongoDB Compose service name and shared network
↓
Prevention
↓
Keep environment-specific URIs in configuration
```

### Data Disappears After Container Recreation

```text
Symptom
↓
MongoDB data is missing after container recreation
↓
Possible causes
↓
No persistent volume
Wrong volume mounted
Volume deleted
Different Compose project
↓
Isolation strategy
↓
Inspect Docker volumes and Compose configuration
↓
Diagnostic commands
```

```bash
docker volume ls
```

```bash
docker inspect mongodb
```

```text
Root cause
↓
MongoDB data was stored only in the container filesystem
↓
Corrective action
↓
Use a persistent named volume
↓
Prevention
↓
Declare database storage explicitly in Compose
```

## Common Mistakes

### Using `localhost` from a Container

Incorrect:

```text
mongodb://localhost:27017/orders
```

when MongoDB is a separate Compose service.

Correct:

```text
mongodb://mongo:27017/orders
```

### Using the Root User From the Application

The root user has excessive privileges.

Use a dedicated application account with only the required permissions.

### Using `latest`

Avoid:

```yaml
image: mongo:latest
```

A version change can unexpectedly modify behavior between environments.

Prefer an explicitly controlled version:

```yaml
image: mongo:8.0
```

### Storing Database Credentials in Git

Avoid:

```python
MONGODB_URI = "mongodb://admin:password@localhost:27017/orders"
```

Use environment-based configuration.

### Running Production Data Locally

Production data may contain sensitive information and can create security and compliance risks.

Prefer synthetic or sanitized datasets.

### Treating Local Performance as Production Performance

Local benchmarks do not account for production hardware, concurrency, network latency, replication, storage, and workload characteristics.

### Ignoring Replica-Set Requirements

A standalone local server can hide issues that only appear with transactions, change streams, elections, or majority semantics.

Use a local replica set when those behaviors matter.

## Production-Like Local Development

A mature backend team can maintain two local profiles.

### Lightweight Profile

```text
API
 ↓
Standalone MongoDB
```

Used for:

- CRUD development
- Unit tests
- Basic integration tests
- Fast startup

### Production-Like Profile

```text
API
 ↓
MongoDB Replica Set
 ↓
Persistent Storage
```

Used for:

- Transactions
- Change streams
- Replica-set behavior
- Majority writes
- Failover experiments
- Integration testing

This avoids forcing every developer workflow to carry unnecessary operational complexity.

## Recommended Local Architecture

For a Python backend, a practical local setup is:

```mermaid
flowchart TB
    DEV[Developer]
    API[FastAPI / Django]
    REPO[Repository Layer]
    PY[PyMongo]
    MONGO[(MongoDB)]
    VOL[(Persistent Volume)]
    TOOLS[mongosh / Database Tools]

    DEV --> API
    API --> REPO
    REPO --> PY
    PY --> MONGO
    MONGO --> VOL
    DEV --> TOOLS
    TOOLS --> MONGO
```

Configuration should remain outside the application code:

```text
Environment
    ↓
MONGODB_URI
    ↓
Application Configuration
    ↓
MongoClient
    ↓
MongoDB
```

## Local Deployment Checklist

### Installation

- [ ] MongoDB server is installed or containerized.
- [ ] `mongosh` is available.
- [ ] MongoDB Database Tools are available when required.
- [ ] MongoDB version is explicitly controlled.

### Connectivity

- [ ] Local URI is documented.
- [ ] Docker service hostname is understood.
- [ ] Application connectivity is tested.
- [ ] Connection timeouts are configured.
- [ ] Health checks are available.

### Persistence

- [ ] Docker deployments use a persistent volume.
- [ ] Developers understand which operations delete local data.
- [ ] Reset procedures are documented.

### Application Integration

- [ ] MongoDB URI comes from configuration.
- [ ] PyMongo client is reused.
- [ ] Repository/service boundaries are defined.
- [ ] Required indexes are created.
- [ ] Seed data is reproducible.

### Security

- [ ] Production credentials are never used locally.
- [ ] Sensitive `.env` files are excluded from Git.
- [ ] MongoDB is not unnecessarily exposed.
- [ ] Authentication is enabled when production-like behavior is required.
- [ ] Local production-data usage is controlled.

### Production-Like Testing

- [ ] Replica-set mode is available when required.
- [ ] Transactions are tested where applicable.
- [ ] Change streams are tested where applicable.
- [ ] Query plans are inspected against realistic datasets.
- [ ] Integration tests can recreate the database environment.

## Interview Focus

Important local MongoDB deployment questions include:

| Question | Key point |
|---|---|
| Why use Docker for MongoDB locally? | Reproducibility and environment isolation |
| Why use a volume? | Container lifecycle should not determine data lifecycle |
| Why does `localhost` fail between containers? | `localhost` refers to the current container |
| Why use a replica set locally? | Transactions, change streams, and replica-set semantics |
| Why should `MongoClient` be reused? | It maintains and manages connection pools |
| Should local configuration match production exactly? | Behavior should be representative where important, but infrastructure and secrets should remain environment-specific |
| Can local MongoDB performance represent production? | No; local environments differ in hardware, workload, topology, and concurrency |
| Why should application users differ from root users? | Least privilege |
| Why pin the MongoDB image version? | Prevent unexpected environment changes |
| Why are health checks useful? | Process availability and dependency readiness are different concerns |

## Key Takeaways

- **Use Docker or another reproducible deployment mechanism when environment consistency matters; persist MongoDB data with explicit volumes.**
- **Use the correct hostname for the deployment topology: `localhost` for host-based access and the Compose service name for container-to-container access.**
- **Reuse a PyMongo `MongoClient`, externalize connection configuration, and use dedicated application credentials rather than administrative accounts.**
- **Use a local replica set when developing features that depend on transactions, change streams, majority semantics, or replica-set behavior.**
- **Treat local MongoDB as an integration environment: reproduce important production behavior without using production secrets or assuming local performance represents production capacity.**