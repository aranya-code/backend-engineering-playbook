# 06- Mock Interview

# Overview

This chapter simulates a senior backend engineering interview focused on AWS Lambda. The questions progress from fundamental concepts to architecture, production troubleshooting, security, scalability, and system design.

The purpose is not only to test your AWS Lambda knowledge but also to improve how you communicate technical decisions during interviews.

Imagine you're interviewing for roles such as:

- Senior Backend Engineer
- Software Engineer III
- Staff Engineer
- Cloud Engineer
- Platform Engineer
- Solution Architect

---

# Interview Structure

The interview is divided into five rounds.

```
Introduction

↓

Fundamentals

↓

Architecture

↓

Production Scenarios

↓

System Design

↓

Behavioral Discussion
```

---

# Round 1 — Introduction

## Interviewer

Tell me about yourself.

### What the interviewer wants

- Technical background
- Current role
- AWS experience
- Backend expertise
- Communication skills

---

## Interviewer

Tell me about a production application where you used AWS Lambda.

### Follow-up Questions

- Why Lambda?
- What problem did it solve?
- Why not ECS?
- Biggest challenge?
- What would you improve today?

---

# Round 2 — Fundamentals

## Question 1

What happens internally when Lambda receives a request?

Expected discussion:

- Invocation
- Execution Environment
- Runtime Initialization
- Handler Execution
- Response
- Environment Reuse

---

## Question 2

Explain Cold Starts.

Follow-up

- Why do they happen?
- How can they be reduced?
- Are they always bad?

---

## Question 3

Explain Warm Starts.

Expected discussion

```
Execution Environment

↓

Freeze

↓

Reuse
```

---

## Question 4

Difference between synchronous and asynchronous invocation?

Expected examples

Synchronous

- API Gateway
- Function URL

Asynchronous

- SNS
- EventBridge
- S3

---

## Question 5

What is Event Source Mapping?

Expected discussion

- Polling
- Batch processing
- Retry
- Partial batch failure

---

# Round 3 — Architecture

## Question 6

Design a REST API using Lambda.

Expected architecture

```
CloudFront

↓

API Gateway

↓

Lambda

↓

Aurora
```

Discuss:

- Authentication
- Monitoring
- Scaling
- Cost

---

## Question 7

How would you process uploaded images?

Expected architecture

```
S3

↓

Lambda

↓

Resize

↓

S3
```

Possible improvements

- SQS
- Step Functions
- EventBridge

---

## Question 8

How would you process one million SQS messages?

Expected discussion

- Batch size
- Concurrency
- DLQ
- Visibility Timeout
- Idempotency

---

## Question 9

Why use EventBridge instead of Lambda calling another Lambda?

Expected answer

Loose coupling.

Independent deployment.

Scalable architecture.

---

## Question 10

Would you choose Lambda or ECS?

Interviewer expects trade-off analysis.

---

# Round 4 — Production

## Question 11

Your Lambda suddenly times out.

How do you investigate?

Expected workflow

```
CloudWatch

↓

Logs

↓

Metrics

↓

X-Ray

↓

Root Cause
```

---

## Question 12

CloudWatch shows throttling.

What happened?

Possible answers

- Traffic spike
- Concurrency limit
- Long execution time

---

## Question 13

Aurora reports

```
Too many connections
```

How do you fix it?

Expected discussion

```
Lambda

↓

RDS Proxy

↓

Aurora
```

---

## Question 14

API latency increased from

```
250 ms

↓

5 seconds
```

How do you identify the bottleneck?

Expected answer

- X-Ray
- Database
- External APIs
- CloudWatch

---

## Question 15

AWS bill suddenly doubles.

How do you investigate?

Possible causes

- Recursive invocation
- Logging
- Memory
- Retries
- Provisioned Concurrency

---

# Round 5 — Security

## Question 16

How do you secure Lambda?

Discuss

- IAM
- Secrets Manager
- KMS
- TLS
- CloudTrail

---

## Question 17

Why shouldn't AdministratorAccess be used?

---

## Question 18

How do you securely connect to Aurora?

Expected answer

```
Lambda

↓

Private Subnet

↓

RDS Proxy

↓

Aurora
```

---

## Question 19

Where should secrets be stored?

Expected answer

Secrets Manager.

Parameter Store.

Never inside source code.

---

# Round 6 — Performance

## Question 20

How do you optimize Lambda performance?

Discuss

- Memory
- CPU
- Cold Starts
- Package Size
- Parallel Processing
- Cache

---

## Question 21

Why can increasing memory reduce cost?

Interviewer expects explanation of

```
Memory

↓

CPU

↓

Duration

↓

Billing
```

