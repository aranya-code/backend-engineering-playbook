# Multipart Upload

---

# Introduction

Uploading large files using a single HTTP request is inefficient and unreliable. If the connection is interrupted near the end of a multi-gigabyte upload, the entire transfer must usually start again.

Amazon S3 solves this problem with **Multipart Upload**, which allows a large object to be split into smaller parts that are uploaded independently and then combined into a single object.

Multipart Upload is one of the most important performance optimization techniques for Amazon S3 and should be the default choice for large objects.

---

# Why Multipart Upload?

Consider uploading a 50 GB backup file.

With a traditional upload:

- A single network interruption can fail the entire upload.
- The upload must often restart from the beginning.
- Only one request transfers data.

With Multipart Upload:

- The file is divided into parts.
- Parts upload independently.
- Failed parts can be retried without affecting successful parts.
- Multiple parts can upload in parallel.

> 💡 **Engineering Insight**
>
> Multipart Upload improves both reliability and throughput. Parallel uploads often complete significantly faster than a single large upload.

---

# How Multipart Upload Works

```text
Large File
    │
Split into Parts
    │
 ┌──┬──┬──┬──┐
 │1 │2 │3 │4 │
 └──┴──┴──┴──┘
    │
Upload in Parallel
    │
Amazon S3
    │
Assemble Object
    │
Upload Complete
```

Each uploaded part is stored temporarily until the upload is completed.

---

# Multipart Upload Lifecycle

A multipart upload consists of three stages.

## 1. Initiate Upload

Amazon S3 returns a unique **Upload ID**.

---

## 2. Upload Parts

Each part is uploaded independently.

Characteristics:

- Can be uploaded in parallel
- Can be retried individually
- Receives its own ETag

---

## 3. Complete Upload

The client sends the Upload ID together with the list of uploaded parts.

Amazon S3 combines the parts into a single object.

---

# Benefits

Multipart Upload provides:

- Higher throughput
- Fault tolerance
- Parallel uploads
- Reduced retry costs
- Better network utilization
- Improved reliability for unstable connections

---

# When Should You Use Multipart Upload?

Multipart Upload is recommended for:

- Large media files
- Database backups
- Log archives
- Machine learning datasets
- Software distributions
- Any upload larger than approximately 100 MB

Many AWS SDKs automatically switch to Multipart Upload for large files.

> 🏗️ **Production Pattern**
>
> Configure SDKs to use Multipart Upload automatically for large objects instead of implementing custom upload logic.

---

# Security Considerations

Multipart Upload follows the same security model as standard uploads.

Ensure that:

- IAM permissions are correct.
- Default encryption is enabled.
- Presigned URLs expire appropriately.
- Abandoned uploads are cleaned up.

---

# Cleaning Up Incomplete Uploads

Interrupted uploads leave temporary parts in Amazon S3.

Although they are not visible as completed objects, they continue to consume storage.

Use Lifecycle Rules to automatically abort incomplete multipart uploads after a specified number of days.

---

# Best Practices

- Upload parts in parallel.
- Retry only failed parts.
- Abort uploads that will never complete.
- Configure lifecycle rules to clean up incomplete uploads.
- Monitor failed uploads.

---

# Common Mistakes

- Uploading very large files with a single request.
- Forgetting to complete or abort uploads.
- Ignoring storage costs for incomplete uploads.
- Using very small part sizes that reduce efficiency.

> ⚠️ **Common Mistake**
>
> An incomplete multipart upload is not automatically removed. Without lifecycle cleanup, unfinished uploads can accumulate unnecessary storage costs.

---

# Key Takeaways

Multipart Upload is the preferred method for transferring large objects to Amazon S3. By splitting files into independently uploaded parts, it improves performance, resilience, and scalability while minimizing the impact of network failures.

In the next chapter, we'll explore **Presigned URLs** and learn how applications securely grant temporary access to Amazon S3 objects without exposing AWS credentials.
