# README

## Overview

This directory contains automated tests for the Data Lake Storage and Lifecycle Automation project. The tests validate local data-quality rules, Athena analytics query definitions, and Terraform lifecycle configuration.

The test suite is designed to catch regressions before deploying infrastructure or running analytics workloads against AWS. It focuses on deterministic checks that can run locally without creating S3 buckets, provisioning Glue resources, or executing Athena queries.

The tests complement, rather than replace, integration tests against a deployed AWS environment.

## Test Coverage

| Test module | Responsibility | AWS required |
|---|---|---|
| `test_dataset_validation.py` | Validates event schema, required fields, data types, timestamps, partition dates, and dataset integrity | No |
| `test_analytics_queries.py` | Checks SQL examples, Glue table references, partition-filter usage, and compatibility with representative sample events | No |
| `test_lifecycle_configuration.py` | Checks Terraform lifecycle configuration, transition ordering, retention settings, and configuration guards | No |

### Dataset validation

`test_dataset_validation.py` exercises the dataset validator using the checked-in sample dataset and invalid input cases.

Coverage includes:

- Required event fields and field types.
- Unique event identifiers.
- ISO timestamp and date consistency.
- Numeric amount representation and currency codes.
- Attributes represented as JSON objects.
- Empty datasets and malformed records.
- Multiple validation errors in one batch.
- Protection against mutation of caller-owned input data.

### Analytics query validation

`test_analytics_queries.py` checks the SQL examples in `src/analytics/query_examples.sql` and the representative data in `data/samples/sample_events.json`.

Coverage includes:

- Presence of non-empty SQL statements.
- Query references to the configured project Glue database and events table.
- Explicit column selection instead of unrestricted `SELECT *`.
- References to expected event fields.
- Partition filtering using `event_date`.
- Absence of unexpected table dependencies.
- Sample data coverage for event types, tenants, dates, currencies, and amount values.

These are static SQL and fixture checks. They do not parse Athena SQL with the Athena engine, verify that Glue partitions exist, or execute queries against AWS. Successful local tests therefore do not prove that a deployed Athena query will run successfully.

### Lifecycle configuration validation

`test_lifecycle_configuration.py` checks the Terraform lifecycle resource and its associated configuration.

Coverage includes:

- Lifecycle configuration targeting the raw-data bucket.
- Lifecycle enablement and prefix filtering.
- Standard-IA and Glacier transition configuration.
- Optional object expiration and noncurrent-version expiration.
- Incomplete multipart upload cleanup.
- Versioning dependency and lifecycle preconditions.
- Variable defaults and validation constraints.
- Protection against unintended lifecycle scope.

These checks inspect Terraform source. They do not apply the configuration or verify actual object transitions in S3.

## Project Dependencies

The test suite uses Python's standard library and `pytest`.

Install the test dependency in the project's active virtual environment:

```bash
python -m pip install pytest
```

The tests import project modules using the `src` package path. Run commands from the project root so that the repository root is available on Python's import path.

No AWS access keys or long-lived credentials are required for these local tests.

## Running the Tests

Run the complete test suite from the project root:

```bash
python -m pytest tests/ -v
```

Run an individual test module:

```bash
python -m pytest tests/test_dataset_validation.py -v
python -m pytest tests/test_analytics_queries.py -v
python -m pytest tests/test_lifecycle_configuration.py -v
```

Run a specific test by name:

```bash
python -m pytest tests/test_analytics_queries.py \
  -k partition_column \
  -v
```

Run with short tracebacks and a concise summary:

```bash
python -m pytest tests/ -ra
```

For CI pipelines, use a non-zero exit code on any test failure:

```bash
python -m pytest tests/ -q
```

`pytest` returns a non-zero exit status when tests fail or collection encounters an error, making it suitable for a GitHub Actions validation job.

## Expected Test Inputs

The tests depend on files already maintained by the project:

| Input | Purpose |
|---|---|
| `data/samples/sample_events.json` | Representative event records used by dataset and analytics tests |
| `src/ingestion/validate_dataset.py` | Dataset validation implementation |
| `src/analytics/query_examples.sql` | Athena SQL examples checked by analytics tests |
| `infrastructure/terraform/lifecycle.tf` | S3 lifecycle resource definition |
| `infrastructure/terraform/variables.tf` | Lifecycle and versioning variable declarations |

Keep these files consistent when changing the event schema, Glue table, SQL examples, or lifecycle configuration.

## Test Design and Limitations

### Deterministic local tests

The suite deliberately avoids AWS API calls. This keeps routine validation fast, repeatable, and independent of account permissions, Region availability, network connectivity, and AWS service charges.

The tests validate local contracts, not deployed behavior.

### Athena query verification

Static SQL assertions can detect missing table references, unexpected dependencies, and absent partition filters. They cannot validate all Athena syntax, Glue type compatibility, SerDe behavior, partition registration, encryption permissions, or query execution semantics.

For deployment-level verification:

1. Deploy the S3 buckets, Glue catalog, and Athena workgroup.
2. Upload the sample dataset using the project's ingestion workflow.
3. Ensure the Glue table and required partitions describe the uploaded data.
4. Execute representative SQL statements through Athena.
5. Validate query execution status, result schema, and returned records.
6. Confirm query results are written to the configured encrypted analytics location.

Athena execution incurs charges based on the amount of data scanned, subject to workgroup configuration and applicable pricing. Use partition predicates and the configured bytes-scanned cutoff to control query cost.

### Terraform lifecycle verification

Static Terraform tests do not replace Terraform validation or an AWS lifecycle integration test.

Run Terraform formatting and validation from the Terraform directory:

```bash
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

A real lifecycle transition requires deployed resources and elapsed time. Validate it using S3 object metadata, storage-class inspection, and lifecycle configuration APIs rather than assuming that a successful Terraform apply proves that an object has transitioned.

### Test isolation

Tests should not depend on:

- A deployed AWS account.
- Local AWS credential files.
- A particular AWS Region.
- Previously generated Athena query results.
- Existing S3 objects or Glue partitions.
- Test execution order.

Use temporary fixtures and independent test data when extending the suite. Avoid modifying the checked-in sample dataset from a test.

## Extending the Test Suite

When adding coverage, keep tests focused on one contract and place them in the module responsible for that behavior.

Recommended additions include:

- Analytics result validation for expected columns, row counts, and aggregate values.
- SQL regression tests for tenant filters and date-range boundaries.
- Tests for malformed or missing Athena result fields.
- Lifecycle configuration tests for disabled versioning and disabled expiration.
- Integration tests that execute Athena queries in an explicitly configured AWS test environment.
- Verification of S3 object storage class and version metadata after lifecycle transitions.

AWS integration tests should be clearly separated from local unit tests. They should use a dedicated test environment, least-privilege IAM permissions, explicit resource ownership, bounded execution time, and cleanup procedures.

Never make destructive cleanup operations target a shared or production bucket.

## Key Takeaways

- Run the local `pytest` suite before changing ingestion, analytics, or lifecycle code.
- Static analytics tests validate SQL structure, not successful Athena execution.
- Terraform source tests do not prove that S3 lifecycle transitions occurred.
- Keep sample data, Glue schema, SQL examples, and validator behavior aligned.
- Use isolated AWS integration tests to verify deployed behavior without risking production resources.