# 02- Flow Log Analysis with Athena

## Overview

Amazon VPC Flow Logs provide network-flow metadata that can be stored in Amazon S3 and queried with Amazon Athena using SQL. This combination is particularly useful for production network troubleshooting, security investigation, traffic analysis, and historical analysis across large AWS environments.

The important architectural separation is:

```text
VPC
 |
 | Network traffic
 v
VPC Flow Logs
 |
 | Log delivery
 v
Amazon S3
 |
 | SQL query
 v
Amazon Athena
 |
 +--> Troubleshooting
 +--> Security Analysis
 +--> Traffic Analysis
 +--> Capacity Analysis
```

VPC Flow Logs do not capture packet payloads. They record metadata such as source and destination addresses, ports, protocol, packet and byte counts, timestamps, traffic action, and other fields depending on the configured flow-log format.

Athena provides a serverless SQL layer over those objects in S3. AWS provides documented Athena table definitions for VPC Flow Logs and also supports partition projection and Parquet-based configurations for larger environments. :contentReference[oaicite:0]{index=0}

For backend engineers, the practical value is straightforward: when an application reports a timeout or connection failure, Athena can answer questions such as:

- Which workload attempted the connection?
- Which destination was contacted?
- Which port was used?
- Was the flow accepted or rejected?
- Which interfaces are generating the most traffic?
- Which destinations receive unexpected traffic?
- Are rejected connections increasing?
- Is an application communicating outside its expected architecture?

## Why Use Athena for Flow Logs

CloudWatch Logs are useful for interactive operational troubleshooting, but S3 provides a durable location for large amounts of historical Flow Log data.

Athena allows that data to be queried without provisioning database infrastructure.

This creates a useful separation of responsibilities:

| Component | Responsibility |
|---|---|
| VPC Flow Logs | Capture network-flow metadata |
| Amazon S3 | Durable log storage |
| AWS Glue Data Catalog / Athena metadata | Describe the log schema |
| Amazon Athena | Execute SQL queries |
| IAM | Control access |
| CloudWatch / SIEM | Alerting and broader security operations |

AWS documents Athena as a supported way to query VPC Flow Logs stored in S3. The AWS VPC console can also generate an Athena integration through CloudFormation, including a database, workgroup, Flow Logs table, partitioning, and predefined queries. :contentReference[oaicite:1]{index=1}

## When Athena Is the Right Tool

Athena is particularly useful when the investigation requires historical or aggregate analysis.

Use it for:

- Investigating rejected connections over hours or days.
- Finding top talkers.
- Identifying unusual destination ports.
- Analyzing east-west traffic.
- Investigating network changes after deployments.
- Examining traffic across multiple accounts.
- Building repeatable security-analysis queries.
- Performing ad-hoc SQL analysis without maintaining a database.

Athena is less appropriate when you need:

- Packet payload inspection.
- Continuous packet-level analysis.
- Sub-second operational telemetry.
- Stateful network-flow processing.
- High-frequency transactional queries.

For those requirements, other observability or network-analysis systems may be more appropriate.

## Architecture

A production architecture commonly looks like:

```mermaid
flowchart LR
    subgraph AWS["AWS Environment"]
        VPC["Production VPC"]
        ENI["Network Interfaces"]
        FL["VPC Flow Logs"]
    end

    S3["Amazon S3\nFlow Log Storage"]
    Glue["Glue Catalog / Athena Metadata"]
    Athena["Amazon Athena"]
    Analysis["SQL Analysis"]
    SIEM["Security / SIEM"]
    Engineers["Engineering / Security Teams"]

    VPC --> ENI
    ENI --> FL
    FL --> S3
    S3 --> Glue
    Glue --> Athena
    Athena --> Analysis
    Athena --> SIEM
    Analysis --> Engineers
    SIEM --> Engineers
```

Flow Logs are collected outside the network traffic path, so enabling Flow Logs does not add network latency to application traffic. AWS notes that Flow Log data can be published to S3, CloudWatch Logs, or Amazon Data Firehose. :contentReference[oaicite:2]{index=2}

## Data Flow

The operational lifecycle is:

```text
Application
    |
    v
Network Interface
    |
    v
VPC Flow Log
    |
    v
S3 Object
    |
    v
Athena Table
    |
    v
SQL Query
    |
    v
Result
```

The application does not query Athena.

Athena reads the underlying S3 objects through the table definition.

