# 15 - Unit Testing DynamoDB Code

## Overview

Writing production code without tests is risky.

When working with DynamoDB, testing becomes even more important because your application depends on an external cloud service.

However, **unit tests should never call the real AWS environment**.

Instead, they should:

- Mock DynamoDB
- Test business logic
- Verify repository behavior
- Validate error handling
- Run quickly
- Be deterministic

Production teams typically divide testing into three layers:

- Unit Tests
- Integration Tests
- End-to-End Tests

Each serves a different purpose.

---

# Learning Objectives

After completing this chapter, you'll understand:

- Testing Pyramid
- Unit vs Integration Tests
- Mocking Boto3
- Mocking Repositories
- Using unittest.mock
- Using pytest
- Testing FastAPI Services
- Testing Repository Classes
- Testing Exceptions
- Testing Retries
- Production testing strategies
- Best practices

---

# Why Test?

Suppose a developer accidentally changes:

```python
status = "PAID"
```

to

```python
status = "FAILED"
```

Without tests:

```text
Deploy

↓

Production Bug
```

With tests:

```text
Run Tests

↓

Failure

↓

Fix

↓

Deploy
```

Tests reduce production incidents.

---

# Testing Pyramid

```text
           E2E Tests

         Integration Tests

            Unit Tests
```

Most tests should be unit tests.

---

# Unit Test

A unit test verifies one small piece of logic.

Example:

```text
OrderService

↓

Mock Repository

↓

Assertions
```

No AWS resources are involved.

---

# Integration Test

Integration tests verify that code works with DynamoDB.

```text
Repository

↓

DynamoDB Local

↓

Assertions
```

---

# End-to-End Test

```text
Client

↓

API

↓

Service

↓

Repository

↓

AWS DynamoDB
```

These tests are slower and fewer in number.

---

# Recommended Testing Strategy

| Test Type | Uses AWS? | Fast? |
|------------|-----------|--------|
| Unit | ❌ | ✅ |
| Integration | DynamoDB Local | Moderate |
| End-to-End | AWS | Slow |

---

# Project Structure

```text
project/

├── app/

└── tests/

    ├── unit/

    ├── integration/

    └── e2e/
```

---

# Testing Repository Layer

Suppose:

```python
repository.save(order)
```

Unit tests should verify:

- Correct parameters
- Correct exception handling
- Correct return values

without contacting AWS.

---

# Mocking with unittest.mock

Python provides:

```python
from unittest.mock import Mock
```

Example:

```python
mock_table = Mock()

mock_table.put_item.return_value = {}
```

The repository receives the mock instead of a real table.

---

# Repository Unit Test

```python
def test_save_order():

    table = Mock()

    repository = OrderRepository(table)

    repository.save({
        "order_id": "1001"
    })

    table.put_item.assert_called_once()
```

No network calls occur.

---

# Testing the Service Layer

```text
Service

↓

Mock Repository

↓

Assertions
```

Example:

```python
repository = Mock()

service = OrderService(repository)

service.create(order)

repository.save.assert_called_once()
```

The service is tested independently.

---

# Testing Business Logic

Example:

```python
def test_discount():

    service.calculate_discount(...)
```

The repository should not participate unless required.

---

# Testing Exceptions

Example:

```python
from botocore.exceptions import ClientError
```

Configure the mock:

```python
table.put_item.side_effect = ClientError(...)
```

Verify:

```text
Repository

↓

Exception

↓

Translated Exception
```

---

# Testing Conditional Writes

Scenario:

```text
Duplicate Order

↓

Conditional Failure

↓

Business Exception
```

Your test should verify:

- Correct exception type
- Correct error message
- No unexpected behavior

---

# Testing Retries

Example:

```text
Failure

↓

Retry

↓

Success
```

Mock sequence:

```text
Exception

↓

Exception

↓

Success
```

Verify:

- Retry count
- Delay logic (often mocked)
- Final result

---

# Testing Pagination

Repository method:

```python
repository.list_orders(...)
```

Mock response:

```python
Items

LastEvaluatedKey
```

Verify:

```text
Multiple Pages

↓

Single Result
```

---

# Testing Transactions

Mock:

```python
transact_write_items()
```

Verify:

- Correct transaction items
- Rollback behavior
- Exception handling

---

# Testing Logging

Repository logs:

```text
PUT

↓

Duration

↓

Success
```

Mock the logger.

Verify:

- Log called
- Correct message
- Correct level

---

# Testing Metrics

Metrics wrapper:

```text
Repository

↓

Metrics

↓

CloudWatch
```

Mock metrics.

Verify:

- Counter increments
- Latency recorded
- Failure metrics

---

# Testing with pytest

Example:

```python
def test_get_order():

    repository = Mock()

    service = OrderService(repository)

    service.get("100")

    repository.get.assert_called_once()
```

Pytest keeps tests concise and readable.

---

# Fixtures

Pytest fixtures remove duplication.

Example:

```python
import pytest

@pytest.fixture
def repository():

    return Mock()
```

Reusable across multiple tests.

---

# Mocking Time

Retries often involve:

```python
time.sleep()
```

Mock it.

```text
Retry

↓

No Actual Delay
```

Tests remain fast.

---

# Mocking UUIDs

Instead of:

```python
uuid.uuid4()
```

Return:

```text
fixed-id
```

Assertions become deterministic.

---

# Mocking Dates

Instead of:

```python
datetime.utcnow()
```

Return:

```text
2026-01-01
```

Predictable timestamps simplify testing.

---

# Code Coverage

Production teams typically measure:

- Statement coverage
- Branch coverage
- Exception paths

Coverage helps identify untested code but should not replace thoughtful test design.

---

# CI/CD Testing

Typical workflow:

```text
Git Push

↓

GitHub Actions

↓

Run Tests

↓

Pass

↓

Deploy
```

Failed tests stop deployments.

---

# Production Architecture

```text
             GitHub Actions

                    │

                    ▼

              Unit Tests

                    │

                    ▼

          Integration Tests

                    │

                    ▼

          Build Docker Image

                    │

                    ▼

               Deployment
```

---

# Performance Considerations

Good unit tests should:

- Finish within seconds
- Run in parallel
- Require no network
- Avoid unnecessary setup
- Produce deterministic results

---

# Security Best Practices

- Never use production AWS credentials.
- Never test against production tables.
- Store test credentials separately.
- Use mock data instead of sensitive customer information.
- Sanitize logs generated during tests.

---

# Best Practices

- Write unit tests for business logic.
- Mock DynamoDB in unit tests.
- Use DynamoDB Local for integration tests.
- Keep tests isolated.
- Make tests deterministic.
- Test failure scenarios as thoroughly as success cases.
- Automate test execution in CI/CD.

---

# Common Mistakes

## Calling Real AWS in Unit Tests

Poor:

```text
Unit Test

↓

AWS DynamoDB
```

Better:

```text
Unit Test

↓

Mock
```

---

## Ignoring Failure Cases

Only testing successful requests leaves error handling unverified.

Test:

- Throttling
- Validation failures
- Conditional failures
- Transactions
- Retries

---

## Sharing State Between Tests

Each test should create its own data.

Avoid hidden dependencies between test cases.

---

## Sleeping During Retry Tests

Mock delays instead of waiting.

This keeps the test suite fast.

---

# Interview Notes

A common interview question is:

> **Why shouldn't unit tests call DynamoDB?**

Unit tests should be fast, deterministic, and independent of external systems. Calling DynamoDB introduces network latency, credentials, infrastructure dependencies, and potential costs.

---

Another common question is:

> **How do you test a DynamoDB repository?**

Inject mocked Boto3 resources or tables into the repository and verify method calls, parameters, return values, and exception handling without making real AWS requests.

---

Another common question is:

> **When should you use DynamoDB Local?**

Use DynamoDB Local for integration testing to validate repository behavior against a real DynamoDB-compatible implementation without requiring AWS resources.

---

Another common question is:

> **Why are mocks important in unit testing?**

Mocks isolate the component being tested, allowing developers to verify behavior without depending on external services, making tests faster and more reliable.

---

# Key Takeaways

- Unit tests should never communicate with real AWS services.
- Mock Boto3 resources, repositories, loggers, metrics, and time-dependent functions to create deterministic tests.
- Use DynamoDB Local for integration testing and reserve real AWS testing for end-to-end validation.
- Automate testing in CI/CD pipelines to prevent regressions before deployment.
- A comprehensive testing strategy covering success, failure, retries, pagination, and transactions is essential for production-grade DynamoDB applications.