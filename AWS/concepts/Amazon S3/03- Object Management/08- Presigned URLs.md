# Presigned URLs

---

# Introduction

In modern cloud applications, clients often need temporary access to Amazon S3 objects without possessing AWS credentials. Sharing permanent credentials or making buckets public would introduce serious security risks.

**Presigned URLs** solve this problem by allowing trusted applications to generate time-limited URLs that grant temporary permission to upload or download specific objects.

They are one of the most widely used security patterns for Amazon S3.

---

# Why Presigned URLs?

Consider a web application where users upload profile pictures.

A poor design would be:

```text
Browser
   │
AWS Access Keys
   │
   ▼
Amazon S3
```

This exposes AWS credentials to the client.

A better design is:

```text
Browser
   │
Request Upload URL
   ▼
Backend API
   │
Generate Presigned URL
   ▼
Amazon S3
```

The browser receives only a temporary URL, never AWS credentials.

> 💡 **Engineering Insight**
>
> Presigned URLs delegate access to a single object for a limited time while keeping AWS credentials securely on the server.

---

# How Presigned URLs Work

A backend service signs an S3 request using AWS credentials.

The generated URL contains:

- Bucket name
- Object key
- Expiration time
- Cryptographic signature

Amazon S3 validates the signature before allowing access.

```text
Client
   │
Request URL
   ▼
Backend API
   │
Sign Request
   ▼
Amazon S3
   ▲
   │
Temporary URL
   │
Client Uploads / Downloads Object
```

---

# Common Use Cases

Presigned URLs are commonly used for:

- Browser uploads
- Mobile app uploads
- Secure downloads
- Temporary document sharing
- Video delivery
- Private image access

---

# Upload vs Download URLs

## Upload URL

Allows a client to upload an object directly into a bucket.

Typical workflow:

1. User requests upload.
2. Backend validates authorization.
3. Backend generates a presigned PUT URL.
4. Client uploads directly to Amazon S3.

---

## Download URL

Allows temporary access to an existing object.

Typical workflow:

1. User requests a document.
2. Backend verifies permissions.
3. Backend generates a presigned GET URL.
4. Client downloads directly from Amazon S3.

---

# Security Considerations

When generating presigned URLs:

- Use the shortest practical expiration time.
- Validate user authorization before generating the URL.
- Restrict uploads to expected object keys.
- Keep buckets private.
- Enable server-side encryption where appropriate.

> 🏗️ **Production Pattern**
>
> Production applications typically issue presigned URLs that expire within a few minutes rather than hours.

---

# Best Practices

- Generate URLs on the backend only.
- Use HTTPS.
- Log URL generation events.
- Validate file size and content type before issuing upload URLs.
- Combine presigned URLs with private buckets.

---

# Common Mistakes

- Using long expiration periods.
- Generating URLs without authorization checks.
- Exposing predictable object keys.
- Making buckets public instead of using presigned URLs.

> ⚠️ **Common Mistake**
>
> A presigned URL grants access to anyone who possesses it until it expires. Treat it like a temporary credential.

---

# Key Takeaways

Presigned URLs provide secure, temporary access to Amazon S3 objects without exposing AWS credentials or making buckets public. They are the preferred approach for browser and mobile uploads, secure downloads, and scalable cloud-native architectures.

This concludes the **Object Management** section. In the next section, we'll begin **Storage Classes** by understanding why Amazon S3 offers multiple storage tiers and how to choose the right one for different workloads.
