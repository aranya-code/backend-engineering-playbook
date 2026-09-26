# README.md

## Overview

This test suite validates the MongoDB query performance optimization examples implemented in this project.

The tests focus on two areas:

- Query behavior implemented in `src/queries`
- Index and collection analysis utilities implemented in `src/analysis` and `src/database`

The suite is intentionally separated from production code so query optimization experiments can be executed repeatedly against controlled test data without coupling performance diagnostics to the application runtime.

The tests should validate both **correctness** and **performance-oriented query characteristics**. A query returning the correct documents is not sufficient for this project; the test suite should also make it possible to verify index usage, examined documents, returned documents, and execution plans.

## Test Structure

```text
tests/
    __init__.py
    test_queries.py
    test_indexes.py
    .env.example
    .gitignore
    requirements.txt
    README.md
```

| File | Responsibility |
| --- | --- |
| `test_queries.py` | Tests optimized query functions and expected query results |
| `test_indexes.py` | Tests index definitions and index-related analysis utilities |
| `.env.example` | Documents test MongoDB configuration |
| `.gitignore` | Prevents local test artifacts and environment files from being committed |
| `requirements.txt` | Defines Python dependencies required by the test suite |
| `README.md` | Documents test execution and engineering expectations |

## Testing Strategy

The project uses `pytest` with PyMongo against MongoDB.

Tests should preferably execute against a dedicated test database rather than a developer's normal development or production database.

The test suite should validate:

- Query correctness
- Projection behavior
- Sorting behavior
- Pagination and limits
- Aggregation results
- Index creation and inspection
- Query execution plans
- `COLLSCAN` versus `IXSCAN` behavior where deterministic
- `totalKeysExamined`
- `totalDocsExamined`
- `nReturned`
- Query execution characteristics

Performance assertions should be conservative. Query execution time can vary significantly between local machines, CI runners, MongoDB versions, storage engines, and dataset sizes. Prefer structural assertions about execution plans and examined documents over strict millisecond thresholds.

## Test Database

Use a dedicated database for the project, for example:

```text
mongodb://localhost:27017
```

with:

```text
mongodb_query_performance_test
```

as the database name.

The test database should contain only synthetic data generated for this project.

Do not point the test suite at:

- Production databases
- Shared development databases
- Databases containing real customer data
- Databases where tests can modify unrelated collections

A typical environment configuration is:

```dotenv
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=mongodb_query_performance_test
MONGODB_SERVER_SELECTION_TIMEOUT_MS=5000
MONGODB_CONNECT_TIMEOUT_MS=5000
MONGODB_SOCKET_TIMEOUT_MS=10000
MONGODB_MAX_POOL_SIZE=10
MONGODB_MIN_POOL_SIZE=0
MONGODB_RETRY_READS=true
MONGODB_RETRY_WRITES=true
```

## Running the Tests

Install the test dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the complete test suite:

```bash
pytest
```

Run a specific test module:

```bash
pytest tests/test_queries.py
```

```bash
pytest tests/test_indexes.py
```

Run with verbose output:

```bash
pytest -v
```

Run with coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

Run only tests matching a keyword:

```bash
pytest -k index
```

## MongoDB Availability

The MongoDB server must be reachable before executing integration tests.

Verify connectivity with `mongosh`:

```bash
mongosh "mongodb://localhost:27017"
```

Then:

```javascript
db.adminCommand({ ping: 1 })
```

Expected result:

```javascript
{ ok: 1 }
```

If MongoDB is running in Docker, the application and test runner must use the appropriate hostname and port based on their network location.

For example, a test process running on the host may use:

```text
mongodb://localhost:27017
```

while a test container may need:

```text
mongodb://mongodb:27017
```

where `mongodb` is the Docker Compose service name.

## Test Isolation

Tests should avoid depending on data left behind by previous test runs.

A reliable integration-test lifecycle is:

```text
Create test database
        ↓
Create required collections
        ↓
Insert deterministic fixture data
        ↓
Create required indexes
        ↓
Execute test
        ↓
Validate result and execution behavior
        ↓
Drop test database
```

A pytest fixture can manage the lifecycle:

```python
import pytest
from pymongo import MongoClient


@pytest.fixture
def database():
    client = MongoClient("mongodb://localhost:27017")
    database = client["mongodb_query_performance_test"]

    yield database

    client.drop_database(database.name)
    client.close()
```

For larger suites, prefer session-scoped client management combined with function- or module-scoped database cleanup. `MongoClient` is designed to be reused and maintains its own connection pool.

## Fixtures and Test Data

Performance tests require representative data.

A small dataset is useful for verifying correctness but is often insufficient for demonstrating meaningful query-planner behavior.

Test fixtures should model realistic characteristics such as:

- Multiple customers
- Multiple order statuses
- Different order dates
- Different order totals
- Repeated customer identifiers
- Selective and non-selective predicates
- Enough documents to exercise indexes
- Documents with fields used by projections
- Documents that represent realistic cardinality

For example:

```python
{
    "customer_id": "customer-001",
    "status": "completed",
    "total": 149.99,
    "created_at": datetime(...),
}
```

The fixture dataset should remain deterministic so test results are reproducible.

Avoid using random data without a fixed seed when the test outcome depends on data distribution.

## Query Correctness Tests

`test_queries.py` should primarily verify that optimized queries return the expected business data.

Typical assertions include:

```python
results = find_recent_orders(
    collection,
    "customer-001",
    limit=10,
)

assert len(results) <= 10
assert all(document["customer_id"] == "customer-001" for document in results)
assert all(document["status"] == "completed" for document in results)
```

Projection behavior should also be validated where applicable:

```python
assert set(results[0]) <= {
    "_id",
    "customer_id",
    "status",
    "total",
    "created_at",
}
```

Tests should verify both positive and boundary cases:

- Matching documents exist
- No documents match
- `limit=1`
- Larger limits
- Multiple customers
- Date boundaries
- Empty collections
- Different statuses
- Aggregation with no matching documents

## Index Tests

`test_indexes.py` should validate that required indexes exist with the expected key patterns and options.

For example:

```python
indexes = list(collection.list_indexes())

index_names = {
    index["name"]
    for index in indexes
}

assert "customer_id_1_status_1_created_at_-1" in index_names
```

For a compound index, validate the complete key definition:

```python
index = next(
    index
    for index in indexes
    if index["name"] == "customer_id_1_status_1_created_at_-1"
)

assert list(index["key"].items()) == [
    ("customer_id", 1),
    ("status", 1),
    ("created_at", -1),
]
```

Do not test only the index name when the key order is important. MongoDB compound index ordering directly affects which query patterns can efficiently use the index.

## Explain Plan Tests

Explain plans are central to this project because the goal is query performance optimization.

A typical diagnostic assertion is:

```python
explain_result = collection.find(
    {
        "customer_id": "customer-001",
        "status": "completed",
    }
).sort(
    "created_at",
    -1,
).limit(50).explain("executionStats")
```

Extract relevant metrics:

```python
execution_stats = explain_result["executionStats"]

assert execution_stats["nReturned"] <= 50
assert execution_stats["totalDocsExamined"] >= execution_stats["nReturned"]
```

For a properly indexed query, the winning plan may contain an `IXSCAN` stage.

The test should not blindly require a specific internal plan shape unless the exact MongoDB version and query conditions make that requirement stable.

Prefer assertions around meaningful characteristics such as:

- An index is selected
- A collection scan is absent where expected
- Documents examined are bounded
- Returned documents match expectations

## Performance Assertions

Avoid fragile assertions such as:

```python
assert execution_time_ms < 5
```

A fixed execution-time threshold can fail because of:

- CI resource contention
- Different CPU performance
- Cold caches
- Dataset size
- MongoDB version
- Storage characteristics
- Container overhead

Prefer plan-oriented assertions:

```python
stats = analyze_execution_stats(explain_result)

assert stats["n_returned"] >= 0
assert stats["total_docs_examined"] is not None
assert stats["total_keys_examined"] is not None
```

For a controlled benchmark environment, latency thresholds may be appropriate, but they should be treated as benchmark acceptance criteria rather than ordinary unit-test assertions.

## Before-and-After Optimization Testing

This project should demonstrate the difference between an unoptimized and optimized query.

A useful test flow is:

```text
Unoptimized Query
        ↓
COLLSCAN / high documents examined
        ↓
Create appropriate index
        ↓
Optimized Query
        ↓
IXSCAN / reduced documents examined
```

For example, compare:

```python
unoptimized = collection.find(
    {
        "customer_id": "customer-001",
        "status": "completed",
    }
)
```

with an indexed query using an appropriate compound index.

The important comparison is not merely execution time. Examine:

| Metric | Unoptimized | Optimized |
| --- | --- | --- |
| Winning plan | Often `COLLSCAN` | Often `IXSCAN` |
| Documents examined | Potentially large | Typically reduced |
| Keys examined | None or low | Index-dependent |
| Returned documents | Same business result | Same business result |
| Execution time | Environment-dependent | Environment-dependent |

The optimized query must preserve correctness while reducing unnecessary work.

## Aggregation Tests

Aggregation tests should validate both the resulting data and the pipeline behavior.

For example:

```python
results = aggregate_customer_sales(
    collection,
    customer_id="customer-001",
)

assert len(results) <= 1

if results:
    result = results[0]

    assert result["customer_id"] == "customer-001"
    assert result["order_count"] >= 0
    assert result["total_sales"] >= 0
```

