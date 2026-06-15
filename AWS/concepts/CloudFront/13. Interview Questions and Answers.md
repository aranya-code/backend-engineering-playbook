# AWS CloudFront - Section 13: Interview Questions and Answers

# Beginner Level Questions

## Q1. What is Amazon CloudFront?

Amazon CloudFront is AWS's Content Delivery Network (CDN) service that delivers content through a global network of Edge Locations.

It improves:

- Performance
- Availability
- Security

by caching content closer to users.

---

## Q2. What is a CDN?

A Content Delivery Network (CDN) is a globally distributed network of servers that caches content near users to reduce latency and improve performance.

---

## Q3. Why use CloudFront?

Benefits:

- Lower latency
- Improved performance
- Reduced origin load
- Better scalability
- HTTPS support
- AWS WAF integration
- DDoS protection

---

## Q4. What is an Edge Location?

An Edge Location is an AWS location where CloudFront caches content.

Example:

```text
User (India)
     |
Mumbai Edge Location
```

Content is delivered from the nearest edge location whenever possible.

---

## Q5. What is an Origin?

An Origin is the backend source from which CloudFront retrieves content.

Examples:

```text
S3
ALB
EC2
API Gateway
Custom Server
```

---

## Q6. What is a Distribution?

A Distribution is the CloudFront configuration object that defines:

- Origins
- Cache behaviors
- Security settings
- Policies

---

# Intermediate Level Questions

## Q7. What happens when a user requests an object?

Flow:

```text
User
   |
Edge Location
   |
Cache Check
```

If object exists:

```text
Cache Hit
```

If object doesn't exist:

```text
Cache Miss
```

CloudFront retrieves the object from the origin.

---

## Q8. What is a Cache Hit?

A Cache Hit occurs when CloudFront serves content directly from cache without contacting the origin.

Benefits:

- Faster response
- Reduced cost
- Lower origin load

---

## Q9. What is a Cache Miss?

A Cache Miss occurs when CloudFront cannot find the requested object in cache and must retrieve it from the origin.

---

## Q10. What is TTL?

TTL (Time To Live) determines how long CloudFront stores an object in cache.

Example:

```text
TTL = 3600 Seconds
```

Object remains cached for one hour.

---

## Q11. What is Cache Invalidation?

Cache Invalidation removes objects from CloudFront cache before TTL expiration.

Example:

```text
/images/*
```

CloudFront removes matching cached objects.

---

## Q12. Why is object versioning preferred over invalidation?

Example:

Instead of:

```text
logo.png
```

Use:

```text
logo-v2.png
```

Benefits:

- Better caching
- Lower invalidation costs
- Simpler deployments

---

# Cache Policy Questions

## Q13. What is a Cache Key?

A Cache Key is the unique identifier CloudFront uses to locate objects in cache.

Can include:

```text
Path
Headers
Cookies
Query Strings
```

---

## Q14. What is Cache Fragmentation?

Cache Fragmentation occurs when too many unique cache entries are created.

Causes:

```text
Too Many Headers
Too Many Cookies
Too Many Query Strings
```

Result:

```text
Low Cache Hit Ratio
```

---

## Q15. Difference Between Cache Policy and Origin Request Policy?

### Cache Policy

Controls:

```text
Caching Behavior
Cache Key
TTL
```

### Origin Request Policy

Controls:

```text
Data Sent To Origin
```

---

# Security Questions

## Q16. What is OAC?

OAC (Origin Access Control) allows CloudFront to securely access S3 while preventing direct access to the bucket.

---

## Q17. Why is OAC preferred over OAI?

OAC:

- Modern architecture
- SigV4 support
- AWS recommended

OAI:

- Legacy mechanism

---

## Q18. What is AWS WAF?

AWS Web Application Firewall protects applications from:

```text
SQL Injection
XSS
Bots
```

---

## Q19. What is AWS Shield?

AWS Shield protects CloudFront from DDoS attacks.

---

## Q20. Difference Between Shield Standard and Shield Advanced?

### Shield Standard

Included automatically.

Provides:

```text
Basic DDoS Protection
```

---

### Shield Advanced

Paid service.

Provides:

```text
Advanced Protection
Detailed Visibility
Faster Mitigation
```

---

## Q21. What is Geo Restriction?

Geo Restriction allows access control based on country.

Example:

```text
Allow:
India
US

Block:
Others
```

---

## Q22. What is Field-Level Encryption?

Field-Level Encryption encrypts sensitive fields before data reaches the origin.

Example:

```text
Credit Card Number
```

---

# Signed URL Questions

## Q23. What is a Signed URL?

A Signed URL provides temporary access to a specific object.

Used for:

```text
PDF Downloads
Software Downloads
Private Files
```

---

## Q24. What is a Signed Cookie?

A Signed Cookie grants access to multiple protected resources.

Used for:

```text
Streaming Platforms
Learning Portals
Membership Sites
```

---

## Q25. Difference Between Signed URL and Signed Cookie?

| Feature | Signed URL | Signed Cookie |
|----------|------------|---------------|
| Scope | Single File | Multiple Files |
| Best Use Case | Downloads | Streaming |
| URL Changes | Yes | No |

---

# Edge Computing Questions

## Q26. What is CloudFront Functions?

CloudFront Functions provide lightweight edge computing for:

```text
Redirects
URL Rewrites
Header Manipulation
```

---

## Q27. What is Lambda@Edge?

Lambda@Edge allows Lambda functions to execute at CloudFront Edge Locations.

Used for:

```text
Authentication
Personalization
Routing
```

---

## Q28. Difference Between CloudFront Functions and Lambda@Edge?