This distinction matters because Athena is an analytical query engine rather than a database that owns or continuously ingests the log records.

## S3 Flow Log Layout

When VPC Flow Logs are delivered to S3, AWS organizes the objects under a structured prefix containing information such as the AWS account and Region. The exact layout depends on the Flow Log configuration and format. :contentReference[oaicite:3]{index=3}

A conceptual layout may look like:

```text
s3://central-vpc-flow-logs/
└── AWSLogs/
    └── 123456789012/
        └── vpcflowlogs/
            └── ap-south-1/
                ├── 2026/
                │   ├── 08/
                │   │   ├── 21/
                │   │   └── ...
```

For centralized multi-account logging, the account identifier becomes an important analytical dimension.

Do not assume that every environment uses exactly the same prefix. The Athena table's `LOCATION`, partition definitions, and schema must match the actual S3 layout.

## Flow Log Schema

The Athena schema must correspond to the fields and order configured in the VPC Flow Log format.

AWS provides examples covering Flow Log record versions and fields such as:

- `version`
- `account_id`
- `interface_id`
- `srcaddr`
- `dstaddr`
- `srcport`
- `dstport`
- `protocol`
- `packets`
- `bytes`
- `start`
- `end`
- `action`
- `log_status`
- `vpc_id`
- `subnet_id`
- `instance_id`
- `tcp_flags`
- `pkt_srcaddr`
- `pkt_dstaddr`
- `region`
- `flow_direction`
- `traffic_path`

The exact schema should match the fields configured for the Flow Log. AWS specifically recommends matching Athena column names to the Flow Log fields, replacing hyphens with underscores where required and escaping reserved Athena keywords. :contentReference[oaicite:4]{index=4}

## Creating an Athena Table

For text-formatted Flow Logs, a table can be created using a delimiter-based schema.

A simplified production-oriented example is:

```sql
CREATE EXTERNAL TABLE IF NOT EXISTS vpc_flow_logs (
    version int,
    account_id string,
    interface_id string,
    srcaddr string,
    dstaddr string,
    srcport int,
    dstport int,
    protocol bigint,
    packets bigint,
    bytes bigint,
    start bigint,
    `end` bigint,
    action string,
    log_status string,
    vpc_id string,
    subnet_id string,
    instance_id string,
    tcp_flags int,
    type string,
    pkt_srcaddr string,
    pkt_dstaddr string,
    region string,
    az_id string,
    sublocation_type string,
    sublocation_id string,
    pkt_src_aws_service string,
    pkt_dst_aws_service string,
    flow_direction string,
    traffic_path int
)
PARTITIONED BY (`date` date)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ' '
LOCATION 's3://central-vpc-flow-logs/AWSLogs/123456789012/vpcflowlogs/ap-south-1/';
```

This follows the structure of the AWS Athena example, but the S3 location and schema must be adapted to the actual Flow Log configuration. :contentReference[oaicite:5]{index=5}

### Important Schema Rule

Do not blindly copy a table definition from another environment.

If the Flow Log uses a custom format:

```text
field_a field_b field_c field_d
```

the Athena table must describe those fields in the same order and with compatible types.

A schema mismatch can produce:

- Incorrect values.
- Query failures.
- Misinterpreted columns.
- Silent analytical errors.

## Partitioning

Partitioning is one of the most important performance considerations when querying Flow Logs with Athena.

Without partition filtering, Athena may need to scan substantially more S3 data than necessary.

For example:

```text
Bad:
SELECT *
FROM vpc_flow_logs;
```

A better query restricts the relevant partition:

```sql
SELECT *
FROM vpc_flow_logs
WHERE `date` = DATE '2026-08-21'
LIMIT 100;
```

AWS documents partitioning Flow Logs by date and recommends partition projection as an option for automating partition discovery. :contentReference[oaicite:6]{index=6}

## Manual Partitioning

For a non-Hive-style Flow Log path, a partition can be registered explicitly:

```sql
ALTER TABLE vpc_flow_logs
ADD PARTITION (`date` = DATE '2026-08-21')
LOCATION 's3://central-vpc-flow-logs/AWSLogs/123456789012/vpcflowlogs/ap-south-1/2026/08/21/';
```

The exact path must match the actual S3 object layout.

Manual partitioning is acceptable for smaller environments but becomes operationally expensive when partitions are created continuously across:

- Many accounts.
- Many Regions.
- Many dates.
- Multiple environments.

## Partition Projection

