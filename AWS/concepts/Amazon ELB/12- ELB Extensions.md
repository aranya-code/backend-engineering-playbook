# 12- Elastic Beanstalk Extensions (.ebextensions)

---

# Introduction

As applications grow, developers often need more control than what is available through the Elastic Beanstalk console.

Examples:

```text id="a1e2b3"
Install Additional Packages
Create Files
Modify Configuration
Run Commands
Configure Services
Customize Infrastructure
```

Elastic Beanstalk Extensions provide a mechanism for customizing environments during deployment.

Without Extensions:

```text id="c4d5e6"
Deploy Application
      ↓
Use Default Environment
```

With Extensions:

```text id="f7g8h9"
Deploy Application
      ↓
Customize Environment
      ↓
Deploy Application
```

---

# What Are .ebextensions?

`.ebextensions` is a special directory inside your application source bundle.

It contains YAML or JSON configuration files.

Example:

```text id="j1k2l3"
.ebextensions/
    nginx.config
    packages.config
    environment.config
```

---

# Why .ebextensions Exist

Elastic Beanstalk environments are created automatically.

However, many applications require customizations.

Examples:

```text id="m4n5o6"
Install ImageMagick
Install wkhtmltopdf
Create Directories
Modify Nginx
Configure Cron Jobs
```

`.ebextensions` allows these changes to be automated.

---

# Directory Structure

Typical project structure:

```text id="p7q8r9"
my-app/
│
├── application.py
├── requirements.txt
│
└── .ebextensions/
    ├── packages.config
    ├── files.config
    └── commands.config
```

---

# How Extensions Work

Deployment workflow:

```text id="s1t2u3"
Upload Application
      ↓
Elastic Beanstalk
      ↓
Read .ebextensions
      ↓
Apply Configuration
      ↓
Deploy Application
```

---

# Supported File Format

Elastic Beanstalk supports:

```text id="v4w5x6"
YAML
JSON
```

Most engineers prefer:

```text id="y7z8a9"
YAML
```

because it is easier to read.

---

# Example File

```yaml id="b1c2d3"
packages:
  yum:
    git: []
```

This installs:

```text id="e4f5g6"
Git
```

during deployment.

---

# Configuration Sections

Common sections include:

```text id="h7i8j9"
packages
groups
users
sources
files
commands
container_commands
services
option_settings
resources
```

Understanding these sections is critical.

---

# Packages

The packages section installs software packages.

---

# Example

```yaml id="k1l2m3"
packages:
  yum:
    git: []
    wget: []
```

Result:

```text id="n4o5p6"
Git Installed
Wget Installed
```

---

# Supported Package Managers

Amazon Linux commonly supports:

```text id="q7r8s9"
yum
rpm
```

---

# Real World Example

Install image processing tools:

```yaml id="t1u2v3"
packages:
  yum:
    ImageMagick: []
```

Useful for:

```text id="w4x5y6"
Image Upload Applications
```

---

# Files

The files section creates files during deployment.

---

# Example

```yaml id="z7a8b9"
files:
  "/tmp/sample.txt":
    content: "Hello World"
```

Result:

```text id="c1d2e3"
/tmp/sample.txt
```

created automatically.

---

# Use Cases

```text id="f4g5h6"
Configuration Files
Application Settings
System Files
Certificates
```

---

# File Permissions

Example:

```yaml id="i7j8k9"
files:
  "/tmp/config.txt":
    mode: "000644"
```

---

# Commands

Commands execute before application deployment.

---

# Workflow

```text id="l1m2n3"
Provision Server
      ↓
Run Commands
      ↓
Deploy Application
```

---

# Example

```yaml id="o4p5q6"
commands:
  01_update:
    command: yum update -y
```

---

# Common Uses

```text id="r7s8t9"
Install Dependencies
Create Directories
System Configuration
```

---

# Command Execution Order

Commands execute in alphabetical order.

Example:

```text id="u1v2w3"
01-install
02-configure
03-setup
```

---

# Container Commands

Container commands execute after application extraction but before deployment.

---

# Workflow

```text id="x4y5z6"
Extract Application
      ↓
Container Commands
      ↓
Deploy Application
```

---

# Example

```yaml id="a7b8c9"
container_commands:
  01_migrate:
    command: python manage.py migrate
```

---

# Django Example

```yaml id="d1e2f3"
container_commands:
  01_migrate:
    command: python manage.py migrate

  02_collectstatic:
    command: python manage.py collectstatic --noinput
```

---

# Why Container Commands Matter

Common tasks:

```text id="g4h5i6"
Database Migrations
Static File Collection
Application Setup
```

---

# Option Settings

One of the most important sections.

Allows configuration of Elastic Beanstalk resources.

---

# Example

```yaml id="j7k8l9"
option_settings:
  aws:autoscaling:asg:
    MinSize: 2
    MaxSize: 6
```

---

# What Can Be Configured?

```text id="m1n2o3"
Auto Scaling
Environment Variables
Load Balancer
Monitoring
Deployment Policies
```

---

# Environment Variables

Example:

```yaml id="p4q5r6"
option_settings:
  aws:elasticbeanstalk:application:environment:
    DEBUG: "False"
```

---

# Result

Application receives:

```text id="s7t8u9"
DEBUG=False
```

---

# Services

Used to manage operating system services.

---

# Example

