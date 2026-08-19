# AWS CloudFront - Section 05: Cache Keys and Policies

# Why Cache Keys Matter

CloudFront caching is only effective if CloudFront can determine:

```text
Can I use an existing cached object?
OR
Do I need to contact the origin?
```

To make this decision, CloudFront uses:

```text
Cache Key
```

The Cache Key is one of the most important CloudFront concepts because it directly affects:

- Performance
- Cost
- Scalability
- Cache Hit Ratio

---

# What is a Cache Key?

A Cache Key is a unique identifier used by CloudFront to locate an object in cache.

Think of it like:

```text
Primary Key in a Database
```

CloudFront searches cache using the Cache Key.

If a match exists:

```text
Cache Hit
```

If no match exists:

```text
Cache Miss
```

---

# Default Cache Key

By default, CloudFront uses:

```text
Protocol
Host Header
URL Path
```

Example:

```text
https://example.com/images/logo.png
```

CloudFront creates a cache entry for:

```text
/images/logo.png
```

---

# Cache Key Example

Request 1:

```text
/images/logo.png
```

Request 2:

```text
/images/logo.png
```

Same Cache Key.

Result:

```text
Cache Hit
```

---

# Why Cache Keys Become Complex

Modern applications often serve different content based on:

```text
Headers
Cookies
Query Strings
```

CloudFront must know when content differs.

---

# Query Strings

## Example

Request 1:

```text
/products?id=100
```

Request 2:

```text
/products?id=200
```

Should CloudFront treat these as:

```text
Same Object?
```

or

```text
Different Objects?
```

Depends on your application.

---

# Query Strings in Cache Key

When query strings are included:

```text
/products?id=100
```

and

```text
/products?id=200
```

become:

```text
Different Cache Entries
```

---

# Query String Example

Cache Entries:

```text
/products?id=100
/products?id=101
/products?id=102
/products?id=103
```

Each object gets its own cache record.

---

# Headers

Headers may affect content generation.

Example:

```http
Accept-Language: en
```

Request:

```text
English Content
```

---

Another request:

```http
Accept-Language: fr
```

Response:

```text
French Content
```

---

# Header-Based Cache Key

CloudFront may need:

```text
Accept-Language
```

included in the Cache Key.

Result:

```text
Different Languages
Different Cache Entries
```

---

# Cookies

Applications frequently customize content using cookies.

Example:

```http
Cookie: theme=dark
```

Response:

```text
Dark Theme
```

---

Another request:

```http
Cookie: theme=light
```

Response:

```text
Light Theme
```

CloudFront may need cookie values in the Cache Key.

---

# Cache Key Components

CloudFront Cache Keys can include:

```text
URL Path
Headers
Cookies
Query Strings
```

---

# Cache Key Visualization

Simple Cache Key:

```text
/images/logo.png
```

---

Complex Cache Key:

```text
/images/logo.png
+ language=en
+ theme=dark
+ version=1
```

Every unique combination becomes a separate cache entry.

---

# Cache Fragmentation

## What is Cache Fragmentation?

Cache fragmentation occurs when CloudFront creates too many unique cache entries.

Example:

```text
Header A
Header B
Header C
Cookie A
Cookie B
Query String A
```

Thousands of combinations may exist.

Result:

```text
Low Cache Hit Ratio
```

---

# Example of Poor Cache Design

Including:

```text
User-Agent
```

inside Cache Key.

Requests:

```text
Chrome
Firefox
Safari
Edge
Mobile Chrome
Mobile Safari
```

All become separate cache entries.

Result:

```text
Cache Fragmentation
```

---

# Example of Good Cache Design

Include only values that truly change content.

Example:

```text
Accept-Language
```

because language affects content.

---

# Cache Policies

## What is a Cache Policy?

A Cache Policy controls:

```text
How CloudFront Caches Objects
```

It defines:

- Cache Key configuration
- TTL values
- Headers
- Cookies
- Query Strings

---

# Why Cache Policies Exist

Before Cache Policies:

CloudFront settings were mixed across multiple configurations.

AWS introduced Cache Policies to simplify management.

---

# Cache Policy Controls

A Cache Policy determines:

```text
What gets cached?
How long is it cached?
How is cache identified?
```

---

# Components of a Cache Policy

## TTL Settings

Controls:

```text
Minimum TTL
Default TTL
Maximum TTL
```

---

## Query Strings

Controls:

```text
Forward All
Forward None
Forward Specific
```

---

## Cookies

Controls:

```text
All Cookies
No Cookies
Specific Cookies
```

---

## Headers

