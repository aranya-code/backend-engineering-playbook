# 06- Generators

## Overview

A generator is a Python construct for producing values lazily, one value at a time, rather than materializing an entire result in memory.

Generators are based on the iterator protocol but provide a convenient way to implement iterators using `yield`.

They are particularly valuable in backend and data-engineering systems when processing:

- Large database result sets
- Large files
- API response streams
- Event streams
- ETL pipelines
- Kafka records
- Paginated data
- Potentially unbounded sequences
- Expensive computations

The core distinction is:

```text
List:
    produce everything
          |
          v
    [item1, item2, item3, ...]
          |
          v
    caller consumes later


Generator:
    produce item
          |
          v
    caller consumes
          |
          v
    resume generator
          |
          v
    produce next item
```

Generators provide **lazy evaluation** and **suspended execution**.

They do not automatically make an operation faster. Their primary benefits are reduced memory usage, incremental processing, and the ability to represent streams of values naturally.

## Why Generators Exist

Consider processing a large file.

A materializing approach:

```python
with open("events.log", encoding="utf-8") as file:
    lines = file.readlines()

for line in lines:
    process(line)
```

loads all lines into memory.

A generator-based approach:

```python
with open("events.log", encoding="utf-8") as file:
    for line in file:
        process(line)
```

processes the file incrementally.

For a sufficiently large dataset, the difference can be significant:

```text
Materialized processing

Disk
 |
 v
Entire file
 |
 v
Python memory
 |
 v
Processing


Streaming processing

Disk
 |
 v
One chunk / line
 |
 v
Processing
 |
 v
Next chunk / line
```

Generators are therefore an important tool for controlling memory consumption.

## Generator Functions

A function containing `yield` is a generator function.

```python
def generate_numbers():
    yield 1
    yield 2
    yield 3
```

Calling it does not execute the function body immediately:

```python
numbers = generate_numbers()

print(numbers)
```

`numbers` is a generator object.

Execution begins when values are requested:

```python
for number in numbers:
    print(number)
```

Output:

```text
1
2
3
```

The important semantic difference is:

```python
def regular_function():
    return 42
```

versus:

```python
def generator_function():
    yield 42
```

A regular function executes when called.

A generator function returns a generator object and executes incrementally as that object is iterated.

## `yield` vs `return`

`return` terminates a normal function.

```python
def get_user():
    return user
```

`yield` produces a value while suspending generator execution.

```python
def get_users():
    yield user1
    yield user2
```

A generator can yield multiple values across multiple resumptions.

```text
generator_function()
       |
       v
 generator object
       |
       +--> next() --> yield value 1
       |
       +--> next() --> yield value 2
       |
       +--> next() --> yield value 3
       |
       +--> next() --> StopIteration
```

## Generator Execution Model

Consider:

```python
def process():
    print("start")
    yield 10
    print("middle")
    yield 20
    print("end")
```

Calling:

```python
generator = process()
```

does not print anything.

The first:

```python
next(generator)
```

executes until:

```python
yield 10
```

and returns:

```text
10
```

The generator is suspended.

The next:

```python
next(generator)
```

resumes from the point immediately after the previous `yield`.

The sequence is:

```text
create generator
      |
      v
no body execution
      |
      v
next()
      |
      v
print("start")
      |
      v
yield 10
      |
   suspended
      |
      v
next()
      |
      v
print("middle")
      |
      v
yield 20
      |
   suspended
      |
      v
next()
      |
      v
print("end")
      |
      v
StopIteration
```

This suspended execution state is one of the defining properties of generators.

## `next()`

Generators implement the iterator protocol.

```python
def numbers():
    yield 1
    yield 2


generator = numbers()

print(next(generator))
print(next(generator))
```

Output:

```text
1
2
```

Calling `next()` after the generator is exhausted raises `StopIteration`:

```python
next(generator)
```

The `for` loop handles `StopIteration` automatically.

```python
for number in numbers():
    print(number)
```

Conceptually, iteration behaves like:

```python
iterator = iter(numbers())

while True:
    try:
        value = next(iterator)
    except StopIteration:
        break

    print(value)
```

