# Redis in AWS

## Overview

Amazon Web Services (AWS) provides **Amazon ElastiCache for Redis**, a fully managed Redis service that eliminates much of the operational overhead associated with running Redis yourself.

Instead of managing:

- EC2 instances
- Operating system patches
- Redis upgrades
- Monitoring setup
- Failover configuration
- Hardware failures

AWS manages the infrastructure while engineers focus on building applications.

Redis on AWS is commonly used for:

- API caching
- Session management
- Leaderboards
- Rate limiting
- Pub/Sub
- Real-time analytics
- Machine learning feature stores
- Celery brokers
- Distributed locks

This chapter explores how to deploy and operate Redis on AWS using production best practices.

---

# Self-Managed vs Amazon ElastiCache

| Self-Managed Redis | Amazon ElastiCache |
|--------------------|--------------------|
| Install Redis manually | Fully managed |
| OS patching required | AWS handles updates |
| Configure failover | Built-in failover |
| Manual monitoring | CloudWatch integration |
| Manual backups | Automatic snapshots |
| Manual scaling | Online scaling support |
| High operational effort | Low operational effort |

---

# AWS Architecture

```
                Internet

                    │

             Application Load Balancer

                    │

         ┌──────────┴──────────┐

         ▼                     ▼

    Django API           FastAPI API

         │                     │

         └──────────┬──────────┘

                    ▼

              Amazon ElastiCache

                    │

          Primary + Replica Nodes

                    │

              Amazon CloudWatch
```

---

# Amazon ElastiCache

ElastiCache is AWS's managed in-memory caching service.

Supported engines:

- Redis
- Valkey
- Memcached

Redis provides:

- Persistence
- Replication
- Pub/Sub
- Transactions
- Lua scripting
- Redis Cluster

---

# Deployment Options

You can deploy Redis as:

```
Single Node
```

```
Primary + Replica
```

```
Cluster Mode Disabled
```

```
Cluster Mode Enabled
```

Each deployment serves different workloads.

---

# Single Node Deployment

```
Application

↓

Redis Node
```

Advantages

- Simple
- Low cost

Disadvantages

- No failover
- No redundancy
- No scaling

Suitable only for development or non-critical workloads.

---

# Primary-Replica Deployment

```
              Application

                    │

                    ▼

              Primary Node

             /             \

            ▼               ▼

      Replica 1       Replica 2
```

Benefits

- Automatic failover
- Read scaling
- High availability

---

# Cluster Mode Disabled

One primary.

Multiple replicas.

```
Primary

↓

Replicas
```

Advantages

- Simple
- Good HA

Limitations

- Dataset limited to one node

---

# Cluster Mode Enabled

Redis Cluster partitions data.

```
Slot Range

↓

Node 1

↓

Node 2

↓

Node 3
```

Benefits

- Horizontal scaling
- Higher throughput
- Larger datasets

---

# Multi-AZ Deployment

AWS recommends Multi-AZ for production.

```
Availability Zone A

↓

Primary
```

```
Availability Zone B

↓

Replica
```

Failure of one Availability Zone triggers automatic failover.

---

# Automatic Failover

Workflow

```
Primary Failure

↓

Replica Promotion

↓

DNS Updated

↓

Application Reconnects
```

Recovery typically completes within minutes.

---

# Virtual Private Cloud (VPC)

Redis should reside inside a private VPC.

```
Internet

↓

Application

↓

Private Subnet

↓

ElastiCache
```

Never expose Redis publicly.

---

# Private Subnets

Recommended architecture

```
Public Subnet

↓

Load Balancer
```

```
Private Subnet

↓

Application
```

```
Private Subnet

↓

Redis
```

Redis remains inaccessible from the Internet.

---

# Security Groups

Security Groups restrict access.

Example

```
Application SG

↓

Allowed

↓

Redis SG
```

All other traffic is denied.

---

# Encryption in Transit

Enable TLS.

```
Application

↓

Encrypted Connection

↓

Redis
```

Protects sensitive information over the network.

---

# Encryption at Rest

AWS encrypts:

- Snapshots
- Persistent storage
- Backup data

Recommended for production environments.

---

# Authentication

Modern ElastiCache supports

- Redis AUTH
- Redis ACLs

Applications authenticate before issuing commands.

---

# IAM Authentication

AWS services integrate with IAM for operational management.

IAM does **not** replace Redis client authentication but complements infrastructure security and access control.

---

# Parameter Groups

Parameter Groups manage Redis configuration.

Examples

- maxmemory-policy
- timeout
- appendonly
- slowlog-log-slower-than

Configuration changes can be applied consistently across clusters.

---

# Subnet Groups

Subnet Groups define where ElastiCache nodes are deployed.

```
Subnet Group

↓

AZ-A

↓

AZ-B

↓

AZ-C
```

Multiple Availability Zones improve resilience.

---

# Scaling Redis

Vertical scaling

```
cache.r6g.large

↓

cache.r6g.xlarge
```

Horizontal scaling

```
Cluster

↓

Add Shards
```

Scaling depends on deployment mode.

---

# Read Scaling

Applications can distribute read traffic.

```
Writes

↓

Primary
```

```
Reads

↓

Replicas
```

Improves throughput.

---

# Backup Strategy

ElastiCache supports automatic snapshots.

Workflow

```
Redis

↓

Snapshot

↓

Encrypted Backup

↓

S3 Managed Storage
```

Configure an appropriate backup window.

---

# Snapshot Restore

```
Snapshot

↓

New Cluster

↓

Applications Connect
```

Useful for disaster recovery and testing.

---

# Monitoring with CloudWatch

