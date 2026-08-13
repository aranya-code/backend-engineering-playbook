# CloudWatch Synthetics

CloudWatch Synthetics is a monitoring service that continuously tests your applications, APIs, and websites by simulating real user interactions. It uses **Canaries** to proactively detect availability, performance, and functionality issues before they impact customers.

Unlike CloudWatch Metrics, which monitor infrastructure, Synthetics monitors the **end-user experience**.

---

# What is CloudWatch Synthetics?

CloudWatch Synthetics allows you to create scripts, called **Canaries**, that periodically execute predefined tasks against your applications.

These canaries simulate user behavior such as:

- Opening a website
- Logging into an application
- Calling an API
- Clicking buttons
- Filling forms
- Navigating pages

This helps identify issues before real users experience them.

---

# Why Use CloudWatch Synthetics?

CloudWatch Synthetics helps you:

- Monitor application availability
- Validate API responses
- Detect broken links
- Measure page load times
- Identify performance degradation
- Verify business-critical workflows
- Improve customer experience

---

# What is a Canary?

A **Canary** is an automated script that performs scheduled tests against your application.

Each Canary:

- Runs on a schedule
- Executes predefined steps
- Collects metrics
- Captures logs
- Takes screenshots
- Generates reports

AWS executes Canaries using **AWS Lambda** behind the scenes.

---

# How CloudWatch Synthetics Works

```text
CloudWatch Synthetics
          |
          v
       Canary
          |
          v
Website / API / Application
          |
          v
Collect Results
          |
          +----------------------+
          |                      |
          v                      v
 CloudWatch Metrics      CloudWatch Logs
          |
          v
 CloudWatch Dashboard
          |
          v
 CloudWatch Alarm
```

---

# Types of Canaries

CloudWatch provides several Canary blueprints.

Common types include:

- Heartbeat Monitoring
- API Canary
- Broken Link Checker
- Visual Monitoring
- GUI Workflow
- Multi-step User Journey

Each blueprint is designed for a specific monitoring scenario.

---

# Heartbeat Monitoring

Heartbeat Canaries verify that an application or website is reachable.

Example:

```text
Every 5 Minutes

↓

GET https://example.com

↓

HTTP 200 OK

↓

Success
```

This is useful for availability monitoring.

---

# API Monitoring

Canaries can monitor REST APIs.

Example:

```text
GET /api/orders

↓

Response Time

↓

Status Code

↓

Response Validation
```

Useful for monitoring backend services.

---

# Broken Link Checker

This Canary crawls a website and identifies:

- Broken hyperlinks
- Missing pages
- Invalid redirects
- HTTP 404 errors

Ideal for documentation sites and public websites.

---

# Visual Monitoring

Visual Monitoring compares screenshots taken during each execution.

It can detect:

- Missing UI components
- Layout changes
- Broken images
- Rendering problems

Useful after application deployments.

---

# User Journey Monitoring

Canaries can simulate complete business workflows.

Example:

```text
Open Website

↓

Login

↓

Search Product

↓

Add to Cart

↓

Checkout

↓

Logout
```

This ensures critical business processes continue working correctly.

---

# Data Collected

Each Canary collects:

- Response Time
- Availability
- HTTP Status Code
- Error Messages
- Execution Logs
- Screenshots
- HAR Files (HTTP Archive)

All data is stored in CloudWatch for analysis.

---

# CloudWatch Integration

CloudWatch Synthetics integrates with:

- CloudWatch Metrics
- CloudWatch Logs
- CloudWatch Dashboards
- CloudWatch Alarms
- Amazon SNS
- AWS X-Ray

This provides end-to-end application monitoring.

---

# Real-World Example

A banking application has a critical online payment system.

A Canary runs every five minutes:

1. Opens the login page.
2. Logs into the application.
3. Transfers a small test payment.
4. Verifies the confirmation page.
5. Logs out.

If any step fails:

- The Canary fails.
- CloudWatch records the error.
- A CloudWatch Alarm enters the **ALARM** state.
- Amazon SNS notifies the operations team immediately.

This allows engineers to fix issues before customers report them.

---

# Benefits

- Proactive monitoring
- End-user experience validation
- Automatic screenshots
- Performance monitoring
- API testing
- Website monitoring
- Integration with CloudWatch
- Improved application reliability

---

# Best Practices

- Monitor all customer-facing applications.
- Create separate Canaries for critical business workflows.
- Run Canaries from multiple AWS Regions when monitoring global applications.
- Configure CloudWatch Alarms for failed Canary executions.
- Review screenshots after deployments.
- Store Canary artifacts securely in Amazon S3.

---

# Limitations

- Additional AWS charges apply for Canary executions.
- Frequent executions increase costs.
- Complex user journeys require more maintenance.
- Test credentials should be managed securely using AWS Secrets Manager.

---

# CloudWatch Synthetics vs CloudWatch Metrics

| CloudWatch Metrics | CloudWatch Synthetics |
|--------------------|----------------------|
| Monitors infrastructure | Monitors user experience |
| Resource health | Website and API health |
| Passive monitoring | Active monitoring |
| Collects metrics | Simulates user actions |

---

# Key Takeaways

- CloudWatch Synthetics proactively monitors applications using automated **Canaries**.
- Canaries simulate real user interactions with websites and APIs.
- They collect metrics, logs, screenshots, and performance data.
- CloudWatch Synthetics integrates with CloudWatch Metrics, Logs, Dashboards, Alarms, Amazon SNS, and AWS X-Ray.
- It is one of the best tools for ensuring application availability and validating critical business workflows before users encounter issues.