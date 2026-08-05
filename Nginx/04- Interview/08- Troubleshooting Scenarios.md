# Overview

Troubleshooting questions are among the most common in backend and DevOps interviews because they assess practical experience rather than theoretical knowledge. Interviewers often present a production issue and expect you to explain how you would investigate, identify the root cause, and resolve it.

Rather than memorizing solutions, focus on following a structured troubleshooting process.

---

# General Troubleshooting Approach

Whenever you encounter an issue, follow a systematic workflow.

```text
Identify the Problem
        │
        ▼
Collect Error Messages
        │
        ▼
Check Nginx Logs
        │
        ▼
Validate Configuration
        │
        ▼
Verify Backend Service
        │
        ▼
Test the Fix
        │
        ▼
Deploy Safely
```

A structured approach reduces downtime and prevents unnecessary changes.

---

# Scenario 1 — Nginx Won't Start

### Interview Question

Nginx fails to start after updating the configuration. How would you troubleshoot the issue?

### Expected Approach

1. Validate the configuration.
2. Review the error log.
3. Identify the failing directive.
4. Correct the configuration.
5. Restart or reload Nginx.

### Common Causes

- Missing semicolon
- Invalid directive
- Duplicate configuration
- Invalid file path
- Port already in use

---

# Scenario 2 — 502 Bad Gateway

### Interview Question

Users receive a **502 Bad Gateway** error. What could be the cause?

### Possible Causes

- Backend application is down
- Incorrect `proxy_pass`
- Wrong upstream configuration
- Firewall restrictions
- Backend port not listening

### Investigation

- Verify backend service status.
- Check the Nginx error log.
- Test backend connectivity.
- Confirm upstream configuration.
- Validate network connectivity.

---

# Scenario 3 — 504 Gateway Timeout

### Interview Question

What causes a **504 Gateway Timeout**?

### Possible Causes

- Slow backend
- Database bottleneck
- Long-running API request
- Network latency
- Timeout configuration too low

### Investigation

- Measure backend response time.
- Review application logs.
- Examine database performance.
- Check timeout settings.
- Identify blocking operations.

---

# Scenario 4 — Static Files Return 404

### Interview Question

Static files work locally but return **404 Not Found** in production.

### Possible Causes

- Incorrect `root`
- Incorrect `alias`
- Wrong file permissions
- Missing files
- Incorrect location matching

### Investigation

- Verify file path.
- Review location blocks.
- Check directory permissions.
- Validate deployment process.

---

# Scenario 5 — HTTPS Isn't Working

### Interview Question

HTTPS suddenly stops working after certificate renewal.

### Possible Causes

- Incorrect certificate path
- Expired certificate
- Missing private key
- Invalid permissions
- Configuration error

### Investigation

- Verify certificate files.
- Check expiration date.
- Validate SSL configuration.
- Review error logs.

---

# Scenario 6 — High CPU Usage

### Interview Question

The server CPU suddenly reaches 100%.

### Possible Causes

- Traffic spike
- Infinite redirect loop
- Expensive backend requests
- DDoS attack
- Excessive logging

### Investigation

- Check active connections.
- Review access logs.
- Examine request patterns.
- Verify backend health.
- Monitor system resources.

---

# Scenario 7 — High Memory Usage

### Interview Question

Nginx memory usage keeps increasing.

### Possible Causes

- Large buffers
- Too many connections
- Memory-intensive modules
- Traffic surge

### Investigation

- Review worker settings.
- Check buffer configuration.
- Monitor connection counts.
- Analyze traffic volume.

---

# Scenario 8 — SSL Handshake Failure

### Interview Question

Clients report SSL handshake errors.

### Possible Causes

- Unsupported TLS version
- Invalid certificate
- Cipher mismatch
- Incorrect certificate chain

### Investigation

- Verify certificate chain.
- Review TLS configuration.
- Check supported cipher suites.
- Test using multiple browsers.

---

# Scenario 9 — Client IP Address Is Incorrect

### Interview Question

Your application always receives the Nginx IP instead of the client IP.

### Expected Solution

Configure proxy headers.

Example:

```nginx
proxy_set_header X-Real-IP $remote_addr;

proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

---

# Scenario 10 — Backend Works Directly but Fails Through Nginx

### Interview Question

Accessing the backend directly works, but requests through Nginx fail.

### Investigation

- Verify `proxy_pass`.
- Check upstream configuration.
- Confirm DNS resolution.
- Examine firewall rules.
- Review request headers.
- Compare direct and proxied requests.

---

# Scenario 11 — Infinite Redirect Loop

### Interview Question

The browser continuously redirects between HTTP and HTTPS.

### Possible Causes

- Incorrect redirect rules
- Backend also forcing HTTPS
- Reverse proxy misconfiguration

### Investigation

- Review redirect configuration.
- Check proxy headers.
- Verify backend URL generation.
- Confirm HTTPS termination point.

---

# Scenario 12 — Load Balancing Doesn't Work

### Interview Question

All requests go to the same backend server.

### Possible Causes

- Only one upstream server
- Sticky session configuration
- Incorrect load-balancing method
- Health check failures

### Investigation

- Verify upstream configuration.
- Review load-balancing algorithm.
- Check backend availability.

---

# Production Troubleshooting Checklist

When diagnosing production issues, verify:

- Nginx configuration
- Backend application
- Network connectivity
- DNS resolution
- SSL certificates
- File permissions
- Disk space
- CPU usage
- Memory usage
- Active connections
- Logs
- Firewall configuration

Following a consistent checklist helps avoid overlooking common causes.

---

# Interview Tips

During troubleshooting interviews:

- Explain your thought process.
- Avoid jumping directly to a solution.
- Start with the simplest checks.
- Use logs to support your conclusions.
- Consider both Nginx and the backend application.
- Mention how you would verify the fix after implementing it.

Interviewers are often more interested in your diagnostic approach than your final answer.

---

# Best Practices

- Always validate configuration changes before deployment.
- Monitor logs continuously.
- Keep backups of working configurations.
- Deploy configuration changes gradually.
- Document recurring production issues.
- Perform root cause analysis after major incidents.

---

# Key Takeaways

- Troubleshooting interviews evaluate your ability to diagnose production issues methodically.
- Follow a structured process: identify the problem, collect evidence, investigate, fix, and verify.
- Common issues include startup failures, gateway errors, SSL problems, incorrect routing, and performance bottlenecks.
- Logs, configuration validation, and backend health checks are the primary tools for diagnosing problems.
- Clearly explaining your troubleshooting methodology is often more valuable in interviews than simply providing the correct answer.