```yaml id="v1w2x3"
services:
  sysvinit:
    nginx:
      enabled: true
      ensureRunning: true
```

---

# Result

```text id="y4z5a6"
Nginx Enabled
Nginx Running
```

---

# Resources

Resources allow direct CloudFormation customization.

---

# Why Resources Matter

Elastic Beanstalk uses CloudFormation internally.

Resources allow additional AWS services to be created.

---

# Example

```yaml id="b7c8d9"
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
```

---

# Result

```text id="e1f2g3"
Additional S3 Bucket Created
```

during deployment.

---

# Sources

Downloads archives during deployment.

---

# Example

```yaml id="h4i5j6"
sources:
  /opt/custom:
    https://example.com/archive.zip
```

---

# Use Cases

```text id="k7l8m9"
Custom Software
Third Party Tools
Dependencies
```

---

# Users and Groups

Creates Linux users and groups.

---

# Example

```yaml id="n1o2p3"
groups:
  appgroup: {}

users:
  appuser:
    groups:
      - appgroup
```

---

# Common Use Cases

```text id="q4r5s6"
Security
Permission Management
Application Isolation
```

---

# Execution Order

Understanding execution order is critical.

Workflow:

```text id="t7u8v9"
packages
 ↓
groups
 ↓
users
 ↓
sources
 ↓
files
 ↓
commands
 ↓
services
 ↓
container_commands
 ↓
deployment
```

---

# Multiple Configuration Files

Example:

```text id="w1x2y3"
.ebextensions/
│
├── 01-packages.config
├── 02-files.config
├── 03-commands.config
```

---

# Why Split Files?

Benefits:

```text id="z4a5b6"
Organization
Maintainability
Readability
```

---

# Real World Django Example

```text id="c7d8e9"
Install Dependencies
      ↓
Create Environment Variables
      ↓
Run Migrations
      ↓
Collect Static Files
      ↓
Deploy
```

---

# Example Configuration

```yaml id="f1g2h3"
container_commands:
  01_migrate:
    command: python manage.py migrate

  02_collectstatic:
    command: python manage.py collectstatic --noinput
```

---

# Common Mistakes

---

## Incorrect YAML Indentation

Bad:

```yaml id="i4j5k6"
packages:
yum:
git: []
```

Result:

```text id="l7m8n9"
Deployment Failure
```

---

## Running Long Commands

Example:

```text id="o1p2q3"
Large Downloads
Long Scripts
```

Can cause deployment timeouts.

---

## Hardcoded Secrets

Bad:

```yaml id="r4s5t6"
SECRET_KEY: mysecret
```

Use:

```text id="u7v8w9"
Secrets Manager
```

instead.

---

## Large Infrastructure Changes

Avoid using `.ebextensions` to manage entire AWS architectures.

Use:

```text id="x1y2z3"
CloudFormation
Terraform
CDK
```

for large-scale infrastructure.

---

# Troubleshooting Extensions

Step 1:

```text id="a4b5c6"
Review Elastic Beanstalk Events
```

---

Step 2:

```text id="d7e8f9"
Check Deployment Logs
```

---

Step 3:

```text id="g1h2i3"
/var/log/eb-engine.log
```

---

Step 4:

```text id="j4k5l6"
/var/log/cfn-init.log
```

---

# Best Practices

---

## Keep Files Small

Example:

```text id="m7n8o9"
One Responsibility Per File
```

---

## Use Naming Conventions

```text id="p1q2r3"
01-packages.config
02-files.config
03-services.config
```

---

## Store Secrets Securely

Use:

```text id="s4t5u6"
Secrets Manager
Parameter Store
```

---

## Test In Non-Production

Always validate changes in:

```text id="v7w8x9"
Development
Staging
```

before production.

---

# Interview Questions

## What Is .ebextensions?

A directory containing Elastic Beanstalk configuration files.

---

## Which File Formats Are Supported?

```text id="y1z2a3"
YAML
JSON
```

---

## Difference Between Commands and Container Commands?

Commands run before application deployment.

Container Commands run after application extraction but before deployment.

---

## How Are Environment Variables Configured?

Using:

```text id="b4c5d6"
option_settings
```

---

## Can .ebextensions Create AWS Resources?

Yes.

Using:

```text id="e7f8g9"
Resources
```

section.

---

## Where Are Extension Errors Logged?

```text id="h1i2j3"
eb-engine.log
cfn-init.log
```

---

# Senior Engineer Perspective

`.ebextensions` is one of the most powerful features in Elastic Beanstalk.

It allows teams to:

```text id="k4l5m6"
Automate Configuration
Standardize Environments
Reduce Manual Work
Improve Consistency
```

However, it should be used carefully.

A good rule:

```text id="n7o8p9"
Application Configuration
    ↓
.ebextensions

Infrastructure Provisioning
    ↓
Terraform/CDK/CloudFormation
```

This separation keeps deployments maintainable and predictable.

---

# Key Takeaways

* `.ebextensions` customize Elastic Beanstalk environments.
* Configuration files are written in YAML or JSON.
* Packages install software dependencies.
* Commands and Container Commands automate deployment tasks.
* Option Settings configure Elastic Beanstalk resources.
* Resources can create additional AWS services.
* Proper file organization improves maintainability.
* Deployment logs are critical for troubleshooting.
* `.ebextensions` are powerful but should not replace Infrastructure as Code tools.