| Feature | Functions | Lambda@Edge |
|----------|------------|------------|
| Cost | Lower | Higher |
| Speed | Faster | Slower |
| Complexity | Simple | Advanced |
| Triggers | 2 | 4 |

---

## Q29. When would you use Lambda@Edge?

Examples:

```text
JWT Validation
Authentication
A/B Testing
Dynamic Routing
```

---

# Monitoring Questions

## Q30. Which service monitors CloudFront?

```text
Amazon CloudWatch
```

---

## Q31. What metrics are important?

- Requests
- Cache Hit Rate
- 4xx Errors
- 5xx Errors
- Origin Latency

---

## Q32. Where are Access Logs stored?

```text
Amazon S3
```

---

## Q33. Difference Between Access Logs and Real-Time Logs?

Access Logs:

```text
Delayed
```

Real-Time Logs:

```text
Near Real-Time
```

---

# Scenario-Based Questions

## Q34. Users are reporting slow performance. What would you investigate?

Check:

```text
Cache Hit Rate
Origin Latency
4xx Errors
5xx Errors
```

---

## Q35. CloudFront costs doubled. What would you check?

Investigate:

```text
Traffic Growth
Cache Hit Ratio
Invalidations
Origin Requests
```

---

## Q36. Users are receiving 403 errors. What could be wrong?

Possible causes:

```text
OAC
WAF
Geo Restriction
Signed URL Expiration
Bucket Policy
```

---

## Q37. Cache Hit Ratio dropped from 90% to 40%. What would you check?

Review:

```text
Cache Policies
Headers
Cookies
Query Strings
TTL
```

---

## Q38. Origin is overloaded. What should you investigate?

Check:

```text
Cache Misses
TTL
Origin Capacity
Cache Key Design
```

---

# Senior-Level Questions

## Q39. Design a secure static website using CloudFront.

Architecture:

```text
Users
   |
HTTPS
   |
CloudFront
   |
AWS WAF
   |
OAC
   |
S3
```

Security:

- HTTPS
- OAC
- WAF
- Shield

---

## Q40. Design a video streaming platform.

Architecture:

```text
Users
   |
CloudFront
   |
S3
```

Security:

```text
Signed Cookies
HTTPS
WAF
OAC
```

---

## Q41. Design a global e-commerce application.

Architecture:

```text
Users
   |
CloudFront
   |
+-------------+
|             |
v             v
S3           ALB
             |
             ECS
```

Routing:

```text
/images/* -> S3
/api/* -> ALB
```

---

## Q42. How would you improve CloudFront performance?

Methods:

```text
Increase Cache Hit Ratio
Optimize Cache Keys
Use Compression
Increase TTL
Reduce Invalidations
```

---

## Q43. How would you reduce CloudFront costs?

Methods:

```text
Improve Cache Hit Ratio
Reduce Origin Requests
Compress Content
Optimize Policies
Use Versioning
```

---

# Troubleshooting Questions

## Q44. How would you troubleshoot 502 errors?

Check:

```text
Origin Availability
DNS
SSL Certificates
Connectivity
```

---

## Q45. How would you troubleshoot 504 errors?

Check:

```text
Origin Latency
Database Performance
Application Logs
```

---

## Q46. How would you troubleshoot low Cache Hit Ratio?

Review:

```text
TTL
Headers
Cookies
Query Strings
```

---

## Q47. How would you troubleshoot WAF blocking users?

Check:

```text
WAF Logs
Rule Matches
Rate Limits
Geo Restrictions
```

---

# Architect-Level Questions

## Q48. How would you design CloudFront for high availability?

Use:

```text
Origin Groups
Multi-AZ
Auto Scaling
Monitoring
```

---

## Q49. How would you secure CloudFront in production?

Implement:

```text
HTTPS
AWS WAF
AWS Shield
OAC
Signed URLs/Cookies
Logging
```

---

## Q50. What are the top CloudFront best practices?

1. Use OAC.
2. Enforce HTTPS.
3. Optimize Cache Keys.
4. Improve Cache Hit Ratio.
5. Use Versioning.
6. Enable WAF.
7. Enable Monitoring.
8. Configure Origin Failover.

---

# 10 Rapid-Fire Interview Questions

### What is CloudFront?

AWS CDN service.

---

### What is an Edge Location?

CloudFront cache location.

---

### What is a Cache Hit?

Content served from cache.

---

### What is a Cache Miss?

Content retrieved from origin.

---

### What is OAC?

Secure S3 access through CloudFront.

---

### What is WAF?

Web Application Firewall.

---

### What is Lambda@Edge?

Serverless edge computing.

---

### What is a Signed URL?

Temporary access to one object.

---

### What is a Signed Cookie?

Temporary access to multiple objects.

---

### What metric indicates cache efficiency?

Cache Hit Ratio.

---

# Final Interview Tips

Interviewers usually evaluate:

```text
Architecture Knowledge
Caching Knowledge
Security Knowledge
Troubleshooting Ability
Cost Optimization Skills
```

Always explain answers using:

```text
Performance
Security
Availability
Cost
```

framework.

Example:

Question:

```text
Why use CloudFront?
```

Answer:

```text
Performance:
Lower Latency

Security:
WAF, Shield, HTTPS

Availability:
Global Edge Network

Cost:
Reduced Origin Traffic
```

This structure demonstrates senior-level thinking.

---

# Final Summary

If you master:

```text
Architecture
Origins
Caching
Policies
Security
Signed URLs
Edge Computing
Monitoring
Troubleshooting
Real-World Scenarios
```

you will be prepared for:

- Cloud Engineer Interviews
- DevOps Engineer Interviews
- SRE Interviews
- Solutions Architect Interviews
- Senior Infrastructure Roles

CloudFront is not just a CDN.
