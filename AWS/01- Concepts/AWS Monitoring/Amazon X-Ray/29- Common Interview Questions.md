# Common Interview Questions

AWS X-Ray is frequently discussed in interviews for Cloud Engineers, DevOps Engineers, Backend Developers, Solutions Architects, and Site Reliability Engineers (SREs).

This chapter covers commonly asked interview questions.

------------------------------------------------------------------------

# Beginner Questions

## 1. What is AWS X-Ray?

**Answer**

AWS X-Ray is a managed distributed tracing service that helps monitor and debug applications by tracing requests across multiple services.

---

## 2. What is Distributed Tracing?

**Answer**

Distributed tracing follows a single request as it travels through multiple services, helping identify latency and failures.

---

## 3. What is a Trace?

**Answer**

A trace represents the complete lifecycle of one request and consists of one or more segments.

---

## 4. What is a Segment?

**Answer**

A segment records the work performed by a single service during request processing.

---

## 5. What is a Subsegment?

**Answer**

A subsegment represents a smaller operation within a segment, such as a database query or external API call.

------------------------------------------------------------------------

# Intermediate Questions

## 6. What is the Service Map?

**Answer**

The Service Map is a graphical representation of application components and their dependencies generated automatically from trace data.

---

## 7. Why is Sampling Required?

**Answer**

Sampling reduces the amount of trace data collected, lowering costs and application overhead.

---

## 8. What is the X-Ray Daemon?

**Answer**

The daemon collects trace data from the SDK and uploads it to AWS X-Ray.

---

## 9. What is the X-Ray SDK?

**Answer**

The SDK instruments applications to generate traces, segments, and subsegments.

---

## 10. What are Annotations?

**Answer**

Annotations are indexed key-value pairs used to search and filter traces.

------------------------------------------------------------------------

# Advanced Questions

## 11. What is the difference between Annotations and Metadata?

| Annotations | Metadata |
|-------------|----------|
| Indexed | Not indexed |
| Searchable | Not searchable |
| Used for filtering | Used for debugging |

---

## 12. How does X-Ray integrate with Lambda?

**Answer**

Lambda supports Active Tracing, automatically creating segments and tracing downstream AWS SDK calls.

---

## 13. How does X-Ray integrate with ECS?

**Answer**

Applications use the X-Ray SDK while the daemon typically runs as a sidecar container or Daemon Service.

---

## 14. Which IAM policy is commonly required?

**Answer**

```text
AWSXRayDaemonWriteAccess
```

---

## 15. How does X-Ray differ from CloudWatch?

**Answer**

CloudWatch monitors infrastructure and applications using metrics and logs, whereas X-Ray traces individual requests across distributed systems.

------------------------------------------------------------------------

# Scenario-Based Questions

## Scenario 1

Your API response time suddenly increases.

How would you investigate?

**Answer**

- Check the Service Map.
- Open slow traces.
- Analyze segment latency.
- Identify bottlenecks.
- Review CloudWatch metrics.

---

## Scenario 2

Only some services appear in the trace.

**Answer**

Verify:

- SDK instrumentation
- Daemon status
- IAM permissions
- Sampling configuration

---

## Scenario 3

A Lambda function is slow.

**Answer**

Use X-Ray to determine whether latency comes from:

- Cold starts
- Database calls
- External APIs
- Business logic

---

## Scenario 4

How would you trace requests across Kubernetes?

**Answer**

Deploy the X-Ray Daemon as a sidecar or DaemonSet and instrument applications using the SDK or OpenTelemetry.

------------------------------------------------------------------------

# Interview Tips

Remember:

- Trace = Complete request
- Segment = One service
- Subsegment = One operation
- SDK = Generates traces
- Daemon = Uploads traces
- Service Map = Visual dependencies
- Sampling = Cost optimization

------------------------------------------------------------------------

# Key Takeaways

- Understand traces, segments, and subsegments.
- Know how X-Ray integrates with AWS services.
- Be able to explain sampling and Service Maps.
- Expect architecture and troubleshooting questions in interviews.