## Generator Object State

A generator object maintains suspended execution state.

It retains enough state to resume execution, including:

- Current execution position
- Local variables
- Referenced objects
- Exception state
- Associated frame information

For example:

```python
def counter():
    value = 0

    while value < 3:
        yield value
        value += 1
```

The local variable `value` remains available when execution resumes.

This is fundamentally different from repeatedly calling a normal function that starts from the beginning each time.

## Memory Efficiency

The major practical advantage of generators is avoiding unnecessary materialization.

Consider:

```python
def load_user_ids(rows):
    return [row["user_id"] for row in rows]
```

versus:

```python
def load_user_ids(rows):
    for row in rows:
        yield row["user_id"]
```

The list stores all results.

The generator stores the execution state and produces values incrementally.

| Approach | Memory | Evaluation | Best For |
|---|---:|---|---|
| List | O(n) | Eager | Small bounded collections |
| Tuple | O(n) | Eager | Immutable materialized data |
| Generator | O(1) additional sequence storage | Lazy | Large/streaming data |
| Set | O(n) | Eager | Membership/deduplication |
| Dict | O(n) | Eager | Key-value lookup |

The exact memory usage of a generator is not literally always constant because the generator may retain referenced objects. The useful distinction is that it does not materialize the entire output sequence.

## Generator vs List

Consider one million records:

```python
def get_ids(records):
    return [record["id"] for record in records]
```

This requires memory for the resulting collection.

A generator:

```python
def get_ids(records):
    for record in records:
        yield record["id"]
```

allows:

```python
for user_id in get_ids(records):
    process_user(user_id)
```

Only the currently required values need to flow through the pipeline.

## Generator Expressions

Generator expressions provide a concise syntax for lazy transformations.

```python
user_ids = (user["id"] for user in users)
```

Compare:

```python
user_ids = [user["id"] for user in users]
```

with:

```python
user_ids = (user["id"] for user in users)
```

The first creates a list immediately.

The second creates a generator.

Generator expressions are especially useful when the consumer already accepts an iterable.

For example:

```python
total = sum(
    order["amount"]
    for order in orders
)
```

There is no need to create an intermediate list.

## Generator Pipelines

Generators compose naturally into processing pipelines.

```python
def read_lines(file):
    for line in file:
        yield line.strip()


def valid_lines(lines):
    for line in lines:
        if line:
            yield line


def parse_events(lines):
    for line in lines:
        yield parse_event(line)
```

The pipeline can be consumed:

```python
with open("events.log", encoding="utf-8") as file:
    lines = read_lines(file)
    valid = valid_lines(lines)
    events = parse_events(valid)

    for event in events:
        process_event(event)
```

The data flow is:

```text
File
 |
 v
read_lines()
 |
 v
valid_lines()
 |
 v
parse_events()
 |
 v
process_event()
```

Each stage processes values incrementally.

This is one of the most useful production patterns for generators.

## Lazy Evaluation

A generator does not perform work until values are requested.

```python
def expensive_operation(items):
    for item in items:
        result = expensive_transform(item)
        yield result
```

Creating:

```python
results = expensive_operation(items)
```

does not execute `expensive_transform()`.

Execution begins when:

```python
next(results)
```

or:

```python
for result in results:
    ...
```

requests a value.

This allows downstream consumers to control the rate at which upstream computation occurs.

## Backpressure

Generators can naturally support pull-based backpressure.

Consider:

```python
for event in generate_events():
    process_event(event)
```

The consumer requests one event at a time.

Conceptually:

```text
Consumer
   |
   | request next item
   v
Generator
   |
   | produce one item
   v
Consumer
   |
   | process
   |
   | request next item
   v
Generator
```

If the consumer slows down, the generator does not automatically continue producing an unbounded number of items.

This is useful for in-process pipelines.

However, generators are not a complete distributed backpressure mechanism. Kafka, HTTP streaming, message brokers, and asynchronous systems have additional buffering and flow-control semantics.

## Infinite Generators

Generators can represent unbounded sequences.

```python
def sequence():
    value = 0

    while True:
        yield value
        value += 1
```