---

## Question 22

How do you reduce cold starts?

---

## Question 23

How do you benchmark Lambda?

Expected discussion

- CloudWatch
- Lambda Power Tuning
- Load testing

---

# Round 7 — Deployment

## Question 24

How do you perform zero downtime deployment?

Expected answer

```
Version

↓

Alias

↓

Canary

↓

Monitor

↓

100%
```

---

## Question 25

Why shouldn't production use `$LATEST`?

---

## Question 26

Explain Lambda Versions.

---

# Round 8 — Observability

## Question 27

How do you debug production issues?

Expected tools

- CloudWatch Logs
- CloudWatch Metrics
- AWS X-Ray
- CloudTrail

---

## Question 28

Which CloudWatch metrics are most important?

Expected

- Errors
- Duration
- Invocations
- Throttles
- ConcurrentExecutions

---

## Question 29

What does X-Ray provide?

Expected discussion

- Tracing
- Latency
- Service Map
- Root Cause Analysis

---

# Round 9 — System Design

## Question 30

Design an event-driven order processing platform.

Possible architecture

```
API Gateway

↓

Lambda

↓

EventBridge

↓

SQS

↓

Worker Lambda

↓

SNS

↓

Email
```

---

## Question 31

Design a serverless payment platform.

Expected discussion

- Authentication
- Idempotency
- DLQ
- Monitoring
- Security
- Scaling

---

## Question 32

Design a multi-region serverless architecture.

Discuss

- Route 53
- Global Tables
- CloudFront
- Disaster Recovery

---

# Behavioral Questions

## Question 33

Tell me about a production outage you handled.

Interviewer evaluates

- Ownership
- Debugging
- Communication
- Resolution
- Lessons learned

---

## Question 34

Describe a difficult architectural decision.

---

## Question 35

Have you ever reduced cloud costs?

Discuss

- Optimization
- Benchmarking
- Monitoring
- Architectural improvements

---

# Rapid Fire Questions

- Maximum Lambda timeout?
- Maximum memory?
- What is a Cold Start?
- What is Provisioned Concurrency?
- Difference between Layer and Extension?
- What is Event Source Mapping?
- What is RDS Proxy?
- What is SnapStart?
- Difference between SNS and SQS?
- What is DLQ?
- What is Lambda Destination?
- When should you use ECS instead?

---

# Interview Tips

During interviews:

✅ Think before answering.

✅ Clarify requirements.

✅ Draw architecture diagrams.

✅ Discuss trade-offs.

✅ Mention security.

✅ Mention monitoring.

✅ Mention scaling.

✅ Explain production experience.

---

# Evaluation Criteria

Interviewers typically assess:

| Area | What They Evaluate |
|------|--------------------|
| Fundamentals | Core AWS Lambda knowledge |
| Architecture | System design and scalability |
| Security | IAM, encryption, networking |
| Performance | Optimization strategies |
| Operations | Monitoring and troubleshooting |
| Communication | Structured and concise explanations |
| Trade-offs | Ability to justify technical decisions |

---

# Sample Evaluation Rubric

| Skill | Rating (1–5) |
|--------|-------------:|
| Lambda Fundamentals | ⭐⭐⭐⭐⭐ |
| Event-Driven Design | ⭐⭐⭐⭐⭐ |
| Security | ⭐⭐⭐⭐⭐ |
| Scalability | ⭐⭐⭐⭐⭐ |
| Performance Optimization | ⭐⭐⭐⭐⭐ |
| Production Troubleshooting | ⭐⭐⭐⭐⭐ |
| System Design | ⭐⭐⭐⭐⭐ |
| Communication | ⭐⭐⭐⭐⭐ |

Aim to consistently score **4 or 5** across all categories for senior-level roles.

---

# Senior Backend Engineering Perspective

Senior interviews are less about memorizing AWS documentation and more about demonstrating engineering judgment. Interviewers expect candidates to explain **why** a particular solution was chosen, discuss trade-offs, and show an understanding of how systems behave in production.

Strong candidates connect Lambda concepts to broader topics such as distributed systems, microservices, reliability, observability, security, and cost optimization. They communicate clearly, reason systematically, and draw from real production experience when answering questions.

---

# Key Takeaways

- Senior Lambda interviews focus on architecture, production experience, and decision-making rather than simple definitions.
- Practice explaining concepts with diagrams, workflows, and trade-offs.
- Be prepared for scenario-based questions involving scalability, security, monitoring, and troubleshooting.
- Use a structured approach when answering: understand the problem, investigate, propose a solution, and discuss trade-offs.
- Confidence, clear communication, and practical engineering experience often distinguish senior candidates from intermediate ones.