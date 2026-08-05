# Zero-Downtime Deployment

## Overview

Users expect applications to remain available even while new versions are being deployed. Stopping a container before starting a new one creates service interruptions, failed requests, and a poor user experience.

Zero-downtime deployment is a deployment strategy that replaces running application instances with new ones while continuing to serve user requests.

The objective is simple:

- Deploy new versions safely
- Keep the application available
- Minimize user impact
- Enable quick rollback if necessary

---

# What is Downtime?

Downtime occurs whenever users cannot access the application.

Example

```text
Application

↓

Deployment

↓

Application Stops

↓

Users Receive Errors
```

---

# Zero-Downtime Deployment

Instead of replacing the only running container:

```text
Version 1

↓

Version 2 Starts

↓

Traffic Switches

↓

Version 1 Stops
```

Users continue accessing the application throughout the deployment.

---

# Traditional Deployment

```text
Running Application

↓

Stop Container

↓

Deploy New Version

↓

Start Container

↓

Application Available
```

Problem

```text
Stop

↓

Unavailable

↓

Start
```

Every deployment introduces downtime.

---

# Zero-Downtime Workflow

```text
Version 1

↓

Start Version 2

↓

Health Check

↓

Switch Traffic

↓

Remove Version 1
```

No interruption occurs if the new version becomes healthy before traffic is switched.

---

# Deployment Architecture

```text
Internet

↓

Nginx

↓

Version 1

Version 2

↓

Database
```

Nginx routes requests only to healthy application instances.

---

# Rolling Deployment

Containers are updated gradually.

```text
App 1

↓

Update

↓

Healthy

↓

App 2

↓

Update

↓

Healthy

↓

App 3
```

Advantages:

- Reduced risk
- Continuous availability
- Easy monitoring during deployment

---

# Blue-Green Deployment

Maintain two identical environments.

```text
Blue Environment

↓

Serving Traffic

----------------------

Green Environment

↓

Deploy New Version

↓

Health Check

↓

Switch Traffic
```

After verification:

```text
Green

↓

Serving Users

↓

Blue

↓

Standby
```

Benefits:

- Fast rollback
- Minimal downtime
- Easy validation

---

# Canary Deployment

Release the new version to a small percentage of users.

```text
Users

↓

90%

↓

Version 1

--------------------

10%

↓

Version 2
```

If everything works correctly:

```text
10%

↓

25%

↓

50%

↓

100%
```

Canary deployments reduce deployment risk.

---

# Health Checks Before Switching

Never route traffic immediately.

```text
New Container

↓

Health Check

↓

Healthy?

↓

Yes

↓

Receive Traffic
```

If unhealthy:

```text
Health Check Failed

↓

Remove Container

↓

Keep Old Version
```

---

# Load Balancer Workflow

```text
Internet

↓

Load Balancer

↓

Healthy Container A

Healthy Container B

Healthy Container C
```

Only healthy containers receive requests.

---

# Database Considerations

Application deployments are usually easier than database changes.

Safe workflow

```text
Deploy Database Migration

↓

Backward Compatible

↓

Deploy Application

↓

Remove Old Schema Later
```

Avoid schema changes that immediately break older application versions.

---

# Stateless Applications

Zero-downtime deployment works best with stateless services.

```text
Application

↓

Database

↓

Persistent Storage
```

Application containers should not store session data locally.

---

# Session Management

Avoid:

```text
User Session

↓

Container Memory
```

Prefer:

```text
User Session

↓

Redis

↓

Shared Storage
```

Any container can then handle any request.

---

# Deployment Verification

Verify after deployment:

- Health endpoint
- Application logs
- Error rate
- Response time
- CPU usage
- Memory usage

Only complete deployment after successful verification.

---

# Rollback Strategy

If deployment fails:

```text
Deploy Version 2

↓

Health Check Failed

↓

Switch Back

↓

Version 1
```

Rollback should be automated whenever possible.

---

# CI/CD Workflow

```text
Developer

↓

Git Push

↓

CI Pipeline

↓

Build Image

↓

Deploy New Version

↓

Health Check

↓

Switch Traffic

↓

Remove Old Version
```

---

# Nginx Reverse Proxy

Nginx can control which version receives traffic.

```text
Internet

↓

Nginx

↓

Version 1

Version 2
```

Traffic is switched only after the new version becomes healthy.

---

# Monitoring During Deployment

Monitor:

- Request success rate
- Error rate
- CPU usage
- Memory usage
- Restart count
- Health checks

Continuous monitoring allows early detection of deployment issues.

---

# Common Mistakes

## Stopping the Old Version Too Early

Incorrect

```text
Stop Version 1

↓

Deploy Version 2
```

Always start and verify the new version first.

---

## Skipping Health Checks

Never route production traffic before confirming the new version is healthy.

---

## Breaking Database Compatibility

Schema changes should remain compatible with both old and new application versions during deployment.

---

## Storing Sessions in Containers

Container-local sessions prevent requests from being routed to any healthy instance.

Use shared session storage.

---

## No Rollback Plan

Every deployment should have a documented rollback procedure.

---

# Production Checklist

Before deployment:

- New image built
- Health checks passing
- Rollback plan available
- Monitoring enabled
- Database migration reviewed
- Stateless application verified
- Shared session storage configured
- Reverse proxy ready
- Traffic switching tested
- Deployment validated

---

# Best Practices

- Deploy new containers before removing old ones.
- Verify health before routing traffic.
- Use rolling or blue-green deployments for production systems.
- Keep applications stateless.
- Store sessions in shared storage such as Redis.
- Ensure database migrations are backward compatible.
- Monitor deployments continuously.
- Automate rollback whenever practical.

---

# Key Takeaways

- Zero-downtime deployment allows new application versions to be released without interrupting user access.
- Health checks and traffic switching are fundamental to safe deployments.
- Rolling, blue-green, and canary deployments each provide different trade-offs between simplicity, risk, and operational complexity.
- Stateless applications and shared session storage make zero-downtime deployments significantly easier.
- Reliable deployments combine automation, monitoring, health verification, and rollback procedures to minimize operational risk.