This is safe to create because values are generated lazily:

```python
numbers = sequence()
```

The following is safe:

```python
for number in numbers:
    if number == 10:
        break
```

Trying to materialize it is not:

```python
list(sequence())
```

This never terminates and eventually exhausts available memory.

Infinite generators should always have a bounded consumer or termination condition.

## Generator Pipelines with `itertools`

Generators work particularly well with `itertools`.

```python
from itertools import islice


def sequence():
    value = 0

    while True:
        yield value
        value += 1


first_ten = islice(sequence(), 10)

for value in first_ten:
    print(value)
```

The pipeline remains lazy.

This is useful for:

- Pagination
- Sampling
- Windowing
- Filtering
- Chunking
- Bounded processing

## File Streaming

Generators are commonly used to process large files.

```python
from collections.abc import Iterator
from pathlib import Path


def read_events(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as file:
        for line in file:
            yield parse_event(line)
```

Consumption:

```python
for event in read_events(Path("events.jsonl")):
    process_event(event)
```

The file is not loaded into memory all at once.

For very large files, streaming can significantly reduce memory pressure and improve time-to-first-result.

## Database Streaming

Generators are useful for processing database results incrementally.

A repository might expose:

```python
from collections.abc import Iterator


def iter_users(connection) -> Iterator[User]:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, email
        FROM users
        ORDER BY id
        """
    )

    for row in cursor:
        yield User(
            id=row[0],
            email=row[1],
        )
```

Consumption:

```python
for user in repository.iter_users(connection):
    process_user(user)
```

However, a generator does not guarantee database-side streaming by itself.

The underlying database driver and cursor configuration determine whether rows are actually fetched incrementally.

Production systems should understand:

- Cursor behavior
- Fetch size
- Transaction lifetime
- Connection lifetime
- Server-side cursors where supported
- Driver buffering
- Network transfer
- Query execution time

A generator wrapped around `cursor.fetchall()` does not provide true streaming:

```python
def users(cursor):
    rows = cursor.fetchall()

    for row in rows:
        yield row
```

The entire result set has already been materialized.

## API Streaming

Generators can support incremental response production, depending on the web framework and response type.

A conceptual streaming endpoint:

```python
def generate_lines():
    for event in event_source():
        yield serialize_event(event)
```

The HTTP layer can stream generated chunks to the client rather than constructing one giant response body.

The architecture becomes:

```text
Client
  |
  | HTTP request
  v
Nginx / Load Balancer
  |
  v
Application
  |
  v
Generator
  |
  +--> Database / Kafka / Service
  |
  v
Response chunks
  |
  v
Client
```

Production streaming requires consideration of:

- Chunking
- Buffering
- Timeouts
- Proxy configuration
- Connection lifetime
- Client cancellation
- Error handling
- Observability
- Memory usage

Nginx and other proxies may buffer responses unless configured appropriately for the intended streaming behavior.

## FastAPI Streaming

FastAPI can expose streaming responses using an iterator or generator.

```python
from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse


app = FastAPI()


def generate_events() -> Iterator[str]:
    for event in load_events():
        yield f"{event}\n"


@app.get("/events")
def stream_events() -> StreamingResponse:
    return StreamingResponse(
        generate_events(),
        media_type="application/x-ndjson",
    )
```

The important architectural distinction is:

```text
Generator
    |
    v
Produces chunks
    |
    v
StreamingResponse
    |
    v
ASGI server
    |
    v
HTTP client
```

Whether the entire system remains streaming depends on all layers in the path.

## Async Generators

Python also supports asynchronous generators.

```python
async def generate_events():
    async for event in event_source():
        yield event
```

They are consumed using:

```python
async for event in generate_events():
    await process_event(event)
```

An asynchronous generator can suspend at both:

```python
await
```

and:

```python
yield
```

This makes it appropriate for asynchronous I/O pipelines.

## Async Generator Execution

The flow is:

```text
async generator
      |
      v
produce value
      |
      v
consumer receives value
      |
      v
consumer awaits processing
      |
      v
generator resumes
      |
      v
next value
```

Example:

