# Amazon Elastic Beanstalk

## Overview

Amazon Elastic Beanstalk is an AWS managed service for deploying and operating applications without managing the underlying infrastructure directly.

This section covers Elastic Beanstalk from its core concepts through environment configuration, scaling, load balancing, storage, customization, and environment management.

---

## Folder Structure

```text
02- Amazon Elastic Beanstalk/

├── 01- Introduction.md
├── 02- Core Components.md
├── 03- Platforms.md
├── 04- Configuration.md
├── 05- Auto Scaling.md
├── 06- Load Balancing.md
├── 07- Storage.md
├── 08- Extensions.md
├── 09- Platform Hooks.md
├── 10- Cloning.md
├── 11- Migration.md
└── README.md
```

---

## Quick Navigation

| # | Topic | Coverage |
|---|---|---|
| 01 | [Introduction](01-%20Introduction.md) | Elastic Beanstalk fundamentals, purpose, applications, environments, and core workflow. |
| 02 | [Core Components](02-%20Core%20Components.md) | Applications, environments, application versions, resources, and environment tiers. |
| 03 | [Platforms](03-%20Platforms.md) | Supported platforms, platform versions, runtimes, and platform selection. |
| 04 | [Configuration](04-%20Configuration.md) | Environment configuration, options, configuration files, variables, and settings. |
| 05 | [Auto Scaling](05-%20Auto%20Scaling.md) | Auto Scaling Groups, capacity, scaling policies, triggers, and instance management. |
| 06 | [Load Balancing](06-%20Load%20Balancing.md) | Elastic Load Balancing, traffic distribution, health checks, and availability. |
| 07 | [Storage](07-%20Storage.md) | Application storage, persistent storage considerations, and AWS storage integration. |
| 08 | [Extensions](08-%20Extensions.md) | Elastic Beanstalk configuration extensions and environment customization. |
| 09 | [Platform Hooks](09-%20Platform%20Hooks.md) | Deployment lifecycle hooks and custom automation during environment operations. |
| 10 | [Cloning](10-%20Cloning.md) | Cloning environments for testing, staging, migration, and operational workflows. |
| 11 | [Migration](11-%20Migration.md) | Environment and application migration strategies and considerations. |

---

## Learning Path

```text
Introduction
     │
     ▼
Core Components
     │
     ▼
Platforms
     │
     ▼
Configuration
     │
     ├───────────────┐
     ▼               ▼
Auto Scaling    Load Balancing
     │               │
     └───────┬───────┘
             ▼
          Storage
             │
             ▼
 Extensions & Platform Hooks
             │
             ▼
     Cloning & Migration
```

---

## Key Areas

### Fundamentals

Understand how Elastic Beanstalk abstracts infrastructure management while still exposing the underlying AWS resources.

### Configuration & Platforms

Learn how environments are configured and how platform choices affect application deployment and runtime behavior.

### Scalability & Availability

Understand how Auto Scaling and Load Balancing work together to handle changing traffic and maintain application availability.

### Customization

Learn how Extensions and Platform Hooks allow application environments to be customized beyond the default Elastic Beanstalk configuration.

### Environment Management

Understand how Cloning and Migration support testing, environment replication, and operational changes.

---

## Recommended Study Order

Follow the files in numerical order. Each topic builds on the concepts introduced in the previous sections.

```text
01 → Fundamentals
02 → Core Components
03 → Platforms
04 → Configuration
05 → Auto Scaling
06 → Load Balancing
07 → Storage
08 → Extensions
09 → Platform Hooks
10 → Cloning
11 → Migration
```

---

## Key Takeaways

- Elastic Beanstalk simplifies application deployment and infrastructure management on AWS.
- Understanding applications, environments, platforms, and configuration is the foundation for using the service effectively.
- Auto Scaling and Load Balancing provide the foundation for scalable and highly available environments.
- Extensions and Platform Hooks provide mechanisms for customizing environment behavior.
- Cloning and Migration cover important operational workflows for managing Elastic Beanstalk environments.
```