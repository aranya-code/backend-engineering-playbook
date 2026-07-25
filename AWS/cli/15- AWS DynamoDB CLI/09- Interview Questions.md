# 09 - Interview Questions

## Overview

Although most application development is performed using AWS SDKs like Boto3, the AWS CLI remains an essential tool for backend engineers, DevOps engineers, SREs, and cloud engineers.

Interviewers often ask AWS CLI questions to evaluate whether a candidate understands:

- Production troubleshooting
- Infrastructure automation
- CI/CD workflows
- Disaster recovery
- DynamoDB administration
- Operational best practices

This chapter contains senior-level interview questions with detailed answers.

---

# Basic Questions

---

## 1. What is the AWS CLI?

**Answer**

AWS CLI (Command Line Interface) is a command-line tool that allows users to interact with AWS services by sending authenticated API requests.

It provides access to almost every AWS service, including DynamoDB.

Example:

```bash
aws dynamodb list-tables
```

---

## 2. Why use the AWS CLI instead of the AWS Console?

**Answer**

The CLI is preferred for:

- Automation
- CI/CD
- Scripting
- Infrastructure validation
- Operational tasks
- Faster debugging

The Console is better suited for visualization and exploration.

---

## 3. Why use Boto3 instead of the CLI?

**Answer**

Boto3 is used inside Python applications.

The CLI is used outside applications for:

- Administration
- Automation
- Infrastructure management
- Operational support

---

## 4. Can every DynamoDB operation be performed using the CLI?

**Answer**

Yes.

The AWS CLI exposes nearly every DynamoDB API operation.

---

## 5. Where are AWS CLI credentials stored?

**Answer**

Typically:

```text
~/.aws/config

~/.aws/credentials
```

Production systems should prefer IAM Roles instead of static credentials.

---

# CRUD Questions

---

## 6. Which CLI command inserts an item?

**Answer**

```bash
aws dynamodb put-item
```

---

## 7. Which command retrieves one item?

**Answer**

```bash
aws dynamodb get-item
```

---

## 8. What is the difference between `put-item` and `update-item`?

**Answer**

`put-item`

- Creates a new item
- Completely replaces an existing item having the same primary key

`update-item`

- Updates only specified attributes
- Leaves remaining attributes unchanged

---

## 9. How do you prevent duplicate inserts?

**Answer**

Use a condition expression.

Example:

```text
attribute_not_exists(order_id)
```

This makes writes idempotent.

---

## 10. Why use JSON files instead of inline JSON?

**Answer**

Advantages:

- Easier maintenance
- Cleaner scripts
- Version control
- Reusability
- Fewer syntax errors

---

# Query Questions

---

## 11. What is the difference between Query and Scan?

**Answer**

| Query | Scan |
|--------|------|
| Requires partition key | Reads entire table |
| Fast | Slow |
| Low cost | Expensive |
| Production APIs | Administrative jobs |

---

## 12. Why should Scan be avoided?

**Answer**

Because Scan reads every item in the table.

Large production tables may contain millions of items.

---

## 13. Does Filter Expression reduce read capacity?

**Answer**

No.

Filtering occurs **after** DynamoDB has read the matching items.

Read capacity consumption remains unchanged.

---

## 14. Why use Projection Expressions?

**Answer**

To return only required attributes.

Benefits:

- Smaller responses
- Lower network traffic
- Better performance

---

## 15. What is `LastEvaluatedKey`?

**Answer**

It indicates there are additional results available.

Use it with:

```text
ExclusiveStartKey
```

to retrieve the next page.

---

# Table Management Questions

---

## 16. How do you verify that a table exists?

**Answer**

```bash
aws dynamodb describe-table \
    --table-name Orders
```

---

## 17. Why use `aws dynamodb wait table-exists`?

**Answer**

Because table creation is asynchronous.

The wait command blocks until the table becomes:

```text
ACTIVE
```

---

## 18. What billing modes are available?

**Answer**

Two:

- PAY_PER_REQUEST
- PROVISIONED

---

## 19. Which billing mode should startups typically use?

**Answer**

Usually:

```text
PAY_PER_REQUEST
```

because it automatically scales without capacity planning.

---

## 20. Why enable Time To Live?

**Answer**

TTL automatically removes expired data.

Typical use cases:

- Sessions
- OTPs
- Cache
- Temporary tokens

---

# Backup Questions

---

## 21. What is Point-in-Time Recovery?

**Answer**

Continuous backups that allow restoring a table to any second within the recovery window.

---

## 22. Does restoring overwrite the original table?

**Answer**

No.

Restores always create a **new table**.

---

## 23. Why create manual backups if PITR is enabled?

**Answer**

Manual backups provide a known recovery point before deployments, migrations, or maintenance activities.

---

## 24. When would you export a table instead of creating a backup?

**Answer**

Exports are intended for:

- Analytics
- Data lakes
- Long-term archival
- Data migration

Backups are intended for disaster recovery.

---

# Monitoring Questions

---

## 25. Which CLI command is most useful for troubleshooting?

**Answer**

```bash
aws dynamodb describe-table
```

It provides:

- Status
- Capacity
- Indexes
- Billing mode
- Streams
- Encryption
- Metadata

