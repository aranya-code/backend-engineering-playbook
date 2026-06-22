# 17- Elastic Beanstalk Troubleshooting

---

# Introduction

No matter how well an application is designed, production issues will eventually occur.

Common problems include:

```text id="tr001"
Failed Deployments
Application Crashes
Health Check Failures
Database Connectivity Issues
High CPU Usage
Scaling Problems
Load Balancer Errors
```

The difference between a junior engineer and a senior engineer is often not coding ability.

It is:

```text id="tr002"
Troubleshooting Ability
```

Elastic Beanstalk troubleshooting requires understanding how multiple AWS services work together.

---

# Troubleshooting Mindset

Many engineers immediately start changing configurations.

This is a mistake.

Good troubleshooting follows:

```text id="tr003"
Observe
Analyze
Verify
Fix
Validate
```

Not:

```text id="tr004"
Guess
Change
Hope
```

---

# Elastic Beanstalk Architecture Review

Before troubleshooting, remember the architecture.

```text id="tr005"
Route53
   ↓
ALB
   ↓
Auto Scaling Group
   ↓
EC2
   ↓
Application
```

Plus:

```text id="tr006"
CloudWatch
IAM
S3
CloudFormation
```

Any layer can fail.

---

# Troubleshooting Workflow

A senior engineer typically follows:

```text id="tr007"
Problem
   ↓
Identify Layer
   ↓
Collect Evidence
   ↓
Determine Root Cause
   ↓
Fix
   ↓
Validate
```

---

# Golden Rule

Always answer:

```text id="tr008"
What Changed?
```

Most outages are caused by:

```text id="tr009"
Recent Deployments
Configuration Changes
Infrastructure Updates
```

---

# Elastic Beanstalk Events

The first place to investigate.

Console:

```text id="tr010"
Elastic Beanstalk
     ↓
Environment
     ↓
Events
```

---

# Why Events Matter

Events show:

```text id="tr011"
Deployment Activity
Scaling Events
Environment Changes
Failures
```

---

# Example Event

```text id="tr012"
Environment Update Failed
```

This immediately narrows the investigation.

---

# Health Dashboard

Always check environment health.

---

# Health States

```text id="tr013"
Green
Yellow
Red
Grey
```

---

# Green

```text id="tr014"
Healthy
```

---

# Yellow

```text id="tr015"
Warning
```

---

# Red

```text id="tr016"
Critical Failure
```

---

# Grey

```text id="tr017"
Unknown Status
```

---

# Common Deployment Failures

One of the most frequent issues.

---

# Symptoms

```text id="tr018"
Deployment Failed
Version Not Updated
Environment Degraded
```

---

# Investigation Workflow

```text id="tr019"
Events
 ↓
Deployment Logs
 ↓
Application Logs
```

---

# Common Causes

```text id="tr020"
Dependency Errors
Missing Files
Syntax Errors
Failed Hooks
Permission Issues
```

---

# Python Dependency Failure

Example:

```text id="tr021"
ModuleNotFoundError
```

Cause:

```text id="tr022"
requirements.txt Missing Package
```

---

# Solution

```bash id="tr023"
pip freeze > requirements.txt
```

Redeploy.

---

# Application Startup Failure

Application never starts successfully.

---

# Symptoms

```text id="tr024"
502 Bad Gateway
503 Service Unavailable
```

---

# Common Causes

```text id="tr025"
Application Crash
Incorrect Startup Command
Missing Environment Variables
```

---

# Django Example

Bad:

```python id="tr026"
SECRET_KEY = os.environ["SECRET_KEY"]
```

Environment variable missing.

Result:

```text id="tr027"
Application Crash
```

---

# Solution

Verify:

```text id="tr028"
Environment Variables
```

inside Elastic Beanstalk.

---

# Health Check Failures

Extremely common.

---

# Symptoms

```text id="tr029"
Unhealthy Instances
Red Health Status
Traffic Not Routed
```

---

# Investigation

Check:

```text id="tr030"
ALB Health Checks
```

---

# Example

Configured:

```text id="tr031"
/health
```

Application:

```text id="tr032"
/healthz
```

Mismatch causes failure.

---

# Solution

Align:

```text id="tr033"
Application Endpoint
Health Check Path
```

---

# 502 Bad Gateway

One of the most common production errors.

---

# Meaning

