# AWS CloudFront - Section 07: Signed URLs and Signed Cookies

# Why Do We Need Signed URLs and Signed Cookies?

By default, CloudFront content is public.

Example:

```text
https://d123abc.cloudfront.net/video.mp4
```

Anyone with the URL can access the file.

---

## Problem

Consider a premium video platform.

Content:

```text
course1.mp4
course2.mp4
course3.mp4
```

Requirements:

- Only paid users can access content.
- Access should expire.
- Shared links should stop working after some time.

Normal CloudFront URLs cannot enforce these requirements.

---

# Solution

CloudFront provides:

```text
1. Signed URLs
2. Signed Cookies
```

These mechanisms allow temporary access to private content.

---

# Private Content Architecture

```text
User
  |
Application
  |
Generate Signature
  |
CloudFront
  |
Protected Content
```

CloudFront validates access before serving content.

---

# What is a Signed URL?

A Signed URL is a CloudFront URL that contains:

- Expiration Time
- Cryptographic Signature
- Key Pair Information

The URL becomes valid only for a specific period.

---

# Signed URL Components

Example:

```text
https://d123abc.cloudfront.net/video.mp4
?Expires=1735689600
&Signature=abcxyz
&Key-Pair-Id=APK123456
```

Components:

### URL

```text
video.mp4
```

Object being accessed.

---

### Expires

```text
1735689600
```

Expiration timestamp.

---

### Signature

```text
abcxyz
```

Used by CloudFront to verify authenticity.

---

### Key Pair ID

Identifies the public key used for validation.

---

# How Signed URLs Work

Step 1:

User logs in.

---

Step 2:

Application validates permissions.

---

Step 3:

Application generates Signed URL.

---

Step 4:

User receives URL.

---

Step 5:

User accesses CloudFront.

---

Step 6:

CloudFront validates:

```text
Signature
Expiration
Policy
```

---

Step 7:

Content delivered.

---

# Signed URL Flow

```text
User
  |
Application
  |
Generate Signed URL
  |
CloudFront
  |
Protected Object
```

---

# Real-World Example

Online Course Platform.

User purchases:

```text
Docker Course
```

Application generates:

```text
Signed URL
```

Valid for:

```text
2 Hours
```

After expiration:

```text
Access Denied
```

---

# Benefits of Signed URLs

## Temporary Access

Access automatically expires.

---

## Object-Level Security

Protect individual files.

---

## Easy Sharing Control

Links become invalid after expiration.

---

## Reduced Risk

Unauthorized users cannot access content.

---

# What is a Signed Cookie?

A Signed Cookie grants access to multiple files using browser cookies.

Instead of signing each URL individually:

```text
video1.mp4
video2.mp4
video3.mp4
```

CloudFront validates a cookie.

---

# Why Signed Cookies Exist

Imagine Netflix.

A user watches:

```text
Movie
Poster
Subtitles
Video Segments
```

Hundreds of requests occur.

Generating a Signed URL for every request is inefficient.

---

# Solution

Use:

```text
Signed Cookie
```

---

# Signed Cookie Flow

```text
User
  |
Login
  |
Application
  |
Generate Cookie
  |
Browser
  |
CloudFront
```

Browser automatically sends cookie.

---

# How Signed Cookies Work

Step 1:

User logs in.

---

Step 2:

Application validates user.

---

Step 3:

Application creates signed cookie.

---

Step 4:

Cookie stored in browser.

---

Step 5:

Browser requests content.

---

Step 6:

Cookie sent automatically.

---

Step 7:

CloudFront validates cookie.

---

Step 8:

Content served.

---

# Signed Cookie Components

CloudFront typically creates:

```text
CloudFront-Policy
CloudFront-Signature
CloudFront-Key-Pair-Id
```

Stored as browser cookies.

---

# Example Architecture

```text
User
  |
Browser
  |
Signed Cookie
  |
CloudFront
  |
Protected Content
```

---

# Signed URL vs Signed Cookie

| Feature | Signed URL | Signed Cookie |
|----------|------------|---------------|
| Access Scope | Single Object | Multiple Objects |
| URL Changes | Yes | No |
| Browser Cookie Required | No | Yes |
| Best Use Case | Downloads | Streaming Sites |
| User Experience | Moderate | Better |
| Management | Per File | Per Session |

---

# When to Use Signed URLs

Use Signed URLs when:

```text
Single File Access
```

Examples:

- PDF download
- Software installer
- Paid report
- One-time file access

