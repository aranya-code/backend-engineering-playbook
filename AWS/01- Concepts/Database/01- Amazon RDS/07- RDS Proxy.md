# RDS Proxy

As applications scale, managing database connections becomes a major bottleneck. Relational databases like MySQL and PostgreSQL allocate memory and process limits to each active connection. When serverless architectures (like AWS Lambda) scale out to thousands of parallel instances, they can easily overwhelm the database with connection requests. 

**RDS Proxy** is a fully managed, highly available database proxy that pools and shares database connections, improving application scalability, resiliency, and security.

---

# The Connection Problem in Serverless Architectures

In traditional architectures, application servers use a connection pool (e.g., HikariCP, pgpool) to reuse a set of persistent database connections. 

In serverless architectures, Lambda functions scale out instantly and independently:

```text
Serverless Scaling (Anti-Pattern):
Lambda (1)  ──► Establishes Connection ┐
Lambda (2)  ──► Establishes Connection ┼─► Primary DB (Max Connections Limit Reached!)
Lambda (3)  ──► Establishes Connection │   (CPU Spikes, Client Connection Failures)
Lambda (N)  ──► Establishes Connection ┘

With RDS Proxy (Best Practice):
Lambda (1)  ──┐
Lambda (2)  ──┼─► RDS Proxy (Connection Pool) ──► Shared Connections ──► Primary DB
Lambda (3)  ──┤   (Reuses DB Connections)        (Steady State)
Lambda (N)  ──┘
```

Without a proxy, database connection overhead (CPU and memory consumption per connection) limits the scalability of your application.

---

# Key Features of RDS Proxy

## 1. Connection Pooling

RDS Proxy maintains a pool of established connections to the database. Instead of establishing a new connection for every request, your application connects to the proxy, which multiplexes multiple client requests over a smaller pool of database connections.

## 2. Faster Failover Resiliency

During a Multi-AZ database failover, client connections are dropped as DNS records update (which can take 60–120 seconds due to client DNS caching). 

With RDS Proxy:
- Client connections to the proxy are preserved.
- The proxy detects the failover, establishes connections to the newly promoted primary database, and routes queries directly.
- **Result**: Failover times are reduced by up to **66%**, and the application experiences transient delay instead of connection drop errors.

```text
Failover Flow with RDS Proxy:

Primary DB (AZ-1) Fails  ──►  RDS Proxy holds client requests in queue
                                       │
Standby promoted (AZ-2)  ◄──  RDS Proxy connects to new Primary
                                       │
Query execution resumes  ──►  No connection dropped at application!
```

## 3. Improved Security

- **IAM Authentication**: You can connect to RDS Proxy using IAM authentication, even if the backend database uses standard username/password authentication.
- **Secrets Manager Integration**: RDS Proxy retrieves database credentials securely from AWS Secrets Manager and handles the backend authentication transparently.

---

# Connection Pinning

Connection Pinning is a condition where RDS Proxy cannot safely share a database connection and must tie a client session to a single physical database connection, bypassing the benefits of pooling.

## Causes of Connection Pinning

- **Session State Changes**: Using commands that alter session variables (e.g., `SET timezone` in PostgreSQL).
- **Temporary Tables**: Creating temporary tables during a session.
- **Prepared Statements**: Preparing SQL queries on the connection.
- **Locking operations**: Running active locks (`LOCK TABLE`).

## Mitigating Pinning

- Avoid session-level configuration changes in application code; configure these at the parameter group level.
- Close temporary resources immediately after use.
- Monitor the `DatabaseConnectionsPinned` metric in CloudWatch.

---

# Configuration and Limits

- **Engines Supported**: MySQL, PostgreSQL, MariaDB, and Amazon Aurora.
- **Multi-AZ Support**: RDS Proxy is deployed across multiple Availability Zones automatically for high availability.
- **VPC Requirement**: RDS Proxy runs inside your VPC. Applications must have network access to the proxy endpoints.
- **Active-Passive Routing**: For RDS instances, RDS Proxy routes write traffic to the primary instance. It can also route read traffic to read replicas via separate reader endpoints.

---

# Key Takeaways

- **RDS Proxy** is designed to pool connections, protecting databases from serverless traffic spikes (AWS Lambda).
- It reduces failover recovery time by preserving client connections during AZ failovers.
- Integrate with **Secrets Manager** to manage database credentials and use **IAM Authentication** to access the proxy securely.
- Watch out for **Connection Pinning**, which disables multiplexing and locks client connections to physical backend connections.
- Ensure applications run inside the same VPC to access the RDS Proxy endpoint.

---