Load Balancer cannot communicate with application.

---

# Architecture

```text id="tr034"
ALB
 ↓
Application
```

Communication fails.

---

# Common Causes

```text id="tr035"
Application Not Running
Wrong Port
Gunicorn Failure
Nginx Misconfiguration
```

---

# Investigation

Check:

```text id="tr036"
/var/log/nginx/error.log
```

and

```text id="tr037"
/var/log/web.stdout.log
```

---

# 503 Service Unavailable

Usually indicates:

```text id="tr038"
No Healthy Targets
```

---

# Investigation

Check:

```text id="tr039"
Target Group
```

---

# Example

```text id="tr040"
Healthy Hosts = 0
```

---

# Database Connectivity Issues

Common for Django and FastAPI applications.

---

# Symptoms

```text id="tr041"
Connection Refused
Timeout
Database Error
```

---

# Investigation Checklist

```text id="tr042"
Database Running?
Security Groups Correct?
Credentials Correct?
Network Access Allowed?
```

---

# PostgreSQL Example

Port:

```text id="tr043"
5432
```

Must be allowed.

---

# MySQL Example

Port:

```text id="tr044"
3306
```

Must be allowed.

---

# Security Group Issues

Very common.

---

# Symptoms

```text id="tr045"
Application Cannot Reach Database
ALB Cannot Reach EC2
```

---

# Investigation

Verify:

```text id="tr046"
Inbound Rules
Outbound Rules
```

---

# Bad Example

```text id="tr047"
ALB
 ↓
EC2

Blocked
```

Traffic never arrives.

---

# Environment Variable Issues

---

# Symptoms

```text id="tr048"
Application Startup Failure
Unexpected Behavior
```

---

# Investigation

Review:

```text id="tr049"
Elastic Beanstalk
 ↓
Configuration
 ↓
Environment Variables
```

---

# Common Missing Variables

```text id="tr050"
DATABASE_URL
SECRET_KEY
REDIS_URL
```

---

# Auto Scaling Problems

---

# Symptoms

```text id="tr051"
Instances Not Scaling
Traffic Issues
Performance Problems
```

---

# Investigation

Check:

```text id="tr052"
CloudWatch Metrics
Scaling Policies
```

---

# Example

Maximum Capacity:

```text id="tr053"
2
```

Traffic requires:

```text id="tr054"
10
```

Scaling impossible.

---

# High CPU Utilization

---

# Symptoms

```text id="tr055"
Slow Responses
High Latency
```

---

# Investigation

Review:

```text id="tr056"
CloudWatch Metrics
```

---

# Common Causes

```text id="tr057"
Traffic Spike
Infinite Loop
Poor Database Query
```

---

# Solution

```text id="tr058"
Optimize Code
Scale Out
Increase Instance Size
```

---

# Memory Problems

Often overlooked.

---

# Symptoms

```text id="tr059"
Application Restarting
Unexpected Crashes
```

---

# Investigation

Check:

```text id="tr060"
Memory Usage
Swap Usage
```

---

# Log Analysis

Logs are critical.

---

# Important Logs

Application:

```text id="tr061"
/var/log/web.stdout.log
```

---

Nginx:

```text id="tr062"
/var/log/nginx/error.log
```

---

Deployment:

```text id="tr063"
/var/log/eb-engine.log
```

---

Platform Hooks:

```text id="tr064"
/var/log/eb-hooks.log
```

---

CloudFormation:

```text id="tr065"
/var/log/cfn-init.log
```

---

# Deployment Log Workflow

```text id="tr066"
Deployment Failed
      ↓
eb-engine.log
      ↓
Root Cause
```

---

# Platform Hook Failures

---

# Symptoms

```text id="tr067"
Deployment Stops
```

---

# Investigation

Review:

```text id="tr068"
eb-hooks.log
```

---

# Common Causes

```text id="tr069"
Missing Permissions
Syntax Errors
Bad Exit Codes
```

---

# CloudFormation Failures

Elastic Beanstalk uses CloudFormation internally.

---

# Symptoms

```text id="tr070"
Environment Creation Failed
```

---

# Investigation

```text id="tr071"
CloudFormation Events
```

---

# Common Causes

```text id="tr072"
IAM Issues
Resource Limits
Invalid Configuration
```

---

# DNS Problems

---

# Symptoms

```text id="tr073"
Application Unreachable
```

