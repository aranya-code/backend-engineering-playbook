# README.md

## Overview

This directory contains the automated test suite for the **MongoDB Background Worker Integration** project.

The tests focus on the worker's service-layer behavior, MongoDB persistence boundaries, job validation, retry-safe result persistence, and failure handling. The suite is intentionally separated from infrastructure and worker-loop tests so that business processing behavior can be verified independently.

The project follows a layered design:

```mermaid
flowchart TD
    Worker["Background Worker"] --> Service["ProcessingService"]
    Service --> Validate["Job Validation"]
    Service --> Execute["Job Execution"]
    Service --> Results["MongoDB Results Collection"]
    Worker --> Jobs["MongoDB Jobs Collection"]
    Results --> MongoDB["MongoDB"]
    Jobs --> MongoDB
```

The test suite should verify application behavior rather than reproduce MongoDB internals. MongoDB integration behavior that cannot be meaningfully represented with mocks should be covered by dedicated integration tests.

## Test Scope

The tests in this directory cover:

| Area | Purpose |
|---|---|
| Service initialization | Verify MongoDB collections are resolved correctly |
| Job validation | Reject malformed or incomplete jobs |
| Job execution | Verify valid payloads are processed |
| Result persistence | Verify results use idempotent upsert semantics |
| Error handling | Verify unexpected failures become domain-level errors |
| MongoDB failures | Verify database errors are propagated with context |
| Timestamp handling | Verify processing timestamps are timezone-aware |
| Input integrity | Verify processing does not unexpectedly mutate jobs |
| Execution isolation | Verify failed execution does not persist a successful result |

## Test Files

| File | Responsibility |
|---|---|
| `test_processing_service.py` | Tests `ProcessingService` validation, execution, persistence, and error handling |
| `test_tasks.py` | Tests worker task functions, job claiming, retries, and worker-loop behavior |
| `.env.example` | Documents environment variables used by the test environment |
| `requirements.txt` | Test dependencies |
| `.gitignore` | Excludes local environments, caches, secrets, and runtime artifacts |

## Testing Strategy

The suite uses a layered testing approach.

### Unit Tests

Unit tests isolate the application logic from MongoDB infrastructure by replacing database objects with mocks.

This makes tests:

- Fast
- Deterministic
- Easy to run locally
- Suitable for CI/CD
- Focused on application behavior

The service tests mock the MongoDB database and collections while still asserting the exact filters, update documents, and MongoDB operation options passed to PyMongo.

### Integration Tests

Integration tests should use a real MongoDB instance when validating behavior that depends on MongoDB itself.

Examples include:

- Unique indexes
- Query planner behavior
- Transaction semantics
- Write concerns
- Change streams
- Schema validation
- MongoDB-specific operators
- Replica-set behavior

A unit test should not attempt to prove that MongoDB correctly executes an update operator. It should prove that the application constructs and invokes the operation correctly.

## Processing Service Test Flow

The expected service flow is:

```mermaid
sequenceDiagram
    participant Test
    participant Service as ProcessingService
    participant Mongo as MongoDB

    Test->>Service: process(job)
    Service->>Service: Validate job
    Service->>Service: Execute workload
    Service->>Mongo: update_one(..., upsert=True)
    Mongo-->>Service: Write result
    Service-->>Test: Processing result
```

For an invalid job:

```mermaid
sequenceDiagram
    participant Test
    participant Service as ProcessingService
    participant Mongo as MongoDB

    Test->>Service: process(invalid_job)
    Service->>Service: Validate job
    Service-->>Test: InvalidJobError
    Note over Mongo: No result should be persisted
```

For an execution failure:

```mermaid
sequenceDiagram
    participant Test
    participant Service as ProcessingService
    participant Mongo as MongoDB

    Test->>Service: process(job)
    Service->>Service: Validate job
    Service->>Service: Execute workload
    Service-->>Service: ExecutionError
    Service-->>Test: ProcessingError
    Note over Mongo: Successful result must not be persisted
```

## Running the Tests

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

Install test dependencies:

```bash
pip install -r requirements.txt
```

Run the complete test suite:

```bash
pytest
```

Run the service tests only:

```bash
pytest tests/test_processing_service.py
```

Run the worker task tests:

```bash
pytest tests/test_tasks.py
```

Run with verbose output:

```bash
pytest -v
```

Run a specific test:

```bash
pytest tests/test_processing_service.py::test_process_persists_result -v
```

## Python Import Configuration

The source directory is expected to be importable when running tests.