---

# Example

```text
download.pdf
```

Generate:

```text
Signed URL
```

Valid:

```text
30 Minutes
```

---

# When to Use Signed Cookies

Use Signed Cookies when:

```text
Multiple Files Access
```

Examples:

- Netflix
- Udemy
- Internal Portal
- Membership Site

---

# Example

User accesses:

```text
video1.mp4
video2.mp4
video3.mp4
images
subtitles
```

One cookie grants access.

---

# CloudFront Trusted Key Groups

## What Are Key Groups?

CloudFront validates signatures using public keys.

Architecture:

```text
Private Key
     |
Generate Signature
     |
CloudFront
     |
Public Key
```

---

# Why Use Key Groups?

Benefits:

- Key rotation
- Improved security
- Centralized management

---

# Custom Policies

CloudFront supports:

```text
Canned Policy
Custom Policy
```

---

# Canned Policy

Simpler.

Includes:

```text
Expiration Time
```

Only.

---

# Example

```text
Valid Until:
6 PM
```

After that:

```text
Access Denied
```

---

# Custom Policy

Supports:

```text
Expiration
IP Restrictions
Start Time
```

More flexible.

---

# Example

Allow access:

```text
Only From India
```

or

```text
Only Corporate IP Range
```

---

# IP Restriction Example

```text
Allow:
203.0.113.0/24
```

Other IPs:

```text
Denied
```

---

# Security Best Practices

## Use Short Expiration Times

Bad:

```text
30 Days
```

Good:

```text
30 Minutes
2 Hours
```

---

## Use HTTPS

Never distribute Signed URLs over HTTP.

---

## Rotate Keys

Regularly rotate signing keys.

---

## Principle of Least Privilege

Grant minimum required access.

---

# Real-World Architectures

## Online Course Platform

```text
Users
   |
Application
   |
Signed URL
   |
CloudFront
   |
S3
```

---

## Video Streaming Platform

```text
Users
   |
Login
   |
Signed Cookie
   |
CloudFront
   |
S3
```

---

## Enterprise Document Portal

```text
Users
   |
Authentication
   |
Signed URL
   |
CloudFront
   |
Private Documents
```

---

# Common Mistakes

## Long Expiration Times

Risk:

```text
Link Sharing
```

---

## Public S3 Bucket

Users bypass CloudFront.

Use:

```text
OAC
```

---

## Missing HTTPS

Risk:

```text
URL Exposure
```

---

## No Key Rotation

Security weakness.

---

# Troubleshooting

## Access Denied

Possible Causes:

- Expired URL
- Invalid Signature
- Incorrect Policy
- Wrong Key Pair

---

## Signed Cookie Not Working

Possible Causes:

- Cookie not sent
- Domain mismatch
- Expired cookie

---

## Random Authentication Failures

Check:

```text
System Time
Expiration Settings
```

---

# Interview Questions

## Q1. What is a Signed URL?

A URL containing a cryptographic signature that grants temporary access to a specific object.

---

## Q2. What is a Signed Cookie?

A browser cookie that grants access to multiple protected objects.

---

## Q3. When should Signed URLs be used?

When access is required for a single object.

Example:

```text
PDF Download
```

---

## Q4. When should Signed Cookies be used?

When users need access to multiple protected resources.

Example:

```text
Streaming Platform
```

---

## Q5. Difference Between Signed URL and Signed Cookie?

Signed URL:

```text
Single Object
```

Signed Cookie:

```text
Multiple Objects
```

---

## Q6. Why use short expiration times?

To reduce unauthorized sharing and replay risks.

---

## Q7. What is a Trusted Key Group?

A CloudFront mechanism used to validate signatures using public keys.

---

## Q8. What is the difference between a Canned Policy and a Custom Policy?

Canned Policy:

```text
Expiration Only
```

Custom Policy:

```text
Expiration
IP Restrictions
Start Time
```

---

# Summary

Key Takeaways:

- Signed URLs secure individual objects.
- Signed Cookies secure multiple objects.
- CloudFront validates signatures before serving content.
- Trusted Key Groups manage signing keys.
- Canned Policies are simple.
- Custom Policies provide advanced controls.
- Short expiration times improve security.
- Signed URLs and Signed Cookies are commonly used in streaming, premium content, enterprise portals, and subscription-based applications.

In real-world architectures:

```text
Single File Access
    ->
Signed URL

Multiple Resource Access
    ->
Signed Cookie
```