Partition projection allows Athena to derive partition information from configured properties instead of requiring a separate metadata update for every partition.

This is particularly useful when Flow Logs are continuously generated.

A conceptual design is:

```text
S3
 |
 +-- account
 |
 +-- region
 |
 +-- date
 |
 v
Partition Projection
 |
 v
Athena
```

AWS provides partition-projection examples for VPC Flow Logs, including multi-account layouts where account ID, Region, and date are represented as projected partition columns. :contentReference[oaicite:7]{index=7}

A simplified example is:

```sql
CREATE EXTERNAL TABLE IF NOT EXISTS vpc_flow_logs_projected (
    version int,
    account_id string,
    interface_id string,
    srcaddr string,
    dstaddr string,
    srcport int,
    dstport int,
    protocol bigint,
    packets bigint,
    bytes bigint,
    start bigint,
    `end` bigint,
    action string,
    log_status string,
    vpc_id string,
    subnet_id string,
    instance_id string,
    tcp_flags int,
    type string,
    pkt_srcaddr string,
    pkt_dstaddr string,
    region string,
    az_id string,
    flow_direction string,
    traffic_path int
)
PARTITIONED BY (
    accid string,
    region_partition string,
    day string
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ' '
LOCATION 's3://central-vpc-flow-logs/AWSLogs/'
TBLPROPERTIES (
    'projection.enabled' = 'true',
    'projection.accid.type' = 'enum',
    'projection.accid.values' = '123456789012,210987654321',
    'projection.region_partition.type' = 'enum',
    'projection.region_partition.values' = 'ap-south-1,us-east-1',
    'projection.day.type' = 'date',
    'projection.day.range' = '2026/01/01,NOW',
    'projection.day.format' = 'yyyy/MM/dd',
    'storage.location.template' =
        's3://central-vpc-flow-logs/AWSLogs/${accid}/vpcflowlogs/${region_partition}/${day}'
);
```

This is a pattern rather than a drop-in configuration. The projected values and S3 template must correspond to the organization's actual account, Region, and object structure. AWS provides the authoritative syntax and layout examples. :contentReference[oaicite:8]{index=8}

## Parquet for Large Environments

Text Flow Logs are convenient, but large analytical workloads can benefit from Apache Parquet.

Parquet is columnar, which is well suited to analytical queries that select only a subset of fields.

For example:

```sql
SELECT
    srcaddr,
    dstaddr,
    dstport,
    SUM(bytes) AS total_bytes
FROM vpc_flow_logs
WHERE
    day >= '2026/08/01'
    AND day < '2026/09/01'
GROUP BY
    srcaddr,
    dstaddr,
    dstport;
```

If only these columns are required, a columnar format can avoid reading unrelated fields.

AWS provides Athena examples for VPC Flow Logs stored in Parquet and supports partitioning by account, Region, date, and hour. :contentReference[oaicite:9]{index=9}

### When to Prefer Parquet

Consider Parquet when:

- Flow Log volume is large.
- Queries are frequent.
- Analysts select a subset of columns.
- Scan-cost optimization matters.
- A centralized network-analytics platform is being built.

Do not migrate to Parquet solely because it is a popular format. The operational architecture should justify the additional pipeline and format-management complexity.

## Query Cost Model

Athena is serverless, but SQL queries still have a cost.

A poor query can scan a large amount of S3 data:

```sql
SELECT *
FROM vpc_flow_logs;
```

A better analytical query:

```sql
SELECT
    srcaddr,
    dstaddr,
    dstport,
    SUM(bytes) AS total_bytes
FROM vpc_flow_logs
WHERE `date` >= DATE '2026-08-20'
  AND `date` <= DATE '2026-08-21'
GROUP BY
    srcaddr,
    dstaddr,
    dstport;
```

The general principle is:

```text
Less data scanned
        |
        +--> Lower query cost
        |
        +--> Faster query
        |
        +--> Better analytical scalability
```

Partition pruning and column selection are therefore operational concerns, not merely SQL style preferences.

## Basic Flow Log Queries

### Inspect Recent Records

```sql
SELECT *
FROM vpc_flow_logs
WHERE `date` = CURRENT_DATE
LIMIT 100;
```

Use this for initial validation.

Avoid using `SELECT *` in expensive recurring analytical queries.

### Find Rejected Traffic