From the project root, the recommended layout is:

```text
12- Projects/
    11- MongoDB Background Worker Integration/
        src/
            config/
            database/
            services/
            workers/
        tests/
            test_processing_service.py
            test_tasks.py
```

If the project is not installed as a package, configure `PYTHONPATH` appropriately for local execution or CI.

PowerShell:

```powershell
$env:PYTHONPATH="src"
pytest
```

Linux/macOS:

```bash
PYTHONPATH=src pytest
```

A production project should preferably package the application rather than relying on ad-hoc import-path manipulation.

## Test Fixtures

The service tests use mocked MongoDB objects.

A typical fixture hierarchy is:

```text
database
├── jobs collection
└── job_results collection
        │
        └── ProcessingService
```

The mocked database maps collection names to mock collections:

```python
database.__getitem__.side_effect = {
    "jobs": jobs_collection,
    "job_results": results_collection,
}.get
```

This allows the service to execute its normal collection lookup logic without requiring a running MongoDB instance.

## What the Processing Service Tests Verify

### Valid Job Processing

A valid job must contain:

- `_id`
- `payload`
- A dictionary payload

The test verifies that processing returns:

```python
{
    "status": "processed",
    "payload": {...},
    "processed_at": datetime(...),
}
```

The exact business workload is intentionally represented by the service's execution boundary.

### Job Validation

Invalid inputs should fail before MongoDB persistence occurs.

Examples:

| Input | Expected result |
|---|---|
| Empty job | `InvalidJobError` |
| Missing `_id` | `InvalidJobError` |
| Missing payload | `InvalidJobError` |
| `None` payload | `InvalidJobError` |
| String payload | `InvalidJobError` |
| List payload | `InvalidJobError` |
| Numeric payload | `InvalidJobError` |

This protects the persistence layer from malformed application state.

## Result Persistence

The service persists results using an upsert keyed by the job identifier:

```python
results.update_one(
    {"job_id": job_id},
    {
        "$set": {
            "result": result,
            "updated_at": datetime.now(timezone.utc),
        },
        "$setOnInsert": {
            "job_id": job_id,
            "created_at": datetime.now(timezone.utc),
        },
    },
    upsert=True,
)
```

The important property is that `job_id` becomes the persistence identity.

This is preferable to blindly calling `insert_one()` for a background job because workers may retry the same job.

Without an idempotent persistence strategy:

```text
Job execution
    ↓
Result inserted
    ↓
Worker crashes
    ↓
Job retried
    ↓
Result inserted again
    ↓
Duplicate result
```

With an upsert keyed by `job_id`:

```text
Job execution
    ↓
Result upserted
    ↓
Worker crashes
    ↓
Job retried
    ↓
Same job_id
    ↓
Existing result updated
```

An upsert alone does not automatically make the entire job workflow exactly-once. The complete workflow must still consider job claiming, retries, side effects, and transaction boundaries.

## MongoDB Mocking Boundaries

Mocks should be used to verify the application's interaction with PyMongo.

Good assertions include:

```python
results_collection.update_one.assert_called_once()
```

and:

```python
filter_document = (
    results_collection.update_one.call_args.args[0]
)

assert filter_document == {"job_id": "job-001"}
```

The test can also verify:

- MongoDB filters
- Update operators
- `upsert=True`
- Collection selection
- Number of database calls
- Whether persistence occurred after successful processing

Avoid testing PyMongo itself.

For example, this does not add meaningful value:

```python
assert isinstance(results_collection, MagicMock)
```

The important assertion is what the application asked MongoDB to do.

## Error Handling Tests

The service distinguishes expected domain errors from unexpected infrastructure or execution failures.

Expected validation failures:

```text
Invalid input
    ↓
InvalidJobError
```

Unexpected processing failures:

```text
Execution failure
    ↓
ProcessingError
    ↓
Original exception preserved as __cause__
```

The tests verify exception chaining:

```python
with pytest.raises(
    ProcessingError,
    match="Failed to process job 'job-001'",
) as exc_info:
    service.process(job)

assert exc_info.value.__cause__ is original_error
```

Exception chaining is important because the service can expose a stable application-level error while preserving the underlying failure for debugging and logging.

## MongoDB Failure Handling

MongoDB failures should not be silently swallowed.

For example:

```python
results_collection.update_one.side_effect = (
    PyMongoError("MongoDB unavailable")
)
```

The service should convert the infrastructure failure into an appropriate application-level error while preserving the original exception.

Production systems should also classify failures where appropriate:

| Failure | Typical handling |
|---|---|
| Validation error | Do not retry |
| Duplicate-key error | Usually handle according to idempotency semantics |
| Transient network failure | Potentially retry |
| Server selection timeout | Retry or fail depending on workload |
| Authentication failure | Fail fast and alert |
| Authorization failure | Fail fast and alert |
| Permanent application error | Do not blindly retry |

Retry policy belongs at the appropriate infrastructure or worker boundary. A service should not blindly retry every exception.

## Timestamp Testing

Background jobs should generally use timezone-aware UTC timestamps.

The tests verify:

```python
assert isinstance(processed_at, datetime)
assert processed_at.tzinfo is not None
```

UTC timestamps make distributed systems easier to operate because workers, containers, CI runners, and MongoDB instances may run in different environments.

Avoid tests that compare exact wall-clock values unless the clock is explicitly controlled.

Prefer property-based assertions such as:

```python
assert processed_at.tzinfo is not None
```

over brittle assertions such as:

```python
assert processed_at == datetime(...)
```

## Input Mutation Testing

Processing functions should avoid unexpectedly modifying the original job document.

This matters because the same job object may be:

- Logged
- Passed to another service
- Used by retry handling
- Included in metrics
- Compared during testing
- Reused by a worker loop

The test therefore preserves a copy of the original job and verifies that processing does not modify it.

For larger systems, immutable domain models or explicit copy-on-write behavior can make these boundaries clearer.

## Test Isolation

Tests should be independent.

Avoid:

```text
test_a creates database state
        ↓
test_b depends on that state
```

Prefer:

```text
test_a → isolated fixture
test_b → isolated fixture
test_c → isolated fixture
```

This allows:

- Parallel execution
- Deterministic CI runs
- Individual test execution
- Easier failure diagnosis

When real MongoDB integration tests are introduced, use dedicated test databases or collections and clean up deterministically.

## Unit Tests vs Integration Tests

| Concern | Unit Test | Integration Test |
|---|---:|---:|
| Payload validation | Yes | Optional |
| Service branching | Yes | Optional |
| Error translation | Yes | Optional |
| PyMongo method invocation | Yes | Yes |
| MongoDB update semantics | No | Yes |
| Index behavior | No | Yes |
| Transactions | No | Yes |
| Replica-set behavior | No | Yes |
| Change streams | No | Yes |
| Query planner | No | Yes |
| Write/read concerns | No | Yes |

The distinction prevents the unit suite from becoming slow and infrastructure-dependent while still providing coverage for MongoDB-specific behavior.

## Background Worker Test Boundaries

The processing service is only one part of the worker architecture.

```mermaid
flowchart LR
    Queue["Jobs Collection"] --> Claim["Job Claiming"]
    Claim --> Worker["Worker Loop"]
    Worker --> Service["ProcessingService"]
    Service --> Result["Result Persistence"]
    Result --> Results["Job Results"]
    Worker --> Retry["Retry / Failure Handling"]
    Retry --> Queue
```

Each layer should have focused tests.

### Job Claiming

Test:

- Pending jobs are selected
- Jobs are atomically transitioned to processing
- Attempts are incremented
- Worker identity is recorded
- No job returns when the queue is empty

### Processing Service

Test:

- Job validation
- Workload execution
- Result persistence
- Error translation
- Idempotent result storage

### Retry Handling

Test:

- Retryable jobs return to pending
- Retry count is respected
- Permanent failures become failed jobs
- Failure metadata is persisted

### Worker Loop

Test:

- Empty queues cause polling
- Claimed jobs are processed
- Processing failures do not terminate the worker
- The worker continues polling

## Running Tests in CI/CD

A typical CI pipeline should install dependencies and run the complete test suite:

```yaml
- name: Install dependencies
  run: pip install -r tests/requirements.txt

- name: Run tests
  env:
    PYTHONPATH: src
  run: pytest -v
```

For integration tests, start MongoDB as a CI service or use a dedicated ephemeral MongoDB environment.

The CI pipeline should distinguish unit tests from integration tests so that failures can be diagnosed quickly.

Example:

```bash
pytest tests/unit -v
pytest tests/integration -v
```

If the repository keeps all tests in a single directory, use pytest markers:

```bash
pytest -m unit
pytest -m integration
```

## Test Environment Configuration

The test environment should never depend on production credentials.

Use `.env.example` as the configuration template and inject real test values through:

- CI secrets
- Local environment variables
- Container environment variables
- Secret managers

Never commit:

```text
.env
```

or credentials such as:

```text
MONGODB_URI=mongodb+srv://user:password@...
```

The repository should contain only safe example configuration.

## Common Testing Mistakes

### Testing Implementation Instead of Behavior

A test that verifies every private implementation detail becomes fragile.

Prefer:

```text
Input
↓
Observable behavior
↓
Expected result
```

rather than coupling tests to every internal statement.

### Mocking Too Deeply

Excessive mocking can produce tests that pass while the real MongoDB integration fails.

Use mocks for service-level isolation and real MongoDB for database-specific behavior.

### Assuming Upsert Means Exactly Once

An upsert prevents duplicate documents for a matching key, but it does not make the entire background operation exactly-once.

External side effects such as:

- Sending email
- Publishing Kafka messages
- Calling REST APIs
- Charging a payment provider
- Writing to another database

require separate idempotency strategies.

### Retrying Non-Transient Errors

Repeatedly retrying malformed input or authentication failures increases load and delays failure visibility.

Classify errors before retrying.

### Sharing Mutable Fixtures

Shared mutable objects can leak state between tests.

Use fresh fixtures and avoid modifying global test data.

### Testing With Production Databases

Tests should never point at production MongoDB.

Use isolated databases, dedicated clusters, ephemeral environments, or local containers.

## Performance Considerations

The unit tests should remain fast enough to execute on every commit.

Keep the unit suite free from:

- Network calls
- Real MongoDB connections
- Long sleeps
- External APIs
- Cloud services

Worker retry tests should patch delays rather than waiting for real retry intervals:

```python
with patch(
    "workers.tasks.WORKER_RETRY_DELAY_SECONDS",
    0,
):
    ...
```

For integration and performance tests, measure actual MongoDB behavior separately.

## Reliability Considerations

Background workers operate under at-least-once execution in many practical architectures.

The system should therefore be designed around:

- Idempotent processing
- Durable job state
- Retry classification
- Safe result persistence
- Failure visibility
- Monitoring
- Dead-letter or failed-job handling
- Recovery procedures

A worker crash should not silently lose a job.

A retry should not create duplicate business side effects.

A database failure should not leave the worker in an undefined state.

These properties are architectural concerns that tests should continuously protect.

## Troubleshooting Test Failures

Use a structured approach:

```text
Symptom
↓
Identify failing test
↓
Determine unit vs integration failure
↓
Inspect fixture and mocked calls
↓
Inspect application behavior
↓
Reproduce with a focused test
↓
Fix root cause
↓
Run targeted test
↓
Run complete suite
```

### Import Errors

Check:

```bash
echo $PYTHONPATH
```

or on PowerShell:

```powershell
$env:PYTHONPATH
```

Verify that `src` is importable and that package names match the project structure.

### Mock Assertion Failures

Inspect the actual call:

```python
print(mock.call_args)
```

Then compare:

- Filter document
- Update document
- Positional arguments
- Keyword arguments
- Number of calls

Do not immediately loosen the assertion. First determine whether the application behavior or test expectation is incorrect.

### MongoDB Integration Failures

For real MongoDB tests, verify connectivity first:

```bash
mongosh "$MONGODB_URI"
```

Then inspect:

```javascript
db.runCommand({ ping: 1 })
```

Check:

- Connection string
- Credentials
- Network access
- TLS configuration
- Database name
- Replica-set configuration
- MongoDB server version

## Production-Oriented Test Matrix

| Scenario | Expected behavior |
|---|---|
| Valid job | Process and persist result |
| Empty job | Reject without persistence |
| Missing `_id` | Reject without persistence |
| Invalid payload | Reject without persistence |
| Execution exception | Raise `ProcessingError` |
| MongoDB persistence failure | Raise `ProcessingError` with original cause |
| Repeated same job | Result persistence remains idempotent |
| Worker retry | Retry policy controls subsequent execution |
| Worker crash | Job recovery mechanism prevents silent loss |
| MongoDB outage | Failure is observable and retryable where appropriate |

## Key Takeaways

- Test `ProcessingService` around observable behavior: validation, execution, persistence, and error handling.
- Use mocks for fast service-level tests and real MongoDB integration tests for database-specific semantics.
- Use the job identifier as an idempotency boundary for result persistence, while recognizing that this does not make external side effects exactly-once.
- Keep background-worker tests isolated, deterministic, and free from real retry delays or production infrastructure.
- Treat retries, failure recovery, and durable job state as reliability concerns that must be validated at both service and worker levels.