When aggregation performance is being evaluated, inspect the aggregation explain plan separately rather than assuming that a fast result on a small fixture represents production behavior.

Important considerations include:

- `$match` filtering early
- Index usage
- `$sort` placement
- `$group` memory usage
- `$unwind` cardinality expansion
- `$lookup` join cost
- Large intermediate result sets

## Index Statistics

The project includes utilities for inspecting index usage through `$indexStats`.

Tests can validate the shape of returned statistics:

```python
statistics = get_index_statistics(collection)

for index_stat in statistics:
    assert "name" in index_stat
    assert "accesses" in index_stat
```

An index with zero recorded operations should not automatically be classified as permanently unused.

Index statistics represent observed usage over the relevant statistics period. They must be interpreted together with:

- Application traffic
- Deployment history
- Query logs
- Monitoring data
- Reporting workloads
- Maintenance jobs
- Time since statistics reset

## Collection Statistics

Collection statistics can be used to validate that the test database contains the expected test data and indexes.

Typical metrics include:

- Document count
- Data size
- Storage size
- Total index size

Tests should avoid asserting exact storage sizes because storage representation can vary across MongoDB versions and environments.

Prefer semantic assertions:

```python
size = get_collection_size(collection)

assert size["document_count"] > 0
assert size["data_size_bytes"] > 0
assert size["total_index_size_bytes"] >= 0
```

## Integration Test Boundaries

These tests are MongoDB integration tests rather than pure unit tests.

They require:

- A running MongoDB instance
- A valid connection string
- Appropriate database permissions
- Test data
- Compatible PyMongo and MongoDB versions

Pure unit tests should be used for logic that does not require MongoDB.

Integration tests should be used when validating:

- Query execution
- Index behavior
- Aggregation
- Explain plans
- MongoDB-specific semantics
- BSON behavior
- Connection behavior

Mocking MongoDB for an `explain()` test defeats the purpose of the test because the query planner exists inside MongoDB, not inside PyMongo.

## CI/CD Considerations

The test suite should run in CI against an isolated MongoDB service.

A typical CI workflow is:

```text
Checkout repository
        ↓
Install Python dependencies
        ↓
Start MongoDB
        ↓
Wait for MongoDB readiness
        ↓
Run pytest
        ↓
Generate coverage
        ↓
Publish test results
```

The CI environment should use deterministic configuration and should never require production credentials.

For performance-focused tests, record MongoDB and Python versions because execution characteristics can change across versions.

## Common Testing Mistakes

### Using a Shared Database

Tests that use a shared development database can modify or delete unrelated data.

Use a dedicated test database and clean it between test runs.

### Mocking Query Planner Behavior

Mocks cannot validate `IXSCAN`, `COLLSCAN`, execution statistics, or actual index selection.

Use a real MongoDB instance for query-performance integration tests.

### Asserting Exact Execution Time

Execution time is affected by the environment.

Prefer explain-plan metrics and bounded resource behavior.

### Testing Only Query Results

A query can return correct data while performing a full collection scan.

Performance tests should inspect execution characteristics in addition to correctness.

### Overfitting to One Explain Plan

Explain-plan internals can vary across MongoDB versions and data distributions.

Assert stable performance properties rather than unnecessarily strict internal plan structures.

### Treating Zero Index Usage as Permanent Evidence

`$indexStats` reflects recorded usage during the relevant statistics period. Zero operations do not prove that an index will never be required.

### Using Production Data

Production data can expose sensitive information and make tests destructive or nondeterministic.

Use synthetic, representative fixtures.

## Test Design Principles

Follow these principles when extending the test suite:

- Keep tests deterministic.
- Use isolated MongoDB databases.
- Prefer real MongoDB integration for database behavior.
- Validate correctness before performance characteristics.
- Test indexes according to actual query patterns.
- Inspect explain plans for optimization experiments.
- Avoid brittle latency assertions.
- Keep fixtures representative of realistic cardinality.
- Clean up test databases after execution.
- Never embed production credentials.
- Keep performance benchmarks separate from ordinary correctness tests when possible.
- Record MongoDB and PyMongo versions for reproducible performance investigations.

## Key Takeaways

- Test MongoDB query correctness and execution characteristics separately; correct results do not guarantee efficient execution.
- Use real MongoDB integration tests for indexes, aggregation, `explain()`, and query-planner behavior.
- Prefer assertions on `IXSCAN`, `COLLSCAN`, `nReturned`, `totalDocsExamined`, and `totalKeysExamined` over fragile execution-time thresholds.
- Use isolated, deterministic test data and never run performance tests against production or shared databases.
- Treat explain plans and index statistics as diagnostic evidence that must be interpreted in the context of data distribution, workload, and MongoDB version.