```sql
SELECT
    srcaddr,
    dstaddr,
    dstport,
    protocol,
    SUM(packets) AS packets,
    SUM(bytes) AS bytes
FROM vpc_flow_logs
WHERE `date` = CURRENT_DATE
  AND action = 'REJECT'
GROUP BY
    srcaddr,
    dstaddr,
    dstport,
    protocol
ORDER BY bytes DESC;
```

This is useful for identifying the dominant rejected traffic patterns.

AWS provides similar examples for querying rejected TCP traffic. :contentReference[oaicite:10]{index=10}

## Identify Top Talkers

A top-talker query identifies sources generating significant traffic.

```sql
SELECT
    srcaddr,
    SUM(bytes) AS total_bytes,
    SUM(packets) AS total_packets
FROM vpc_flow_logs
WHERE `date` >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY srcaddr
ORDER BY total_bytes DESC
LIMIT 20;
```

This can help identify:

- High-volume workloads.
- Unexpected data transfer.
- Batch jobs.
- Replication traffic.
- Potentially compromised hosts.

Volume alone is not evidence of malicious behavior. Always correlate with expected workload behavior.

## Identify Top Destinations

```sql
SELECT
    dstaddr,
    SUM(bytes) AS total_bytes,
    SUM(packets) AS total_packets
FROM vpc_flow_logs
WHERE `date` >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY dstaddr
ORDER BY total_bytes DESC
LIMIT 20;
```

This is useful for understanding traffic concentration.

## Find Common Destination Ports

```sql
SELECT
    dstport,
    COUNT(*) AS flow_count,
    SUM(bytes) AS total_bytes
FROM vpc_flow_logs
WHERE `date` = CURRENT_DATE
GROUP BY dstport
ORDER BY flow_count DESC
LIMIT 30;
```

This can reveal the actual service-port distribution of the environment.

For example:

```text
443   -> high
5432  -> expected
6379  -> expected
9092  -> expected
22    -> investigate
4444  -> investigate
```

Unexpected ports should be correlated with infrastructure and application changes before being treated as security incidents.

## Find Rejected PostgreSQL Connections

For a PostgreSQL workload:

```sql
SELECT
    srcaddr,
    dstaddr,
    srcport,
    dstport,
    SUM(packets) AS packets
FROM vpc_flow_logs
WHERE `date` >= CURRENT_DATE - INTERVAL '1' DAY
  AND dstport = 5432
  AND protocol = 6
  AND action = 'REJECT'
GROUP BY
    srcaddr,
    dstaddr,
    srcport,
    dstport
ORDER BY packets DESC;
```

This can help investigate:

```text
Django/FastAPI
      |
      | TCP :5432
      v
PostgreSQL
```

If the query reveals repeated rejected connections, inspect:

- Application Security Group.
- Database Security Group.
- NACLs.
- Route tables.
- Database endpoint.
- Actual destination IP.
- Recent infrastructure changes.

## Find Unexpected SSH Traffic

```sql
SELECT
    srcaddr,
    dstaddr,
    COUNT(*) AS rejected_flows,
    SUM(bytes) AS total_bytes
FROM vpc_flow_logs
WHERE `date` >= CURRENT_DATE - INTERVAL '1' DAY
  AND dstport = 22
  AND action = 'REJECT'
GROUP BY
    srcaddr,
    dstaddr
ORDER BY rejected_flows DESC;
```

This can help identify:

- Misconfigured administration tooling.
- Unauthorized access attempts.
- Security scanning.
- Unexpected internal traffic.

A rejected SSH attempt is not automatically malicious.

## Identify External Traffic

For security analysis, separate private and public addressing carefully.

A simplistic query based solely on string comparisons is not sufficient for robust CIDR classification.

A better architecture is to maintain an inventory mapping:

```text
IP/CIDR
   |
   +--> VPC
   +--> Subnet
   +--> Environment
   +--> Application
   +--> Owner
```

Then enrich Flow Log data before performing security analysis.

This is an important senior-level principle:

> Raw network telemetry becomes significantly more useful when correlated with infrastructure metadata.

## Internal East-West Traffic

East-west traffic refers to traffic between workloads inside an environment.

For a microservices architecture:

```text
orders
  |
  v
payments
  |
  v
inventory
  |
  v
postgres
```

Flow Logs can help validate whether the actual traffic matches the intended service topology.

Unexpected traffic such as:

```text
orders -> database
payments -> unrelated-service
inventory -> administrative-host
```

may indicate:

- Excessive network permissions.
- Architecture drift.
- Misconfigured service discovery.
- Compromised workloads.