---

# Investigation

Verify:

```text id="tr074"
DNS Records
Route53
ALB DNS
```

---

# SSL Problems

---

# Symptoms

```text id="tr075"
HTTPS Failure
Certificate Error
```

---

# Investigation

Check:

```text id="tr076"
ACM Certificate
Listener Configuration
DNS Validation
```

---

# Performance Troubleshooting

---

# Key Metrics

```text id="tr077"
CPU
Memory
Latency
Request Count
Network Usage
```

---

# Workflow

```text id="tr078"
Performance Issue
      ↓
Metrics
      ↓
Logs
      ↓
Root Cause
```

---

# Monitoring Tools

Primary tools:

```text id="tr079"
CloudWatch
Elastic Beanstalk Health
CloudTrail
ALB Metrics
```

---

# Root Cause Analysis (RCA)

After every incident:

```text id="tr080"
What Happened?
Why?
How To Prevent Recurrence?
```

---

# Example RCA

Problem:

```text id="tr081"
Deployment Failed
```

Root Cause:

```text id="tr082"
Missing Environment Variable
```

Prevention:

```text id="tr083"
Deployment Validation Script
```

---

# Troubleshooting Checklist

---

## Step 1

Check:

```text id="tr084"
Elastic Beanstalk Events
```

---

## Step 2

Check:

```text id="tr085"
Health Dashboard
```

---

## Step 3

Check:

```text id="tr086"
CloudWatch Metrics
```

---

## Step 4

Check:

```text id="tr087"
Application Logs
```

---

## Step 5

Check:

```text id="tr088"
Load Balancer Health
```

---

## Step 6

Check:

```text id="tr089"
Database Connectivity
```

---

## Step 7

Review:

```text id="tr090"
Recent Changes
```

---

# Common Elastic Beanstalk Interview Scenarios

---

## Deployment Succeeds But Site Shows 502

Investigate:

```text id="tr091"
Application Startup
Gunicorn
Nginx
Ports
```

---

## Site Returns 503

Investigate:

```text id="tr092"
Health Checks
Target Groups
```

---

## Environment Turns Red

Investigate:

```text id="tr093"
Application Logs
Health Dashboard
```

---

## Auto Scaling Not Working

Investigate:

```text id="tr094"
Policies
CloudWatch Alarms
Capacity Limits
```

---

# Senior Engineer Troubleshooting Approach

A senior engineer generally follows:

```text id="tr095"
1. Reproduce Problem
2. Collect Evidence
3. Identify Layer
4. Determine Root Cause
5. Implement Fix
6. Validate
7. Document
```

Never:

```text id="tr096"
Randomly Change Settings
```

---

# Interview Questions

## Where Do You Start Troubleshooting?

```text id="tr097"
Elastic Beanstalk Events
```

---

## What Causes 502 Errors?

Typically:

```text id="tr098"
Application Failure
Nginx Issues
Port Misconfiguration
```

---

## What Causes 503 Errors?

Typically:

```text id="tr099"
No Healthy Targets
```

---

## Which Log Is Most Useful For Deployment Failures?

```text id="tr100"
/var/log/eb-engine.log
```

---

## Where Are Platform Hook Errors Logged?

```text id="tr101"
/var/log/eb-hooks.log
```

---

## Why Is CloudWatch Important?

Provides:

```text id="tr102"
Metrics
Alarms
Visibility
```

---

# Senior Engineer Perspective

Troubleshooting is fundamentally:

```text id="tr103"
Evidence Collection
```

The goal is not to find a fix quickly.

The goal is to:

```text id="tr104"
Find The Correct Fix
```

A mature engineer uses:

```text id="tr105"
Metrics
Logs
Events
Monitoring
```

to identify root causes instead of relying on assumptions.

Most production incidents can be resolved faster when troubleshooting follows a structured methodology.

---

# Key Takeaways

* Start with Elastic Beanstalk Events and Health Dashboard.
* Use logs to determine root causes.
* CloudWatch provides critical metrics and alerts.
* 502 errors usually indicate application communication issues.
* 503 errors usually indicate no healthy targets.
* Security groups and environment variables are common causes of failures.
* Platform Hook and CloudFormation logs are essential for deployment troubleshooting.
* Always perform Root Cause Analysis after incidents.
* Effective troubleshooting relies on evidence, not guesses.
