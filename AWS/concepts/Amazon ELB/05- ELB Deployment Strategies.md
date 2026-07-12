# 05- Elastic Beanstalk Deployment Strategies

---

# Introduction

Deploying a new application version in production is one of the riskiest activities in software engineering.

A deployment can:

```text id="w1r3aj"
Fix Bugs
Introduce Bugs
Improve Performance
Cause Downtime
Break Production
```

Elastic Beanstalk provides multiple deployment strategies to balance:

* Deployment Speed
* Availability
* Cost
* Risk

Choosing the wrong deployment strategy can result in:

* Downtime
* Failed Releases
* Customer Impact
* Revenue Loss

Understanding deployment strategies is therefore essential for production operations.

---

# Deployment Lifecycle

Every deployment follows a similar process.

```text id="z6l4up"
Application Version
        ↓
Environment Update
        ↓
Instance Deployment
        ↓
Health Checks
        ↓
Traffic Routing
        ↓
Production Traffic
```

The difference between deployment strategies is:

```text id="2w6e4w"
How Traffic Is Shifted
How Instances Are Updated
How Risk Is Managed
```

---

# Deployment Strategy Overview

Elastic Beanstalk supports:

```text id="hh8wzi"
All At Once
Rolling
Rolling With Additional Batch
Immutable
Blue/Green
Traffic Splitting
```

Each strategy has different trade-offs.

---

# Strategy Comparison

| Strategy                      | Downtime | Cost   | Risk     | Speed  |
| ----------------------------- | -------- | ------ | -------- | ------ |
| All At Once                   | High     | Low    | High     | Fast   |
| Rolling                       | Low      | Low    | Medium   | Medium |
| Rolling With Additional Batch | Very Low | Medium | Low      | Medium |
| Immutable                     | None     | High   | Very Low | Slower |
| Blue/Green                    | None     | High   | Very Low | Fast   |
| Traffic Splitting             | None     | High   | Lowest   | Slower |

---

# All At Once Deployment

---

## How It Works

All instances are updated simultaneously.

```text id="cwz40j"
Instance A
Instance B
Instance C
        ↓
Deploy New Version
```

All instances stop serving traffic while deployment occurs.

---

## Architecture

Before:

```text id="yrj3vr"
ALB
 ↓
A(v1)
B(v1)
C(v1)
```

After:

```text id="1h0t1r"
ALB
 ↓
A(v2)
B(v2)
C(v2)
```

---

## Advantages

```text id="ld9ovx"
Fastest Deployment
Simplest Process
Lowest Cost
```

---

## Disadvantages

```text id="vgqhjw"
Downtime
No Rollback Protection
High Risk
```

---

## Use Cases

Suitable for:

```text id="8hxvyh"
Development
Testing
Personal Projects
```

Not recommended for production.

---

# Rolling Deployment

---

## How It Works

Instances are updated in batches.

Example:

```text id="q2ecb9"
Batch 1
 ↓
Batch 2
 ↓
Batch 3
```

Some instances continue serving traffic while others update.

---

## Architecture

Initial:

```text id="z2bnur"
A(v1)
B(v1)
C(v1)
D(v1)
```

Batch 1:

```text id="q48h2z"
A(v2)
B(v2)
C(v1)
D(v1)
```

Batch 2:

```text id="nhnh5v"
A(v2)
B(v2)
C(v2)
D(v2)
```

---

## Advantages

```text id="vwxwl9"
Reduced Downtime
Lower Risk
No Additional Instances
```

---

## Disadvantages

```text id="0i2c6u"
Reduced Capacity During Deployment
Longer Deployment Time
```

---

## Production Consideration

Traffic load must be low enough that fewer instances can handle requests.

---

# Rolling With Additional Batch

---

## How It Works

Elastic Beanstalk launches an extra batch before deployment begins.

---

## Architecture

Current:

```text id="u2jv7n"
A(v1)
B(v1)
C(v1)
D(v1)
```

Temporary Batch:

```text id="epkdf6"
A(v1)
B(v1)
C(v1)
D(v1)
E(v1)
```

Deployment:

```text id="99yk9v"
A(v2)
B(v2)
C(v2)
D(v2)
```

Extra instance removed.

---

## Advantages

```text id="k0i4m5"
Maintains Capacity
Reduced Risk
Better User Experience
```

---

## Disadvantages

```text id="9vf0jh"
Higher Temporary Cost
```

---

## Production Recommendation

Widely used for medium-sized production environments.

---

# Immutable Deployment

---

## How It Works

Instead of updating existing instances:

```text id="cuv6g8"
Create New Instances
Deploy New Version
Validate
Replace Old Instances
```

---

## Architecture

Before:

```text id="36o0n5"
A(v1)
B(v1)
C(v1)
```

New Group:

```text id="axl1p2"
D(v2)
E(v2)
F(v2)
```

Traffic moves only after validation.

---

## Advantages

```text id="pkqvbn"
No Downtime
Safe Rollback
High Reliability
```

---

## Disadvantages

```text id="ny6jch"
Higher Cost
Longer Deployment Time
```

---

## Why Enterprises Love Immutable Deployments

Production traffic never reaches unhealthy instances.

---

## Failure Example

If deployment fails:

```text id="8kk50r"
Old Environment Remains Active
```