## Detecting Network Architecture Drift

Suppose the intended architecture allows:

```text
API -> Redis
API -> PostgreSQL
Worker -> PostgreSQL
Worker -> Kafka
```

but Flow Logs reveal:

```text
API -> Kafka
API -> PostgreSQL
API -> Redis
Worker -> PostgreSQL
Worker -> Kafka
Worker -> Elasticsearch
```

The unexpected `API -> Kafka` or `Worker -> Elasticsearch` traffic should be investigated.

The important point is that Flow Logs can provide evidence of **actual** communication rather than relying solely on declared architecture.

## Rejected Traffic Analysis

A useful rejected-traffic investigation groups records by multiple dimensions:

```text
Source
Destination
Port
Protocol
Action
Time
```

For example:

```sql
SELECT
    srcaddr,
    dstaddr,
    dstport,
    protocol,
    COUNT(*) AS flow_count,
    SUM(bytes) AS bytes
FROM vpc_flow_logs
WHERE `date` >= CURRENT_DATE - INTERVAL '7' DAY
  AND action = 'REJECT'
GROUP BY
    srcaddr,
    dstaddr,
    dstport,
    protocol
ORDER BY flow_count DESC
LIMIT 100;
```

This is more useful than simply counting all rejected traffic because it identifies the actual communication patterns.

## Traffic Baselines

A mature environment should establish expected traffic baselines.

For example:

```text
Normal daily traffic:

443   -> 70%
5432  -> 15%
6379  -> 5%
9092  -> 7%
Other -> 3%
```

A sudden change:

```text
443   -> 40%
5432  -> 10%
6379  -> 5%
9092  -> 5%
22    -> 20%
Other -> 20%
```

should trigger investigation.

Baseline analysis can be performed by:

- Application.
- VPC.
- Subnet.
- Source workload.
- Destination.
- Port.
- Environment.
- AWS account.
- Region.

## Time-Based Analysis

Flow Logs include start and end timestamps.

For operational analysis, it is useful to group traffic into time windows.

Conceptually:

```text
00:00 ─────────────── 06:00
        |
        +--> Normal

06:00 ─────────────── 12:00
        |
        +--> Traffic increase

12:00 ─────────────── 18:00
        |
        +--> Deployment

18:00 ─────────────── 24:00
        |
        +--> Rejected traffic spike
```

This can be correlated with:

- CI/CD deployments.
- Kubernetes rollouts.
- EC2 scaling.
- Batch jobs.
- Database maintenance.
- Security incidents.

## Flow Logs and Incident Response

A practical incident workflow is:

```mermaid
flowchart TD
    Incident["Network / Security Incident"]
    Scope["Identify affected workload"]
    Query["Query Flow Logs"]
    Pattern["Analyze source / destination / port"]
    Policy["Inspect SG / NACL / Route"]
    Change["Correlate infrastructure changes"]
    App["Correlate application logs"]
    Root["Determine root cause"]
    Action["Remediation"]

    Incident --> Scope
    Scope --> Query
    Query --> Pattern
    Pattern --> Policy
    Pattern --> Change
    Pattern --> App
    Policy --> Root
    Change --> Root
    App --> Root
    Root --> Action
```

This prevents a common operational mistake: changing network rules before establishing evidence.

## Troubleshooting a Django or FastAPI Timeout

Suppose an application reports:

```text
connection timed out
```

Start with the intended network path:

```text
Django / FastAPI
      |
      v
Application ENI
      |
      v
Route Table
      |
      v
Database Subnet
      |
      v
PostgreSQL :5432
```

Then query:

```sql
SELECT
    srcaddr,
    dstaddr,
    srcport,
    dstport,
    protocol,
    action,
    SUM(packets) AS packets,
    SUM(bytes) AS bytes
FROM vpc_flow_logs
WHERE `date` = CURRENT_DATE
  AND dstport = 5432
  AND protocol = 6
GROUP BY
    srcaddr,
    dstaddr,
    srcport,
    dstport,
    protocol,
    action
ORDER BY packets DESC;
```

Interpretation:

```text
REJECT
  |
  +--> Investigate network controls

ACCEPT
  |
  +--> Investigate destination/service/application layers
```

An `ACCEPT` record does not prove that PostgreSQL accepted the connection.

## Multi-Account Analysis

A centralized AWS organization may contain:

```text
Management
   |
   +-- Production
   |
   +-- Staging
   |
   +-- Development
   |
   +-- Security
   |
   +-- Shared Services
```

Flow Logs can be centralized into an S3-based analytics architecture.

The account ID should remain part of the analytical model:

```text
account_id
region
vpc_id
subnet_id
interface_id
srcaddr
dstaddr
```

This enables questions such as:

```sql
SELECT
    account_id,
    region,
    SUM(bytes) AS total_bytes
FROM vpc_flow_logs
WHERE `date` >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY
    account_id,
    region
ORDER BY total_bytes DESC;
```

Centralized analysis is particularly valuable for security teams because it allows network behavior to be compared across accounts.

## Athena Workgroups

Athena workgroups can be used to separate analytical workloads and apply operational controls.

For example:

```text
network-security
    |
    +--> Security queries

network-operations
    |
    +--> Troubleshooting

network-analytics
    |
    +--> Historical reporting
```

Workgroup design can help organizations separate:

- Query ownership.
- Query configuration.
- Cost monitoring.
- Access control.
- Operational responsibilities.

The exact governance model should match the organization's AWS account and IAM architecture.

## Query Optimization

### Filter Partitions

Prefer:

```sql
WHERE `date` >= DATE '2026-08-20'
  AND `date` < DATE '2026-08-22'
```

over:

```sql
SELECT *
FROM vpc_flow_logs;
```

### Select Required Columns

Prefer:

```sql
SELECT
    srcaddr,
    dstaddr,
    dstport,
    bytes
FROM vpc_flow_logs;
```

instead of:

```sql
SELECT *
FROM vpc_flow_logs;
```

### Aggregate in Athena

Prefer:

```sql
SELECT
    dstport,
    SUM(bytes) AS total_bytes
FROM vpc_flow_logs
WHERE `date` = CURRENT_DATE
GROUP BY dstport;
```

instead of exporting millions of raw records and aggregating them externally.

### Avoid Unbounded Historical Queries

A query covering years of logs may be valid but operationally expensive.

Start narrow:

```text
1 day
  |
  v
7 days
  |
  v
30 days
  |
  v
Long-term historical analysis
```

Expand the range only when necessary.

## Partition Projection vs Manual Partitions

| Approach | Best Fit | Operational Complexity |
|---|---|---|
| Manual partitions | Small or static datasets | Higher over time |
| `MSCK REPAIR TABLE` | Hive-compatible partition layouts | Moderate |
| Partition projection | Continuously generated Flow Logs | Lower metadata maintenance |
| Parquet + projection | Large analytical environments | Strong scalability, more design complexity |

AWS notes that `MSCK REPAIR TABLE` is appropriate for Hive-compatible partition layouts, while non-Hive layouts can use `ALTER TABLE ADD PARTITION`. :contentReference[oaicite:11]{index=11}

## `MSCK REPAIR TABLE`

For Hive-compatible partition layouts:

```sql
MSCK REPAIR TABLE vpc_flow_logs;
```

This updates the table's partition metadata based on the S3 layout.

However, this should not automatically be considered the best solution for every production environment.

For continuously growing, large-scale Flow Log datasets, partition projection can reduce partition-management overhead.

## Schema Evolution

Flow Log formats can evolve as AWS adds fields or as organizations customize their configurations.

This creates an operational requirement:

```text
Flow Log Configuration
        |
        v
S3 Data Format
        |
        v
Athena Table Schema
        |
        v
Queries
```

These components must remain compatible.

When changing a Flow Log format:

1. Review the new field set.
2. Update the Athena schema.
3. Validate historical compatibility.
4. Test representative queries.
5. Deploy the change through Infrastructure as Code where applicable.

Do not silently change a production schema and assume all analytical queries remain valid.

## Security and IAM

Athena-based Flow Log analysis often involves sensitive infrastructure information.

An analyst may be able to infer:

```text
Application A
   |
   +--> Database B
   |
   +--> Redis C
   |
   +--> Kafka D
```

Therefore access should be controlled.

Recommended controls include:

- Least-privilege S3 access.
- Least-privilege Athena access.
- Restricted Glue Catalog permissions.
- Encryption for S3 data.
- Encryption for Athena query results.
- Separate security and application roles.
- Audit access to sensitive log data.
- Protect the central logging account.

The security model should cover both:

```text
Source Logs
    |
    v
S3
```

and:

```text
Athena Query Results
    |
    v
S3 Query Results Location
```

## Query Result Security

