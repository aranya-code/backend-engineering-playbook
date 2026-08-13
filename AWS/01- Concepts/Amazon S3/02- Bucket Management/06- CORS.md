# Cross-Origin Resource Sharing (CORS)

---

# Introduction

Modern web applications often consist of multiple components hosted on different domains. For example, a React application may be hosted on one domain while images, videos, or downloadable documents are stored in Amazon S3.

By default, web browsers block requests made across different origins for security reasons. **Cross-Origin Resource Sharing (CORS)** is the mechanism that allows Amazon S3 to explicitly permit trusted cross-origin requests.

Without CORS, browsers may prevent JavaScript applications from interacting with objects stored in Amazon S3, even when the user has permission to access them.

---

# What Is CORS?

CORS (Cross-Origin Resource Sharing) is a browser security mechanism that controls whether a web page hosted on one origin can access resources hosted on another origin.

An **origin** consists of:

- Protocol (HTTP or HTTPS)
- Domain
- Port

For example:

```text
Frontend
https://app.example.com

Amazon S3
https://my-assets.s3.amazonaws.com
```

These are different origins, so the browser applies CORS rules.

> 💡 **Engineering Insight**
>
> CORS is enforced by browsers—not by Amazon S3 itself. Applications using the AWS SDK, CLI, or backend services are not restricted by browser CORS policies.

---

# How CORS Works

When a browser makes a cross-origin request, it checks the bucket's CORS configuration.

```text
Browser
    │
    ▼
Request Object
    │
    ▼
Amazon S3
    │
Check CORS Rules
    │
 ┌──┴───────────┐
 │              │
Allowed      Not Allowed
 │              │
 ▼              ▼
Return Data   Browser Blocks Access
```

If the request matches an allowed rule, the browser allows the response to be accessed by JavaScript.

---

# CORS Configuration

A CORS rule defines:

- Allowed Origins
- Allowed Methods
- Allowed Headers
- Exposed Headers
- Max Age

Example:

```json
[
  {
    "AllowedOrigins": [
      "https://app.example.com"
    ],
    "AllowedMethods": [
      "GET",
      "PUT"
    ],
    "AllowedHeaders": [
      "*"
    ]
  }
]
```

---

# Common Use Cases

CORS is commonly required for:

- Single Page Applications (SPA)
- React applications
- Angular applications
- Vue applications
- Direct browser uploads using Presigned URLs
- Image galleries
- Video streaming applications

---

# Production Example

A typical upload workflow:

```text
User
   │
   ▼
React Application
   │
Request Presigned URL
   │
   ▼
Backend API
   │
Generate URL
   │
   ▼
Amazon S3
   ▲
   │
Browser Upload (CORS)
```

The browser communicates directly with Amazon S3, making CORS configuration essential.

> 🏗️ **Production Pattern**
>
> Configure CORS only for trusted frontend domains. Avoid using `"*"` for `AllowedOrigins` unless the content is intentionally public.

---

# Best Practices

- Allow only trusted origins.
- Restrict HTTP methods to those required.
- Minimize allowed headers.
- Test CORS using browser developer tools.
- Review CORS rules whenever frontend domains change.

---

# Common Mistakes

- Allowing every origin (`*`) unnecessarily.
- Forgetting to allow `PUT` for browser uploads.
- Confusing IAM permission errors with CORS errors.
- Assuming CORS affects backend services.

> ⚠️ **Common Mistake**
>
> A successful IAM permission check does not guarantee a browser request will succeed. Incorrect CORS settings can still cause the browser to block access.

---

# Key Takeaways

CORS enables secure communication between browser-based applications and Amazon S3 across different origins. Properly configured CORS policies allow modern frontend applications to upload and retrieve objects while maintaining browser security protections.

In the next chapter, we'll explore **Static Website Hosting** and learn how Amazon S3 can serve static web applications directly without traditional web servers.