```python
import asyncio


async def events():
    for event_id in range(3):
        await asyncio.sleep(0.1)
        yield event_id


async def main():
    async for event_id in events():
        print(event_id)


asyncio.run(main())
```

Async generators are useful when producing values requires asynchronous operations.

## Synchronous vs Asynchronous Generators

| Feature | Generator | Async Generator |
|---|---|---|
| Syntax | `yield` | `async def` + `yield` |
| Consumer | `for` | `async for` |
| Advancement | `next()` | `anext()` |
| Blocking I/O | Possible | Should use async I/O |
| Async suspension | No | Yes |
| Typical use | Files, CPU pipelines, sync DB | Async APIs, async DB, streams |

Do not use an async generator merely because the application uses `asyncio`. Use it when producing the values requires asynchronous operations.

## Generator Methods

Generators expose methods beyond `next()`.

### `send()`

A value can be sent into a suspended generator:

```python
def accumulator():
    total = 0

    while True:
        value = yield total
        total += value
```

Usage:

```python
generator = accumulator()

next(generator)

print(generator.send(10))
print(generator.send(5))
```

This provides bidirectional communication between the consumer and generator.

It is a powerful feature but relatively uncommon in modern backend application code.

### `throw()`

An exception can be injected into a suspended generator:

```python
generator.throw(RuntimeError("failure"))
```

This is useful for advanced generator protocols and resource-aware abstractions.

### `close()`

A generator can be explicitly closed:

```python
generator.close()
```

This causes `GeneratorExit` to be raised inside the generator.

Generators can use `finally` for cleanup:

```python
def resource_stream():
    resource = acquire_resource()

    try:
        while True:
            yield resource.read()
    finally:
        resource.close()
```

This is important when generators own resources.

## `yield from`

`yield from` delegates iteration to another iterable or generator.

```python
def child():
    yield 1
    yield 2


def parent():
    yield from child()
    yield 3
```

Consumption produces:

```text
1
2
3
```

Without `yield from`, delegation would require:

```python
def parent():
    for value in child():
        yield value

    yield 3
```

`yield from` is especially useful when composing generators.

## Delegating Return Values

A generator can return a value:

```python
def child():
    yield 1
    return "complete"
```

A delegating generator can receive that return value through `yield from`:

```python
def parent():
    result = yield from child()
    print(result)
```

The returned value is carried through `StopIteration.value`.

This is an advanced generator feature and is less common in ordinary application code.

## Generator Expressions vs Generator Functions

| Feature | Generator Expression | Generator Function |
|---|---|---|
| Syntax | `(x for x in items)` | `def` + `yield` |
| Complexity | Simple | Arbitrary logic |
| Multiple stages | Limited | Excellent |
| Exception handling | Limited | Full control |
| State | Implicit | Explicit local state |
| Reusability | Usually local | Good for named APIs |

Use generator expressions for short transformations.

Use generator functions when the logic has meaningful control flow or deserves a named abstraction.

## Generator Reusability

Generators are generally single-use iterators.

```python
numbers = (x for x in range(3))

list(numbers)
```

produces:

```text
[0, 1, 2]
```

Calling:

```python
list(numbers)
```

again produces:

```text
[]
```

The generator has been exhausted.

If a computation needs to be repeated, expose a function that creates a fresh generator:

```python
def generate_numbers():
    return (x for x in range(3))
```

Then:

```python
list(generate_numbers())
list(generate_numbers())
```

each creates an independent iterator.

## Generator Exhaustion

Once a generator reaches the end:

```python
next(generator)
```

raises:

```python
StopIteration
```

The generator cannot simply restart.

This creates an important API design consideration.

Bad:

```python
class ReportService:
    def __init__(self):
        self.rows = (load_row(i) for i in range(100))

    def first_report(self):
        return list(self.rows)

    def second_report(self):
        return list(self.rows)
```

The second call receives no rows after the generator has been exhausted.

Prefer creating the iterator when needed.

## Generator Ownership and Resource Lifetime

Resource lifetime is a critical production concern.

Consider:

```python
def read_rows(connection):
    cursor = connection.cursor()

    try:
        for row in cursor:
            yield row
    finally:
        cursor.close()
```