---

## 26. How do you check if TTL is enabled?

**Answer**

```bash
aws dynamodb describe-time-to-live
```

---

## 27. How do you check if PITR is enabled?

**Answer**

```bash
aws dynamodb describe-continuous-backups
```

---

## 28. How do you troubleshoot authentication issues?

**Answer**

Use:

```bash
--debug
```

This displays:

- Request signing
- Credentials
- Retries
- HTTP requests
- HTTP responses

---

# Automation Questions

---

## 29. Why is the AWS CLI commonly used in CI/CD?

**Answer**

Because it provides a consistent interface for:

- Infrastructure provisioning
- Validation
- Health checks
- Backups
- Deployments
- Rollbacks

---

## 30. Why should automation use exit codes?

**Answer**

Exit codes allow scripts to detect failures and stop, retry, or trigger alerts instead of continuing with inconsistent operations.

---

## 31. Why should scripts use environment variables?

**Answer**

Environment variables improve portability across development, staging, and production environments while reducing hardcoded configuration.

---

# Scenario-Based Questions

---

## 32. Your deployment failed because the table does not exist. What would you check first?

**Answer**

- Correct AWS Profile
- Correct Region
- Table Name
- IAM Permissions
- `describe-table` output
- Infrastructure deployment logs

---

## 33. Your API suddenly becomes slow. What would you investigate?

**Answer**

- CloudWatch metrics
- Throttling
- Read/Write Capacity
- Billing mode
- Hot partitions
- GSI usage
- Application logs

---

## 34. Production data was accidentally deleted. What would you do?

**Answer**

1. Stop further writes.
2. Verify PITR or available backups.
3. Restore to a new table.
4. Validate the restored data.
5. Redirect traffic after verification.

---

## 35. A deployment introduced corrupted data. How would you recover?

**Answer**

- Restore from the pre-deployment backup or PITR.
- Compare restored and current data.
- Validate application behavior.
- Perform a controlled cutover.

---

## 36. How would you verify that Infrastructure as Code created a table correctly?

**Answer**

Run:

```bash
aws dynamodb describe-table
```

Then verify:

- Table status
- Billing mode
- Keys
- GSIs
- Streams
- TTL
- PITR

---

## 37. A GSI query suddenly starts failing after deployment. What would you investigate?

**Answer**

- Verify the GSI exists.
- Check the index status (`ACTIVE`).
- Confirm the index name used in the query.
- Validate IAM permissions.
- Review deployment logs for index creation.

---

## 38. You notice frequent `ProvisionedThroughputExceededException` errors. What steps would you take?

**Answer**

- Check CloudWatch throttling metrics.
- Review read/write capacity.
- Look for hot partitions.
- Enable Auto Scaling or switch to On-Demand mode if appropriate.
- Re-evaluate the table's partition key design.

---

## 39. How would you automate nightly backups for all production tables?

**Answer**

Use a scheduled script (Cron, EventBridge Scheduler, or GitHub Actions) that:

1. Lists production tables.
2. Creates timestamped backups.
3. Logs success or failure.
4. Sends alerts if any backup operation fails.

---

## 40. How would you build a production health check using the CLI?

**Answer**

A health check should verify:

- Table status is `ACTIVE`.
- TTL is enabled.
- PITR is enabled.
- Streams are configured (if required).
- GSIs are `ACTIVE`.
- Recent CloudWatch alarms are clear.

This can be integrated into deployment pipelines or operational dashboards.

---

# Rapid Fire Questions

| Question | Answer |
|-----------|--------|
| Command to list tables? | `list-tables` |
| Insert item? | `put-item` |
| Read item? | `get-item` |
| Update item? | `update-item` |
| Delete item? | `delete-item` |
| Query data? | `query` |
| Read entire table? | `scan` |
| Create backup? | `create-backup` |
| Restore backup? | `restore-table-from-backup` |
| Export table? | `export-table-to-point-in-time` |
| Import table? | `import-table` |
| Describe table? | `describe-table` |
| Enable TTL? | `update-time-to-live` |
| Check TTL? | `describe-time-to-live` |
| Enable PITR? | `update-continuous-backups` |
| Check limits? | `describe-limits` |
| Wait for table creation? | `wait table-exists` |
| Debug requests? | `--debug` |

---

# Senior-Level Tips

Experienced backend engineers should be comfortable with:

- Automating DynamoDB administration using shell scripts.
- Using the CLI within CI/CD pipelines.
- Diagnosing production issues with `describe-table` and `--debug`.
- Managing backups and disaster recovery.
- Validating infrastructure after deployment.
- Combining CloudWatch monitoring with CLI-based troubleshooting.
- Writing reusable operational runbooks.

---

# Key Takeaways

- The AWS CLI is a critical operational tool for managing DynamoDB in production.
- Interview questions often focus on automation, troubleshooting, disaster recovery, and operational best practices rather than simple command syntax.
- Senior engineers should understand not only **how** to execute CLI commands but also **when** and **why** to use them in real-world scenarios.
- Strong CLI knowledge complements SDK expertise and is essential for CI/CD, DevOps, and cloud-native backend development.
```