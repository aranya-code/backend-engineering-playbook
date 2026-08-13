# Interview Questions: System Design Scenarios

This section provides detailed, senior-level system design questions and model answers focusing on real-world database scaling, migrations, and high-load traffic handling.

---

# Scalability and Performance Scenarios

## Q1: How would you design a database architecture for a flash sale platform expecting a 100x spike in traffic?

A flash sale requires high-throughput, low-latency writes and reads for hot inventory items, preventing race conditions (over-selling).

```text
                               Flash Sale Architecture:
                               
User Traffic ──► Route 53 ──► CloudFront ──► ALB ──► EKS Application
                                                      │
             ┌────────────────────────────────────────┴───────────────────────┐
             ▼ (Stock Reads - Sub-ms)                                         ▼ (Purchase Writes - High Scale)
     ElastiCache Redis                                                Amazon DynamoDB
     (Holds inventory counts)                                         (Orders table - Partition Key: OrderId)
     ├── Hash Tags {} for atomic decr                                 ├── Strong consistency for order check
     └── Lua Script (Check-and-Decrement)                             └── DynamoDB Streams ──► SQS (Post-processing)
```

- **Read Scaling (Inventory Check)**:
  - Cache inventory counts in **Amazon ElastiCache for Redis**. Use a **Lua Script** to perform atomic "check-and-decrement" operations. This ensures that stock is only decremented if it is greater than zero, preventing race conditions.
  - Lua scripts run atomically on the single Redis thread, avoiding the need for distributed database locks.
- **Write Scaling (Order Placement)**:
  - Write orders to **Amazon DynamoDB** configured with **On-Demand Capacity Mode** to absorb the write spike, or pre-warm Provisioned Capacity.
  - Design the DynamoDB partition key around `OrderId` or a composite key (`UserId + SaleId`) to distribute writes evenly across physical partitions.
- **Post-Processing (Asynchronous Workloads)**:
  - Enable **DynamoDB Streams** to capture order creations.
  - Stream events to Lambda to send confirmations, generate invoices, and update shipping tables asynchronously, keeping the main purchase path clean and fast.

---

## Q2: How would you perform a database migration from an on-premises database to Amazon RDS with zero downtime?

Zero-downtime migration requires setting up replication between the source and target databases before cutting over traffic.

```text
Source Database (On-Premises)
       │
       ▼ (Reads/Writes from active users)
   AWS DMS Replication Instance
   ├── Full Load (Initial copy)
   └── Change Data Capture (CDC - Continuous sync)
       │
       ▼
Target Database (Amazon RDS - Encrypted)
```

### Steps of the Migration

1. **Prerequisites**: Deploy the target RDS database in private subnets, enable encryption at rest, and establish network connectivity (VPN or Direct Connect) between on-premises and AWS.
2. **AWS DMS Setup**: Spin up an **AWS Database Migration Service (DMS)** replication instance. Configure a migration task with two phases:
   - **Full Load**: Copies all active tables from the source database to the target RDS database.
   - **Change Data Capture (CDC)**: Captures ongoing transactions from the database engine's transaction log (binlog/WAL) and replays them on the target RDS instance in real time.
3. **Validation**: Monitor the DMS task and compare row counts and checksums between the source and target.
4. **Traffic Cutover**:
   - Once replication lag is near zero, temporarily set the application to read-only mode to prevent new writes.
   - Wait for the final CDC changes to sync.
   - Update application connection strings (or Route 53 CNAMEs) to point to the new RDS endpoint.
   - Switch the application back to write mode.
   - Terminate the DMS task and the source database.

---

# Connection Management Scenarios

## Q3: Your application is experiencing database connection exhaustion. How do you diagnose and resolve this?

- **Diagnostic Steps**:
  - Monitor **`DatabaseConnections`** in CloudWatch to confirm the database has reached its maximum connection limit (often defined by `max_connections` in parameter groups, which defaults to a value scaled based on instance memory).
  - Check application logs for connection timeouts or `Too many connections` errors.
  - Use **Enhanced Monitoring** at 1-second intervals to check if the connection spike is causing CPU/Memory saturation.
- **Resolution Path**:
  - **Deploy RDS Proxy**: Place RDS Proxy between the application and the database. RDS Proxy pools database connections and multiplexes active queries over a smaller set of connections, preventing connection saturation.
  - **Optimize Client Connection Pools**: Configure client-side connection pooling (e.g., HikariCP) to set a maximum limit on connection allocation per application pod.
  - **Serverless Scaling Controls**: If the connections are coming from Lambda, restrict the maximum concurrency of the Lambda functions or route them through RDS Proxy.
  - **Verify Connection Leaks**: Check application code for unclosed database sessions (e.g., failing to close connections in `finally` blocks).

---

# Key Takeaways

- Scale high-throughput reads/writes during sales using **ElastiCache for stock checks (Lua scripts)** and **DynamoDB for order capturing**.
- Perform zero-downtime migrations using **AWS DMS (Full Load + CDC)**.
- Handle connection exhaustion by deploying **RDS Proxy** and optimizing client-side connection pools.
- Monitor active database sessions (AAS) in Performance Insights to quickly identify locked or long-running queries during incidents.

---