Athena query results are stored separately from the source Flow Logs.

Therefore:

```text
Flow Logs
    |
    v
Source S3 Bucket

Athena Query
    |
    v
Query Result S3 Location
```

Both locations require appropriate access controls.

A common mistake is to secure the source bucket while leaving query results overly permissive.

## Cost Management

Athena pricing is influenced by the amount of data scanned by queries.

Therefore the following have direct operational value:

- Partition pruning.
- Column selection.
- Appropriate file formats.
- Query limits.
- Controlled historical ranges.
- Workgroup governance.
- Query review.
- Data lifecycle policies.

A useful mental model is:

```text
Raw Logs
   |
   v
Partitioning
   |
   v
Column Selection
   |
   v
Efficient Query
   |
   v
Less Data Scanned
```

For high-volume environments, evaluate whether Parquet and other columnar optimizations justify the additional ingestion architecture.

## Monitoring Athena Analysis

Monitor the analytical platform itself.

Useful operational signals include:

- Query execution failures.
- Query duration.
- Data scanned.
- Frequent expensive queries.
- Unexpected query volume.
- Failed partition discovery.
- S3 access failures.
- Schema mismatches.
- Missing Flow Log data.

This creates two distinct observability layers:

```text
Layer 1:
VPC Traffic
    |
    v
Flow Logs

Layer 2:
Flow Log Analytics
    |
    v
Athena / S3 / Catalog
```

Both need operational ownership.

## Common Mistakes

### Querying Without Partition Filters

Bad:

```sql
SELECT *
FROM vpc_flow_logs;
```

Why it is a problem:

- More data may be scanned.
- Queries become slower.
- Costs can increase.
- Analysts may accidentally run expensive workloads.

Prefer targeted time ranges and partition filters.

### Assuming the Athena Schema Is Universal

Different Flow Log configurations can contain different fields.

**Avoid it:** derive the Athena schema from the actual Flow Log format.

### Forgetting Partition Metadata

A table can exist while queries return no data because the required partitions are not registered or projected correctly.

**Avoid it:** verify the S3 path, partition configuration, and metadata.

### Treating `ACCEPT` as Application Success

An accepted flow does not mean the application succeeded.

**Avoid it:** correlate with application and service telemetry.

### Treating `REJECT` as Automatically Malicious

A rejected flow may simply represent a broken application configuration.

**Avoid it:** investigate the source, destination, port, expected architecture, and timing.

### Using `SELECT *` for Recurring Analytics

This reads columns that may not be needed.

**Avoid it:** explicitly select the required columns.

### Ignoring Query Results Security

Athena results are stored separately from the source logs.

**Avoid it:** protect both the source data and query-result locations.

### Using Manual Partitions at Large Scale

Manual partition management becomes operationally expensive across many accounts, Regions, and dates.

**Avoid it:** evaluate partition projection and automated metadata management.

### Treating Raw IP Addresses as Application Identity

IP addresses alone are often insufficient to determine ownership.

**Avoid it:** enrich traffic analysis with VPC, subnet, interface, instance, Kubernetes, ECS, or application metadata.

## Production Design Recommendations

For a production Flow Log analytics platform:

| Area | Recommendation |
|---|---|
| Storage | Use centralized S3 where organizationally appropriate |
| Schema | Match the actual Flow Log format |
| Partitioning | Partition by useful dimensions such as date |
| Large scale | Evaluate partition projection |
| File format | Evaluate Parquet for high-volume analytics |
| Queries | Require partition filtering |
| Security | Apply least-privilege IAM |
| Encryption | Protect source and query-result data |
| Governance | Use Athena workgroups where useful |
| Retention | Define hot and long-term retention separately |
| Analysis | Maintain reusable operational/security queries |
| Metadata | Enrich IPs and interfaces with ownership information |
| Automation | Manage infrastructure and schemas through IaC |
| Monitoring | Monitor both Flow Log delivery and Athena workloads |

## Recommended Investigation Query Set

A production team should maintain a small library of tested queries.

At minimum:

```text
01. Recent flow records
02. Rejected traffic
03. Top source IPs
04. Top destination IPs
05. Top destination ports
06. Rejected PostgreSQL traffic
07. Rejected HTTPS traffic
08. Unexpected administrative ports
09. Highest-volume interfaces
10. East-west traffic
11. External destinations
12. Traffic by account
13. Traffic by VPC
14. Traffic by subnet
15. Traffic over time
```