The resource remains active while the generator is suspended.

This means a consumer that stops early can affect resource lifetime:

```python
for row in read_rows(connection):
    if should_stop(row):
        break
```

The generator may need to be explicitly closed or otherwise managed depending on the surrounding resource lifecycle.

For file and database resources, prefer clear ownership and context-manager boundaries.

## Generators and Context Managers

For resource-heavy streaming operations, combining generators with context managers can make lifecycle semantics explicit.

```python
from contextlib import contextmanager
from collections.abc import Iterator


@contextmanager
def open_event_stream(path) -> Iterator[Iterator[str]]:
    file = open(path, encoding="utf-8")

    try:
        yield (line.strip() for line in file)
    finally:
        file.close()
```

Usage:

```python
with open_event_stream("events.log") as events:
    for event in events:
        process_event(event)
```

The important principle is to avoid making resource ownership ambiguous.

## Generators and Exceptions

Exceptions raised while producing values occur during iteration, not necessarily when the generator is created.

```python
def generate():
    yield load_data()
```

This:

```python
generator = generate()
```

does not call `load_data()`.

The exception may occur here:

```python
next(generator)
```

or during:

```python
for value in generator:
    ...
```

This affects error handling and transaction boundaries.

## Generator Pipelines and Error Handling

A pipeline can isolate failures:

```python
def parse_lines(lines):
    for line in lines:
        try:
            yield parse_line(line)
        except ValueError:
            record_invalid_line(line)
```

This allows the pipeline to continue processing valid records.

However, whether failures should be skipped depends on the application's correctness requirements.

For financial, security, or transactional data, silently skipping malformed records may be unacceptable.

## Generator-Based ETL

Generators are particularly effective for ETL pipelines.

```text
Source
  |
  v
Extract
  |
  v
Validate
  |
  v
Transform
  |
  v
Batch
  |
  v
Load
```

Example:

```python
def extract(rows):
    for row in rows:
        yield row


def validate(rows):
    for row in rows:
        if row["email"]:
            yield row


def transform(rows):
    for row in rows:
        yield {
            "email": row["email"].strip().lower(),
        }


def load(rows):
    for row in rows:
        save_row(row)
```

Pipeline:

```python
pipeline = transform(
    validate(
        extract(source_rows)
    )
)

load(pipeline)
```

This avoids unnecessary intermediate collections.

## Batching Generator Output

Streaming one record at a time is not always optimal for database writes or network calls.

A batching generator can combine values:

```python
from collections.abc import Iterable, Iterator
from itertools import islice
from typing import TypeVar


T = TypeVar("T")


def batched(
    items: Iterable[T],
    size: int,
) -> Iterator[list[T]]:
    iterator = iter(items)

    while batch := list(islice(iterator, size)):
        yield batch
```

Usage:

```python
for batch in batched(events, 500):
    bulk_insert(batch)
```

This provides a useful balance:

```text
Too much materialization
        |
        v
Entire dataset
        |
        v
High memory


Too little batching
        |
        v
One database call per item
        |
        v
High overhead


Balanced
        |
        v
Bounded batches
        |
        v
Controlled memory + efficient I/O
```

Modern Python versions also provide `itertools.batched()` for this common pattern.

## Generator Pipelines and Database Transactions

Streaming and transaction boundaries must be designed together.

A generator that keeps a database transaction open while a slow consumer processes results can hold:

- Database connections
- Transaction state
- Locks
- Server-side cursors
- MVCC snapshots

for longer than intended.

Avoid designs where:

```text
Database transaction
        |
        v
Generator
        |
        v
Slow external processing
        |
        v
Transaction remains open
```

Instead, consider bounded batches:

```text
Read batch
   |
   v
Commit / release DB resources
   |
   v
Process batch
   |
   v
Read next batch
```

The correct approach depends on consistency requirements.

## Generators and Concurrency

A generator object is generally not designed for concurrent consumption by multiple threads.

Avoid:

```python
generator = generate_events()

thread_a -> next(generator)
thread_b -> next(generator)
```

