# Static Website Hosting

---

# Introduction

Amazon S3 is more than an object storage service—it can also host static websites. This capability allows organizations to serve HTML, CSS, JavaScript, images, and other static assets directly from an S3 bucket without managing traditional web servers.

For personal websites, documentation portals, landing pages, and frontend applications, S3 provides a simple, scalable, and cost-effective hosting solution.

---

# What Is Static Website Hosting?

A static website consists of files that are delivered to users exactly as they are stored.

Typical assets include:

- HTML
- CSS
- JavaScript
- Images
- Fonts
- Videos

Unlike dynamic applications, no server-side code executes when a user requests a page.

> 💡 **Engineering Insight**
>
> Amazon S3 can host static content, but it cannot execute backend code such as Python, Java, PHP, or Node.js.

---

# How It Works

When Static Website Hosting is enabled, Amazon S3 exposes a website endpoint.

```text
User
   │
   ▼
Website Endpoint
   │
   ▼
Amazon S3 Bucket
   │
   ├── index.html
   ├── styles.css
   ├── app.js
   └── images/
```

When a browser requests the website, S3 returns the requested static object.

---

# Website Endpoint

Each bucket receives a Region-specific website endpoint.

Example:

```text
http://my-website.s3-website-ap-south-1.amazonaws.com
```

This endpoint differs from the REST API endpoint used by SDKs and CLI tools.

---

# Required Configuration

To host a website, configure:

- Static Website Hosting
- Index document (for example, `index.html`)
- Optional error document (`error.html`)
- Bucket permissions
- Public access (or CloudFront with Origin Access Control)

---

# Public Access Considerations

A website hosted directly from S3 typically requires public read access.

However, exposing buckets publicly is not recommended for production applications.

> 🏗️ **Production Pattern**
>
> Place Amazon CloudFront in front of the S3 bucket and use **Origin Access Control (OAC)** to keep the bucket private while serving content globally.

---

# Common Use Cases

Amazon S3 Static Website Hosting is commonly used for:

- Company websites
- Product landing pages
- Documentation sites
- Portfolio websites
- Single Page Applications (React, Angular, Vue)
- Internal knowledge portals

---

# Best Practices

- Use CloudFront for production deployments.
- Enable HTTPS through CloudFront.
- Store static assets in versioned object keys.
- Enable server-side encryption.
- Use lifecycle rules for old deployment artifacts.

---

# Common Mistakes

- Making the bucket publicly writable.
- Hosting production websites without CloudFront.
- Forgetting custom error pages.
- Disabling Block Public Access without understanding the security implications.
- Storing sensitive files in the website bucket.

> ⚠️ **Common Mistake**
>
> Public website hosting does **not** require every object in the bucket to be public. Separate public website assets from private application data.

---

# Key Takeaways

Amazon S3 Static Website Hosting provides a simple and highly scalable way to host static web content. While it is suitable for many frontend workloads, production deployments should generally combine Amazon S3 with Amazon CloudFront to improve security, performance, HTTPS support, and global content delivery.

This concludes the **Bucket Management** section. In the next section, we'll begin **Object Management**, starting with uploading objects to Amazon S3.
