# Latency vs Throughput

## Overview

Latency and Throughput are two of the most important performance metrics in System Design.

Although they are closely related, they measure completely different aspects of a system.

Many beginners confuse these concepts because both are associated with system performance. However, optimizing one does not necessarily improve the other. In many real-world systems, increasing throughput can actually increase latency, and reducing latency may reduce overall throughput.

Understanding the difference between latency and throughput is essential before learning topics such as load balancing, caching, databases, distributed systems, and performance optimization.

---

# What is Latency?

Latency is the **time taken to complete a single request**.

It measures how long a user waits from sending a request until receiving the response.

In simple terms:

> Latency measures **how fast one request is processed**.

Latency is usually measured in:

- Milliseconds (ms)
- Microseconds (µs)
- Seconds (s)

Lower latency means a faster system.

---

# Latency Example

Suppose a user opens a shopping website.

```
Request Sent
      │
      ▼
Server Processes Request
      │
      ▼
Response Received
```

If the response arrives after **150 milliseconds**, then:

**Latency = 150 ms**

---

# Everyday Analogy

Imagine ordering coffee.

```
Customer places order
        │
        ▼
Barista prepares coffee
        │
        ▼
Customer receives coffee
```

The waiting time for one customer represents **latency**.

---

# What Affects Latency?

Several factors contribute to latency.

### Network Delay

The physical distance between client and server.

Example:

- User in India
- Server in the United States

The request naturally takes longer.

---

### Processing Time

The time required for the server to execute business logic.

Example:

- Authentication
- Database Queries
- Calculations

More complex operations generally increase latency.

---

### Database Performance

Slow database queries directly increase response time.

Common causes include:

- Missing indexes
- Large table scans
- Lock contention

---

### Disk I/O

Reading data from storage is significantly slower than reading from memory.

Using caches can dramatically reduce latency.

---

### External Services

Calling third-party APIs increases total response time.

Examples include:

- Payment gateways
- Email providers
- Maps APIs

---

# What is Throughput?

Throughput measures **how much work a system can perform in a given amount of time**.

Instead of measuring the time taken for one request, throughput measures how many requests can be processed.

In simple terms:

> Throughput measures **how much work the system can handle**.

Typical units include:

- Requests per Second (RPS)
- Transactions per Second (TPS)
- Queries per Second (QPS)
- Messages per Second

Higher throughput means the system can process more work.

---

# Throughput Example

Suppose a server processes:

- 5,000 requests every second

Then:

**Throughput = 5,000 Requests per Second (RPS)**

---

# Everyday Analogy

Consider a supermarket.

```
Checkout Counter

Customer 1 ✔
Customer 2 ✔
Customer 3 ✔
Customer 4 ✔
Customer 5 ✔
```

The number of customers served each minute represents **throughput**.

---

# Latency vs Throughput

| Latency | Throughput |
|----------|------------|
| Time taken for one request | Number of requests processed |
| Measured in milliseconds | Measured in requests per second |
| Lower is better | Higher is better |
| Focuses on speed | Focuses on capacity |
| User experience metric | System capacity metric |

---

# Relationship Between Latency and Throughput

Latency and throughput influence each other but are not the same.

For example:

### Scenario 1

One server processes:

- 1 request every 50 ms

The latency is excellent.

However, if only one request can be processed at a time, overall throughput remains low.

---

### Scenario 2

Another server processes:

- 20,000 requests simultaneously

Throughput is excellent.

However, if each request waits several seconds before processing, latency becomes poor.

---

# Can High Throughput Increase Latency?

Yes.

As more users send requests simultaneously:

- CPU usage increases
- Memory usage increases
- Database connections become busy
- Network congestion increases

Eventually requests begin waiting in queues.

```
Incoming Requests
        │
        ▼
Request Queue
        │
        ▼
Application Server
```

Waiting in the queue increases latency.

---

# Can Low Latency Reduce Throughput?

Yes.

Suppose every request receives its own dedicated resources.

Responses become extremely fast.

However, fewer requests can be processed simultaneously.

This increases latency performance but reduces throughput.

---

# Improving Latency

Engineers commonly reduce latency by:

- Using Redis or in-memory caching
- Optimizing database queries
- Adding indexes
- Using Content Delivery Networks (CDNs)
- Reducing network hops
- Compressing responses
- Eliminating unnecessary API calls
- Using faster hardware

The objective is to minimize the response time experienced by users.

---

# Improving Throughput

To increase throughput, engineers typically:

- Add more application servers
- Introduce load balancing
- Scale horizontally
- Use asynchronous processing
- Implement message queues
- Optimize algorithms
- Batch operations
- Increase parallelism

The objective is to process more work without overwhelming the system.

---

# Real-World Examples

### Google Search

Google aims for:

- Very low latency
- Extremely high throughput

Search results should appear almost instantly while handling billions of searches every day.

---

### Netflix

Netflix serves millions of users simultaneously.

Objectives include:

- High throughput for video streaming
- Low latency for playback

Caching and CDNs help achieve both.

---

### Banking Systems

Banks prioritize:

- Low latency for account operations
- Consistent throughput during peak hours

Accuracy is always more important than maximum throughput.

---

### E-commerce Platforms

During shopping festivals, platforms such as Amazon or Flipkart experience massive traffic spikes.

The architecture must:

- Maintain acceptable latency
- Increase throughput through auto-scaling and load balancing

---

# Choosing Between Latency and Throughput

The priority depends on the application's requirements.

| Application | Higher Priority |
|-------------|-----------------|
| Online Gaming | Low Latency |
| Video Calls | Low Latency |
| Banking | Low Latency |
| Search Engines | Both |
| Streaming Services | Both |
| Batch Processing | High Throughput |
| Analytics Systems | High Throughput |
| Log Processing | High Throughput |

---

# Common Mistakes

- Assuming latency and throughput are the same.
- Optimizing only one metric while ignoring the other.
- Measuring average latency instead of percentiles (P95, P99).
- Ignoring network latency.
- Running expensive database queries unnecessarily.
- Failing to scale infrastructure as traffic grows.

---

# Best Practices

- Measure both latency and throughput continuously.
- Optimize database queries before adding hardware.
- Use caching to reduce response time.
- Scale horizontally to improve throughput.
- Monitor latency percentiles rather than averages.
- Balance system capacity with user experience.
- Identify bottlenecks before optimizing performance.

---

# Key Takeaways

- **Latency** measures the time taken to process a single request.
- **Throughput** measures the amount of work a system can process over time.
- Low latency improves user experience, while high throughput improves system capacity.
- Improving one metric does not always improve the other.
- Successful distributed systems balance latency and throughput based on business requirements and expected workloads.