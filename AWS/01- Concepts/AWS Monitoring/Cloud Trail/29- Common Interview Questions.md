# Common Interview Questions

AWS CloudTrail is a common topic in interviews for AWS Solutions Architects, DevOps Engineers, Cloud Engineers, Security Engineers, and Site Reliability Engineers (SREs).

This chapter covers frequently asked interview questions along with concise answers.

------------------------------------------------------------------------

# Beginner Questions

## 1. What is AWS CloudTrail?

**Answer**

AWS CloudTrail is a managed service that records AWS API activity for governance, compliance, auditing, and operational troubleshooting.

---

## 2. What does CloudTrail record?

**Answer**

CloudTrail records supported AWS API calls made by:

- IAM Users
- IAM Roles
- AWS Services
- AWS CLI
- AWS SDKs
- AWS Management Console

---

## 3. What is an Event?

**Answer**

An Event represents a single AWS API call recorded by CloudTrail.

---

## 4. What is a Trail?

**Answer**

A Trail continuously records CloudTrail events and delivers them to destinations such as Amazon S3 and CloudWatch Logs.

---

## 5. What is Event History?

**Answer**

Event History stores Management Events for the previous 90 days without requiring a Trail.

------------------------------------------------------------------------

# Intermediate Questions

## 6. What are the three CloudTrail event types?

**Answer**

- Management Events
- Data Events
- Network Activity Events

---

## 7. What are Data Events?

**Answer**

Data Events record operations performed on the data inside AWS resources, such as S3 object uploads and Lambda invocations.

---

## 8. What is CloudTrail Insights?

**Answer**

CloudTrail Insights detects unusual Write Management API activity by comparing current behavior with historical baselines.

---

## 9. Why store CloudTrail logs in Amazon S3?

**Answer**

Amazon S3 provides durable, scalable, and cost-effective long-term storage for CloudTrail logs.

---

## 10. How does CloudTrail integrate with CloudWatch?

**Answer**

CloudTrail sends logs to CloudWatch Logs, where Metric Filters and Alarms can monitor sensitive API activity.

------------------------------------------------------------------------

# Advanced Questions

## 11. What is Log File Integrity Validation?

**Answer**

It uses cryptographic digest files to verify that CloudTrail log files have not been modified or deleted.

---

## 12. What is an Organization Trail?

**Answer**

An Organization Trail records CloudTrail events from every AWS account within an AWS Organization.

---

## 13. What is the difference between Event History and Trails?

| Event History | Trail |
|---------------|-------|
| 90 days | Long-term retention |
| Management Events only | Configurable event types |
| No setup | Requires configuration |

---

## 14. How would you detect unauthorized IAM changes?

**Answer**

Use:

- CloudTrail
- CloudWatch Metric Filters
- CloudWatch Alarms
- Amazon SNS
- EventBridge

---

## 15. What is the difference between CloudTrail and CloudWatch?

**Answer**

CloudTrail audits AWS API activity, while CloudWatch monitors infrastructure and application performance.

------------------------------------------------------------------------

# Scenario-Based Questions

## Scenario 1

Someone accidentally deletes an S3 bucket.

How would you determine who performed the action?

**Answer**

Search CloudTrail for the **DeleteBucket** event and review:

- IAM User
- Timestamp
- Source IP
- AWS Region

---

## Scenario 2

CloudTrail logs are missing from Amazon S3.

What would you check?

**Answer**

- Trail status
- Bucket policy
- IAM permissions
- S3 bucket configuration

---

## Scenario 3

A company needs centralized logging across 50 AWS accounts.

What would you recommend?

**Answer**

Use:

- AWS Organizations
- Organization Trail
- Central Amazon S3 Bucket

---

## Scenario 4

How would you automatically respond when an IAM user is created?

**Answer**

CloudTrail → EventBridge → Lambda → SNS Notification

------------------------------------------------------------------------

# Interview Tips

Remember:

- **CloudTrail = Audit**
- **CloudWatch = Monitor**
- **X-Ray = Trace**

Also remember:

- Event History = 90 Days
- Trails = Long-term Logging
- Data Events = Disabled by Default
- Insights = Detect Anomalies

------------------------------------------------------------------------

# Key Takeaways

- Learn CloudTrail architecture.
- Understand Management vs Data Events.
- Know how CloudTrail integrates with CloudWatch, EventBridge, and Organizations.
- Be prepared for troubleshooting and architecture questions.