CloudWatch provides metrics such as:

- CPUUtilization
- EngineCPUUtilization
- FreeableMemory
- CurrConnections
- NetworkBytesIn
- NetworkBytesOut
- CacheHits
- CacheMisses
- Evictions
- ReplicationLag

---

# Monitoring Workflow

```
ElastiCache

↓

CloudWatch

↓

Alarm

↓

SNS

↓

Operations Team
```

Automated alerts reduce response times.

---

# CloudWatch Alarms

Common alerts

```
CPU > 80%
```

```
Memory < 20%
```

```
Replication Lag > 5 sec
```

```
Evictions Increasing
```

```
Node Failure
```

---

# Logging

Integrate Redis events with:

- CloudWatch Logs
- AWS Lambda
- EventBridge

Centralized logging improves troubleshooting.

---

# High Availability

Production architecture

```
               ElastiCache

                     │

        Primary + Replica

                     │

           Multi-AZ Failover

                     │

             CloudWatch Alerts
```

---

# Disaster Recovery

Cross-region strategy

```
Region A

↓

Snapshots

↓

Region B

↓

Restore Cluster
```

Protects against regional outages.

---

# Redis for Django

Example architecture

```
Users

↓

ALB

↓

Django

↓

ElastiCache

↓

RDS PostgreSQL
```

Typical usage

- Sessions
- Cache framework
- Celery broker

---

# Redis for FastAPI

```
Users

↓

ALB

↓

FastAPI

↓

Redis

↓

Aurora PostgreSQL
```

Typical usage

- Response cache
- Rate limiting
- Distributed locking

---

# Celery on AWS

```
Celery Workers

↓

Redis Broker

↓

ElastiCache

↓

Worker Processing
```

Deploy workers on ECS, EKS, or EC2.

---

# Infrastructure as Code

Provision Redis using:

- AWS CloudFormation
- Terraform
- AWS CDK

Benefits

- Version control
- Repeatable deployments
- Automated provisioning

---

# Cost Optimization

Reduce costs by:

- Choosing appropriate node sizes
- Removing unused replicas
- Setting appropriate TTLs
- Monitoring memory utilization
- Scaling only when necessary

Right-sizing instances avoids unnecessary infrastructure expense.

---

# Production Architecture

```
                     Internet

                         │

                Application Load Balancer

                         │

          ┌──────────────┴──────────────┐

          ▼                             ▼

      Django API                   FastAPI API

          │                             │

          └──────────────┬──────────────┘

                         ▼

             Amazon ElastiCache Redis

          ┌──────────────┴──────────────┐

          ▼                             ▼

      Primary Node                 Replica Node

                         │

                         ▼

                 Amazon CloudWatch

                         │

                         ▼

                   Amazon SNS Alerts

                         │

                         ▼

                     Operations Team
```

---

# Common Mistakes

## Public Redis

Redis should never receive Internet traffic.

Always deploy inside private subnets.

---

## No Multi-AZ

Single Availability Zone failures can cause outages.

Enable Multi-AZ.

---

## No Backups

Always enable automatic snapshots.

---

## Ignoring CloudWatch

Infrastructure problems go unnoticed.

Create alarms.

---

## Wrong Node Size

Undersized nodes

↓

High latency

↓

Evictions

↓

Poor user experience.

---

## No Encryption

Enable encryption both

- In transit
- At rest

---

# Best Practices

- Deploy Redis using Amazon ElastiCache for production workloads.
- Use Multi-AZ deployments with automatic failover.
- Keep Redis in private subnets protected by Security Groups.
- Enable TLS and encryption at rest.
- Configure automatic snapshots and test restore procedures.
- Monitor Redis using CloudWatch and create proactive alarms.
- Use Infrastructure as Code for repeatable deployments.
- Scale based on measured utilization rather than assumptions.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| Node Type | Right-size based on workload |
| Multi-AZ | Improve availability |
| Replicas | Scale read traffic |
| Cluster Mode | Scale large datasets |
| CloudWatch | Continuous monitoring |
| Snapshots | Protect against data loss |
| Security Groups | Restrict network access |
| Parameter Groups | Standardize configuration |

---

# Production Considerations

For production deployments:

- Deploy ElastiCache inside private VPC subnets across multiple Availability Zones.
- Enable automatic failover and configure at least one replica for critical workloads.
- Regularly review CloudWatch metrics to anticipate capacity issues.
- Automate Redis provisioning using CloudFormation, Terraform, or AWS CDK.
- Periodically test snapshot restoration and disaster recovery procedures.
- Integrate Redis monitoring with organizational incident management systems.
- Apply the principle of least privilege to Security Groups, IAM roles, and Redis ACLs.

---

# Summary

Amazon ElastiCache provides a fully managed, highly available Redis platform that simplifies operations while delivering enterprise-grade scalability and reliability. By combining Multi-AZ deployments, automatic failover, encryption, CloudWatch monitoring, automated backups, and Infrastructure as Code, organizations can build resilient Redis deployments that support demanding production workloads with minimal operational overhead.

---

# Key Takeaways

- Amazon ElastiCache is the recommended way to run Redis on AWS production workloads.
- Deploy Redis in private VPC subnets with Security Groups controlling access.
- Enable Multi-AZ deployments and automatic failover for high availability.
- Use Cluster Mode for large datasets and horizontal scalability.
- Protect data with encryption, automatic snapshots, and disaster recovery plans.
- Monitor Redis continuously using CloudWatch metrics and alarms.
- Automate infrastructure provisioning with CloudFormation, Terraform, or AWS CDK.
- Regularly test failover and backup restoration to ensure operational readiness.