Users are unaffected.

---

# Blue/Green Deployment

---

# Concept

Two complete environments exist.

```text id="pg11ut"
Blue = Current Production
Green = New Version
```

---

## Architecture

Current:

```text id="zlv6bo"
Blue(v1)
```

New:

```text id="lz34s7"
Green(v2)
```

---

## Traffic Shift

```text id="2lqzhw"
Blue
 ↓
DNS Swap
 ↓
Green
```

---

## Advantages

```text id="b8v6n6"
Zero Downtime
Instant Rollback
Safe Validation
```

---

## Disadvantages

```text id="d6w9ew"
Double Infrastructure Cost
```

---

## Enterprise Usage

Most common strategy for:

```text id="vpxkwe"
Banking
Healthcare
E-Commerce
```

---

# Traffic Splitting Deployment

---

## How It Works

A percentage of traffic is routed to the new version.

Example:

```text id="mrfx9u"
90% → Old Version
10% → New Version
```

---

## Architecture

```text id="2x8wya"
Users
 ↓
ALB
 ↓
90% v1

10% v2
```

---

## Benefits

```text id="vhv3yq"
Canary Testing
Gradual Rollout
Risk Reduction
```

---

## Example Rollout

```text id="2jlwmj"
10%
 ↓
25%
 ↓
50%
 ↓
100%
```

---

## Advantages

```text id="aqhtcy"
Lowest Risk
Real User Validation
Production Testing
```

---

## Disadvantages

```text id="7izs9g"
Complexity
Higher Cost
Longer Deployment
```

---

# Deployment Strategy Selection

---

## Development Environment

Recommended:

```text id="7mp2i2"
All At Once
```

---

## Small Production Environment

Recommended:

```text id="w9dbmb"
Rolling
```

---

## Medium Production Environment

Recommended:

```text id="8czp3z"
Rolling With Additional Batch
```

---

## Enterprise Environment

Recommended:

```text id="b9wbxr"
Immutable
Blue/Green
Traffic Splitting
```

---

# Rollback Strategies

---

## All At Once

Rollback:

```text id="krz0sh"
Redeploy Previous Version
```

---

## Rolling

Rollback:

```text id="5m1dmu"
Redeploy Previous Version
```

---

## Immutable

Rollback:

```text id="x1qbg4"
Terminate New Instances
```

---

## Blue/Green

Rollback:

```text id="9ofj2r"
Swap DNS Back
```

Fastest rollback strategy.

---

# Cost Analysis

---

## Lowest Cost

```text id="8of6b6"
All At Once
Rolling
```

---

## Medium Cost

```text id="efm93v"
Rolling With Additional Batch
```

---

## Highest Cost

```text id="dphozk"
Immutable
Blue/Green
Traffic Splitting
```

---

# Common Deployment Failures

---

## Health Check Failures

```text id="49qjkn"
Application Starts
But Health Check Fails
```

---

## Dependency Issues

```text id="tpmu6j"
Missing Packages
```

---

## Configuration Errors

```text id="bh4m0r"
Environment Variables Missing
```

---

## Database Migration Problems

```text id="eqknjk"
Schema Changes Break Application
```

---

# Deployment Best Practices

---

## Never Deploy Directly To Production

Use:

```text id="lf3hlx"
Development
 ↓
Testing
 ↓
Staging
 ↓
Production
```

---

## Validate Health Checks

Health checks should verify:

```text id="z3cv1m"
Application Health
Database Connectivity
Dependencies
```

---

## Use Immutable Deployments

For critical workloads.

---

## Use Blue/Green For Major Releases

Especially when:

```text id="2gg4xj"
Database Changes
Infrastructure Changes
Major Features
```

are involved.

---

# Interview Questions

---

## Which Deployment Strategy Causes Downtime?

```text id="n7a9j2"
All At Once
```

---

## Which Deployment Strategy Is Safest?

```text id="c4zy6q"
Traffic Splitting
```

---

## Which Deployment Strategy Is Most Common In Enterprises?

```text id="3g4ivn"
Blue/Green
Immutable
```

---

## Which Strategy Provides Fastest Rollback?

```text id="8m3dkl"
Blue/Green
```

---

## What Is The Difference Between Rolling And Immutable?

Rolling updates existing instances.

Immutable creates entirely new instances.

---

# Senior Engineer Perspective

Most outages are not caused by bad code.

They are caused by:

```text id="9p6m6m"
Bad Deployments
```

A deployment strategy is therefore a risk-management decision.

General recommendation:

```text id="e1h3cc"
Development
    ↓
All At Once

Small Production
    ↓
Rolling

Medium Production
    ↓
Rolling With Additional Batch

Critical Production
    ↓
Immutable

Enterprise Production
    ↓
Blue/Green
```

The safest deployment is the one that allows fast validation and fast rollback.

---

# Key Takeaways

* Elastic Beanstalk supports six deployment strategies.
* All At Once is fastest but riskiest.
* Rolling updates instances in batches.
* Rolling With Additional Batch preserves capacity.
* Immutable creates new instances for deployment.
* Blue/Green uses two separate environments.
* Traffic Splitting gradually shifts traffic.
* Deployment strategy selection is a balance between risk, cost, and availability.
* Enterprise workloads typically prefer Immutable or Blue/Green deployments.
