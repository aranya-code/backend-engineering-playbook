Database/
│
├── README.md
│
├── 00- Fundamentals/
│   ├── 01- SQL vs NoSQL.md
│   ├── 02- OLTP vs OLAP.md
│   ├── 03- CAP Theorem.md
│   ├── 04- ACID Properties.md
│   ├── 05- BASE Model.md
│   ├── 06- Consistency Models.md
│   ├── 07- Database Indexing.md
│   ├── 08- Database Normalization.md
│   ├── 09- Database Denormalization.md
│   ├── 10- Database Partitioning.md
│   ├── 11- Database Sharding.md
│   ├── 12- Replication.md
│   ├── 13- Backup & Recovery.md
│   ├── 14- High Availability.md
│   ├── 15- Disaster Recovery.md
│   └── 16- Database Selection Guide.md
│
├── 01- Amazon RDS/
│   ├── 01- Overview.md
│   ├── 02- Architecture.md
│   ├── 03- Supported Engines.md
│   ├── 04- Storage Types.md
│   ├── 05- Instance Classes.md
│   ├── 06- Networking.md
│   ├── 07- Security.md
│   ├── 08- Encryption.md
│   ├── 09- IAM Authentication.md
│   ├── 10- Parameter Groups.md
│   ├── 11- Option Groups.md
│   ├── 12- Automated Backups.md
│   ├── 13- Manual Snapshots.md
│   ├── 14- Point-in-Time Recovery.md
│   ├── 15- Read Replicas.md
│   ├── 16- Multi-AZ.md
│   ├── 17- Multi-AZ DB Cluster.md
│   ├── 18- Storage Auto Scaling.md
│   ├── 19- Maintenance Windows.md
│   ├── 20- RDS Proxy.md
│   ├── 21- Performance Insights.md
│   ├── 22- Enhanced Monitoring.md
│   ├── 23- CloudWatch Integration.md
│   ├── 24- Scaling Strategies.md
│   ├── 25- Cost Optimization.md
│   ├── 26- Best Practices.md
│   ├── 27- Troubleshooting.md
│   ├── 28- Common Interview Questions.md
│   └── 29- Quick Revision.md
│
├── 02- Amazon Aurora/
│   ├── 01- Overview.md
│   ├── 02- Architecture.md
│   ├── 03- Distributed Storage.md
│   ├── 04- Aurora Replicas.md
│   ├── 05- Reader Endpoint.md
│   ├── 06- Writer Endpoint.md
│   ├── 07- Aurora Serverless v2.md
│   ├── 08- Aurora Global Database.md
│   ├── 09- Backtrack.md
│   ├── 10- Failover.md
│   ├── 11- Security.md
│   ├── 12- Monitoring.md
│   ├── 13- Aurora vs RDS.md
│   ├── 14- Best Practices.md
│   ├── 15- Interview Questions.md
│   └── 16- Quick Revision.md
│
├── 03- Amazon DynamoDB/
│   ├── 01- Overview.md
│   ├── 02- Architecture.md
│   ├── 03- Primary Keys.md
│   ├── 04- Secondary Indexes.md
│   ├── 05- Read Consistency.md
│   ├── 06- Capacity Modes.md
│   ├── 07- Auto Scaling.md
│   ├── 08- DynamoDB Streams.md
│   ├── 09- Global Tables.md
│   ├── 10- Transactions.md
│   ├── 11- TTL.md
│   ├── 12- DAX.md
│   ├── 13- Security.md
│   ├── 14- Monitoring.md
│   ├── 15- Best Practices.md
│   ├── 16- Common Mistakes.md
│   ├── 17- Interview Questions.md
│   └── 18- Quick Revision.md
│
├── 04- Amazon ElastiCache/
│   ├── 01- Overview.md
│   ├── 02- Redis.md
│   ├── 03- Memcached.md
│   ├── 04- Cache Patterns.md
│   ├── 05- Cache Aside.md
│   ├── 06- Read Through.md
│   ├── 07- Write Through.md
│   ├── 08- Write Back.md
│   ├── 09- TTL.md
│   ├── 10- Eviction Policies.md
│   ├── 11- Redis Cluster.md
│   ├── 12- Replication.md
│   ├── 13- Security.md
│   ├── 14- Monitoring.md
│   ├── 15- Best Practices.md
│   ├── 16- Cache Stampede.md
│   ├── 17- Cache Penetration.md
│   ├── 18- Cache Avalanche.md
│   ├── 19- Interview Questions.md
│   └── 20- Quick Revision.md
│
├── 05- Amazon MemoryDB/
│   ├── 01- Overview.md
│   ├── 02- Architecture.md
│   ├── 03- Durability.md
│   ├── 04- High Availability.md
│   ├── 05- Security.md
│   ├── 06- Monitoring.md
│   ├── 07- MemoryDB vs ElastiCache.md
│   ├── 08- Best Practices.md
│   ├── 09- Interview Questions.md
│   └── 10- Quick Revision.md
│
├── 06- Amazon DocumentDB/
│   ├── 01- Overview.md
│   ├── 02- Architecture.md
│   ├── 03- Security.md
│   ├── 04- Monitoring.md
│   ├── 05- Best Practices.md
│   └── 06- DocumentDB vs MongoDB.md
│
├── 07- Amazon Neptune/
│   ├── 01- Overview.md
│   ├── 02- Graph Databases.md
│   ├── 03- RDF vs Property Graph.md
│   ├── 04- Use Cases.md
│   └── 05- Best Practices.md
│
├── 08- Amazon Timestream/
│   ├── 01- Overview.md
│   ├── 02- Architecture.md
│   ├── 03- Use Cases.md
│   └── 04- Best Practices.md
│
├── 09- Amazon QLDB/
│   ├── 01- Overview.md
│   ├── 02- Ledger Databases.md
│   ├── 03- Architecture.md
│   └── 04- Best Practices.md
│
├── 10- Amazon Redshift/
│   ├── 01- Overview.md
│   ├── 02- Architecture.md
│   ├── 03- Columnar Storage.md
│   ├── 04- Workloads.md
│   ├── 05- Spectrum.md
│   ├── 06- Security.md
│   └── 07- Best Practices.md
│
├── 11- Database Architecture Patterns/
│   ├── 01- Read Scaling.md
│   ├── 02- Write Scaling.md
│   ├── 03- CQRS.md
│   ├── 04- Event Sourcing.md
│   ├── 05- Database per Service.md
│   ├── 06- Shared Database.md
│   ├── 07- Connection Pooling.md
│   ├── 08- Database Failover.md
│   ├── 09- Blue Green Deployment.md
│   ├── 10- Zero Downtime Migration.md
│   └── 11- Multi-Region Architecture.md
│
├── 12- Comparison Guides/
│   ├── RDS vs Aurora.md
│   ├── Aurora vs PostgreSQL.md
│   ├── Redis vs Memcached.md
│   ├── ElastiCache vs MemoryDB.md
│   ├── SQL vs NoSQL.md
│   ├── Multi-AZ vs Read Replica.md
│   ├── RDS vs DynamoDB.md
│   ├── Snapshot vs Backup.md
│   ├── Vertical vs Horizontal Scaling.md
│   └── Database Decision Matrix.md
│
├── 13- Interview Questions/
│   ├── RDS.md
│   ├── Aurora.md
│   ├── DynamoDB.md
│   ├── ElastiCache.md
│   ├── System Design.md
│   └── Senior Backend Questions.md
│
└── 99- Quick Revision/
    ├── Database Cheat Sheet.md
    ├── AWS Database Cheat Sheet.md
    ├── Comparison Tables.md
    ├── Architecture Diagrams.md
    └── Last Minute Revision.md