without explicit synchronization and a strong reason to share the iterator.

A safer architecture is often:

```text
Producer
   |
   v
Queue
   |
   +--> Consumer A
   |
   +--> Consumer B
```

Use:

- `queue.Queue` for threaded pipelines.
- `asyncio.Queue` for async pipelines.
- Kafka or another broker for durable distributed processing.

Generators are excellent for sequential pipelines but are not substitutes for concurrency primitives.

## Generators and Async Concurrency

An async generator can be consumed by one async consumer:

```python
async for event in event_stream():
    await process(event)
```

If multiple consumers need the same stream, explicitly define the distribution semantics.

For fan-out processing:

```text
Producer
   |
   v
asyncio.Queue
   |
   +--> Worker A
   |
   +--> Worker B
   |
   +--> Worker C
```

An async generator alone does not provide broadcast or work distribution semantics.

## Generators and Kafka

Kafka consumers already provide streaming semantics.

A Python Kafka client may expose records incrementally, and a generator can be used to wrap application-level processing:

```python
def events(consumer):
    for message in consumer:
        yield deserialize(message)
```

However, offset management remains a Kafka concern.

Do not assume that yielding a message means it has been durably processed.

A reliable consumer must define:

```text
Consume
   |
   v
Process
   |
   v
Persist / commit side effects
   |
   v
Commit offset
```

The generator is merely part of the local iteration mechanism.

## Generators and Memory Retention

Generators can reduce memory usage, but they can also retain objects longer than expected.

For example:

```python
def process(records):
    large_buffer = create_large_buffer()

    for record in records:
        yield process_record(record, large_buffer)
```

While the generator remains alive, `large_buffer` may remain reachable.

Long-lived generators should therefore be reviewed for captured state and resource ownership.

Generators reduce materialization; they do not eliminate memory management concerns.

## Performance Considerations

Generators can improve memory efficiency and time-to-first-result.

They can also reduce unnecessary intermediate allocations:

```python
total = sum(
    transform(x)
    for x in values
)
```

instead of:

```python
total = sum(
    [transform(x) for x in values]
)
```

The generator expression avoids constructing an intermediate list.

However, generators can introduce overhead from:

- Python-level iteration
- Generator suspension/resumption
- Function calls
- Object allocation
- Per-item processing

For CPU-heavy workloads, vectorized operations or specialized libraries may outperform Python generator pipelines.

For I/O-heavy workloads, generator-based streaming can be highly effective.

Measure with representative workloads.

## Generator vs Materialization

Use a generator when:

- The dataset is large.
- Results are consumed once.
- Results can be processed incrementally.
- Time-to-first-result matters.
- The producer may be unbounded.
- Intermediate collections are unnecessary.

Materialize when:

- Multiple passes are required.
- Random access is required.
- The dataset is small.
- The data must be reused.
- The consumer requires a concrete collection.
- Length is required without consuming the iterator.

## Generators vs Lists

| Requirement | Generator | List |
|---|---|---|
| Lazy evaluation | Yes | No |
| Low additional sequence memory | Yes | No |
| Random access | No | Yes |
| Reusable without recreation | No | Yes |
| Multiple passes | No | Yes |
| Immediate validation of all values | No | Yes |
| Streaming | Excellent | Poor |
| Indexing | No | Yes |
| `len()` | No | Yes |
| Time to first item | Usually low | Requires full construction first |

The correct choice depends on the data lifecycle rather than a blanket preference for generators.

## Generator API Design

A function returning an iterator communicates streaming semantics:

```python
from collections.abc import Iterator


def iter_users() -> Iterator[User]:
    ...
```

Naming can reinforce intent:

```python
iter_users()
iter_events()
iter_rows()
stream_events()
```

An `iter_` prefix is useful when the API returns an iterator and callers should understand that values are produced lazily.

Document important semantics:

- Whether the iterator is single-use.
- Whether it owns resources.
- When I/O occurs.
- What exceptions can occur during iteration.
- Whether ordering is guaranteed.
- Whether results are eventually consistent.
- Whether cancellation is supported.

## Testing Generators

Test both values and laziness.

Basic test:

```python
def test_generate_ids():
    result = list(generate_ids([1, 2, 3]))

    assert result == [1, 2, 3]
```

To verify lazy behavior:

```python
def test_generator_is_lazy():
    calls = 0

    def source():
        nonlocal calls
        calls += 1
        yield 1
        yield 2

    generator = transform(source())

    assert calls == 0

    assert next(generator) == 1
    assert calls == 1
```

Also test:

- Empty input
- Single item
- Exhaustion
- Exceptions during iteration
- Early termination
- Resource cleanup
- Large datasets
- Async generator behavior
- Cancellation where applicable

## Testing Streaming Systems

For an HTTP streaming endpoint, do not only test the final concatenated response.

Also consider:

- First-byte latency
- Chunk boundaries
- Client disconnects
- Timeout behavior
- Partial failures
- Resource cleanup
- Proxy buffering
- Cancellation

The production behavior of a streaming API depends on the complete request path, not only the Python generator.

## Serialization and Pickling

Generator objects represent active execution state and are not generally suitable for serialization or persistence.

Do not design distributed jobs around passing live generator objects between processes or services.

Instead, represent the state explicitly:

```python
@dataclass
class ProcessingCursor:
    last_id: int
```

Then reconstruct the iterator from durable state.

For Celery, multiprocessing, or distributed workers, prefer:

```text
Serializable task input
        |
        v
Worker
        |
        v
Create generator locally
        |
        v
Process stream
```

rather than attempting to transfer an active generator.

## Operational Considerations

Production generator pipelines should be observable.

Track where appropriate:

- Records processed
- Records failed
- Processing rate
- Batch size
- Processing latency
- Queue lag
- Database cursor duration
- Stream duration
- Memory usage
- Client disconnects
- Generator termination
- Retry counts

For long-running streams, health and progress metrics are particularly important.

A process that remains alive while making no progress should not necessarily be considered healthy.

## Security Considerations

Generators are not inherently a security boundary.

When streaming data:

- Enforce authorization before exposing records.
- Avoid leaking sensitive records through logs.
- Validate streamed input.
- Apply output filtering consistently.
- Bound resource consumption.
- Apply request and stream timeouts.
- Avoid unbounded streams for untrusted clients.
- Prevent excessive memory accumulation in downstream buffering layers.

Streaming can make denial-of-service behavior easier to sustain if connections remain open indefinitely.

## Common Mistakes

### Materializing Before Yielding

This defeats the purpose:

```python
def users():
    rows = database.fetch_all()

    for row in rows:
        yield row
```

The database results are already fully materialized.

### Assuming Generators Are Always Faster

Generators primarily improve memory behavior and laziness.

They can be slower than optimized bulk operations.

### Reusing an Exhausted Generator

Generators are usually single-use.

Create a fresh iterator when another pass is required.

### Holding Resources Too Long

A generator can keep a database connection or file open while the consumer is slow.

Define resource ownership carefully.

### Ignoring Exceptions During Iteration

Errors can occur on `next()` rather than generator creation.

### Using Generators for Random Access

If consumers need:

```python
items[500]
```

a list or another indexed data structure is usually more appropriate.

### Sharing Generators Across Threads

Concurrent access to a single iterator requires explicit coordination.

### Creating Unbounded Streams Without Limits

An infinite generator must have a bounded consumer or termination condition.

### Confusing Generator Streaming with Distributed Streaming

A Python generator is an in-process abstraction. Kafka, HTTP streaming, and distributed queues have additional durability, buffering, and delivery semantics.

## Production Pitfalls

| Pitfall | Impact | Mitigation |
|---|---|---|
| `fetchall()` before `yield` | High memory usage | Use streaming cursor/fetch APIs |
| Long-lived DB cursor | Connection exhaustion | Bound processing and transaction lifetime |
| Exhausted generator reuse | Missing data | Create a fresh iterator |
| Infinite generator materialization | Process OOM | Bound consumption |
| Slow consumer | Resource retention | Define timeouts and ownership |
| Generator shared across threads | Race/errors | Use queues or synchronization |
| Hidden I/O during iteration | Unexpected latency | Document lazy I/O semantics |
| Large captured state | Memory retention | Minimize generator-local state |
| Proxy buffering | Broken streaming behavior | Configure infrastructure appropriately |
| No stream observability | Stalled processing unnoticed | Emit progress and latency metrics |
| Unbounded client streams | Resource exhaustion | Apply limits, quotas, and timeouts |
| Retrying streamed operations blindly | Duplicate processing | Design idempotency and checkpointing |