Controls:

```text
All Headers
No Headers
Specific Headers
```

---

# Managed Cache Policies

AWS provides built-in policies.

Examples:

```text
CachingOptimized
CachingDisabled
Amplify
```

---

# CachingOptimized

Recommended for:

```text
Static Content
```

Characteristics:

```text
High Cache Efficiency
Minimal Cache Key
```

---

# CachingDisabled

Used when:

```text
Content Changes Frequently
```

CloudFront forwards every request.

---

# Custom Cache Policies

Organizations often create custom policies.

Example:

```text
Include:
Accept-Language

Exclude:
User-Agent
```

Provides better optimization.

---

# Origin Request Policy

## What is an Origin Request Policy?

Controls:

```text
What CloudFront Sends To The Origin
```

---

Important Distinction:

```text
Cache Policy
=
Cache Key
```

---

```text
Origin Request Policy
=
Origin Communication
```

---

# Example

CloudFront receives:

```http
Authorization Header
```

You may:

```text
Forward to Origin
```

but

```text
Not Include In Cache Key
```

---

# Why Useful?

Improves cache efficiency.

Origin still receives necessary data.

---

# Response Headers Policy

## What is a Response Headers Policy?

Controls headers CloudFront adds to responses.

Examples:

```text
Security Headers
CORS Headers
Custom Headers
```

---

# Security Header Example

Add:

```http
Strict-Transport-Security
```

to all responses.

Improves browser security.

---

# Relationship Between Policies

```text
Cache Policy
        |
Determines Cache Key
```

---

```text
Origin Request Policy
        |
Controls Origin Requests
```

---

```text
Response Headers Policy
        |
Controls Client Responses
```

---

# Real-World Example

E-Commerce Website

Request:

```text
/products?id=100
```

Requirements:

```text
Language Aware
```

Include:

```text
Accept-Language
```

---

Do NOT Include:

```text
User-Agent
```

Reason:

```text
No Content Difference
```

Improves cache hit ratio.

---

# Designing Efficient Cache Keys

Good Rule:

```text
Include Only
What Changes Content
```

---

# Good Candidates

```text
Language
Region
Product ID
```

---

# Bad Candidates

```text
Random Headers
Session IDs
User-Agent
Tracking Parameters
```

---

# Cache Key Optimization Strategy

Goal:

```text
Smallest Possible Cache Key
```

while still serving correct content.

---

# Common Mistakes

## Forwarding All Headers

Problem:

```text
Massive Cache Fragmentation
```

---

## Forwarding All Cookies

Problem:

```text
Low Cache Hit Ratio
```

---

## Forwarding Tracking Parameters

Examples:

```text
utm_source
utm_medium
utm_campaign
```

Usually unnecessary.

---

# Troubleshooting Cache Key Problems

## Symptom

High Origin Traffic

Possible Cause:

```text
Large Cache Key
```

---

## Symptom

Low Cache Hit Ratio

Possible Cause:

```text
Too Many Headers
Too Many Cookies
Too Many Query Strings
```

---

## Symptom

Unexpected Content

Possible Cause:

```text
Missing Header
Missing Cookie
Missing Query String
```

from Cache Key.

---

# Interview Questions

## Q1. What is a Cache Key?

A unique identifier CloudFront uses to locate cached objects.

---

## Q2. What can be included in a Cache Key?

- URL Path
- Headers
- Cookies
- Query Strings

---

## Q3. Why is Cache Key design important?

Because it directly affects:

- Cache Hit Ratio
- Performance
- Cost
- Scalability

---

## Q4. What is Cache Fragmentation?

The creation of too many cache entries due to an overly complex Cache Key.

---

## Q5. Difference Between Cache Policy and Origin Request Policy?

Cache Policy:

```text
Controls Caching
```

Origin Request Policy:

```text
Controls Data Sent To Origin
```

---

## Q6. Should User-Agent be included in Cache Key?

Usually no.

It often causes cache fragmentation without providing value.

---

## Q7. What is the best Cache Key design strategy?

Include only values that actually change the content returned by the application.

---

# Summary

Key Takeaways:

- Cache Keys determine cache hits and misses.
- Cache Policies define how objects are cached.
- Origin Request Policies define what is sent to origins.
- Response Header Policies define what is returned to users.
- Large Cache Keys reduce cache efficiency.
- Cache Fragmentation lowers Cache Hit Ratio.
- Efficient Cache Key design is one of the biggest CloudFront optimization techniques.
- Cache Key design is a very common interview topic for Cloud Engineer, DevOps Engineer, and Solutions Architect roles.