This is significantly more useful during an incident than writing every query from scratch.

## Example Query Library

### Highest-Volume Interfaces

```sql
SELECT
    interface_id,
    SUM(bytes) AS total_bytes,
    SUM(packets) AS total_packets
FROM vpc_flow_logs
WHERE `date` >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY interface_id
ORDER BY total_bytes DESC
LIMIT 20;
```

### Most Rejected Destinations

```sql
SELECT
    dstaddr,
    dstport,
    COUNT(*) AS rejected_flows
FROM vpc_flow_logs
WHERE `date` >= CURRENT_DATE - INTERVAL '7' DAY
  AND action = 'REJECT'
GROUP BY dstaddr, dstport
ORDER BY rejected_flows DESC
LIMIT 50;
```

### Traffic by Protocol

```sql
SELECT
    protocol,
    SUM(packets) AS packets,
    SUM(bytes) AS bytes
FROM vpc_flow_logs
WHERE `date` = CURRENT_DATE
GROUP BY protocol
ORDER BY bytes DESC;
```

### Traffic by VPC

```sql
SELECT
    vpc_id,
    SUM(bytes) AS total_bytes,
    SUM(packets) AS total_packets
FROM vpc_flow_logs
WHERE `date` >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY vpc_id
ORDER BY total_bytes DESC;
```

## Operational Checklist

Before relying on Athena for production Flow Log analysis:

- [ ] VPC Flow Logs are enabled for the required resources.
- [ ] Flow Logs are delivered to the intended S3 location.
- [ ] S3 permissions follow least privilege.
- [ ] S3 encryption is configured appropriately.
- [ ] Athena can read the Flow Log objects.
- [ ] The Athena schema matches the Flow Log format.
- [ ] Partitions or partition projection are configured correctly.
- [ ] Queries use partition filters.
- [ ] Query results are stored securely.
- [ ] Athena workgroups are configured where useful.
- [ ] Common troubleshooting queries are available.
- [ ] Security-analysis queries are available.
- [ ] Flow Log data retention is defined.
- [ ] Large-volume environments have evaluated Parquet.
- [ ] Multi-account environments preserve account identity.
- [ ] Network telemetry is correlated with infrastructure ownership.
- [ ] Query costs and execution behavior are monitored.
- [ ] Schema changes are tested before production rollout.
- [ ] Infrastructure and Athena configuration are managed consistently.

## Interview Traps

### Is Athena a database for Flow Logs?

No.

Athena is a serverless interactive query service that reads data stored in services such as S3.

The underlying architecture is:

```text
S3
 |
 v
Athena
 |
 v
SQL Results
```

### Does Athena Ingest Flow Logs?

Not in the traditional database-ingestion sense.

Flow Logs are delivered to S3, and Athena queries the objects through a table definition.

### Why Partition Flow Logs?

To reduce unnecessary data scanning and improve query performance.

### Why Use Parquet?

Parquet is a columnar format that can be advantageous for analytical workloads because queries can read only the required columns.

### Does Partitioning Change the Flow Logs?

No.

Partitioning organizes how Athena locates the data. It does not alter the network-flow records themselves.

### Does Athena Replace CloudWatch Logs?

Not necessarily.

The services address different operational patterns.

```text
CloudWatch Logs
    |
    +--> Operational / interactive analysis

S3 + Athena
    |
    +--> Historical / analytical analysis
```

### Can Athena Tell You Why a Packet Was Rejected?

It can provide evidence that a flow was recorded as `REJECT`, along with the associated metadata.

It does not replace analysis of:

- Security Groups.
- Network ACLs.
- Route tables.
- Network topology.
- Application configuration.

## Key Takeaways

- **Athena turns S3-based VPC Flow Logs into queryable network telemetry**, enabling SQL-based troubleshooting, security analysis, traffic analysis, and historical investigation.
- **Partitioning and query design are production concerns**: restrict time ranges, select only required columns, and evaluate partition projection for continuously generated logs.
- **Large-scale environments should evaluate Parquet and centralized analytics**, especially when Flow Logs span many accounts, Regions, and high traffic volumes.
- **Flow Log analysis is most valuable when enriched with infrastructure context**, connecting IP addresses and interfaces to VPCs, subnets, workloads, applications, and ownership.
- **Protect the complete analytics pipeline**, including Flow Log storage, Athena metadata, query execution, query-result locations, IAM permissions, encryption, retention, and cost controls.