## Senior Engineering Heuristics

Use generators as a **data-flow abstraction**, not merely as a memory-saving trick.

A strong design usually has:

```text
Source
  |
  v
Iterator / Generator
  |
  v
Transformation
  |
  v
Validation
  |
  v
Bounded batching
  |
  v
Side effect
```

Keep each stage:

- Lazy where appropriate.
- Single-purpose.
- Explicit about errors.
- Explicit about resource ownership.
- Bounded in memory.
- Observable when long-running.
- Compatible with cancellation or termination requirements.

For high-throughput systems, determine whether Python-level iteration is actually the bottleneck before optimizing the generator itself.

## Decision Guide

| Situation | Recommended Approach |
|---|---|
| Small result set | List |
| Large sequential dataset | Generator |
| Large file | File iterator / generator |
| Database streaming | Driver-supported streaming cursor + generator |
| ETL pipeline | Generator pipeline |
| Async I/O stream | Async generator |
| Reusable collection | Materialized collection |
| Random access | List / indexed structure |
| Concurrent workers | Queue / task system |
| Durable distributed stream | Kafka / message broker |
| Shared distributed state | Redis / PostgreSQL |
| Batch database writes | Generator + bounded batching |
| Framework-supported streaming | Framework streaming response |
| CPU-heavy numerical transformation | Measure against vectorized/specialized alternatives |

## Interview Traps

### Is a Generator an Iterator?

A generator object is an iterator. Generator functions provide a convenient way to create iterator objects using `yield`.

### Does Calling a Generator Function Execute Its Body?

No. Calling the generator function creates a generator object. Its body begins executing when iteration requests a value.

### What Happens at `yield`?

The generator produces a value and suspends execution. Its state is retained so execution can resume after that `yield`.

### What Happens When a Generator Finishes?

Python raises `StopIteration` internally. A `for` loop handles this automatically.

### Are Generators Reusable?

Normally no. A generator is an iterator and is generally consumed once.

### What Is the Main Advantage of a Generator?

Lazy, incremental production of values without materializing the entire result sequence.

### Are Generators Always More Memory Efficient?

They avoid storing the entire output sequence, but they can retain local state and referenced objects.

### Are Generators Always Faster?

No. They can reduce allocations and improve time-to-first-result, but generator overhead can make them slower than optimized bulk operations for some workloads.

### What Is `yield from`?

`yield from` delegates iteration to another iterable or generator and can also propagate the delegated generator's return value.

### What Is an Async Generator?

A generator defined with `async def` and `yield`, consumed with `async for`, allowing asynchronous operations between yielded values.

### Can Generators Be Used for Infinite Sequences?

Yes. Their lazy execution makes this possible, but consumption must remain bounded.

### Can a Generator Be Shared Across Threads?

It can be shared only with appropriate synchronization and semantics, but a shared generator is usually a poor concurrency primitive. Use queues or explicit coordination for concurrent consumers.

## Key Takeaways

- Generators provide lazy, incremental execution through `yield`, making them valuable for large datasets, streaming pipelines, files, database cursors, and potentially unbounded sequences.
- A generator avoids materializing the entire output sequence, but it still retains execution state, local variables, referenced objects, and potentially external resources.
- Generator pipelines compose naturally for ETL and backend data flows; use bounded batching when downstream systems such as PostgreSQL or external APIs benefit from bulk operations.
- Generators are single-use, pull-based iterators and should not be confused with durable distributed streaming systems such as Kafka or with concurrency primitives such as queues.
- Production generator designs must account for resource lifetime, exceptions during iteration, cancellation, observability, memory retention, database transaction scope, and streaming behavior across the complete infrastructure path.