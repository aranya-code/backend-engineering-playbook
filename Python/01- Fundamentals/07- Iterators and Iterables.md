# 07- Iterators and Iterables

## Overview

Iteration is one of Python's core execution models. `for` loops, comprehensions, generators, `map()`, `filter()`, and many standard-library APIs depend on the iterator protocol.

The key distinction is:

- An **iterable** can provide an iterator.
- An **iterator** produces values one at a time and remembers its current position.

This distinction matters in backend engineering because large datasets, database cursors, files, API streams, Kafka consumers, and asynchronous data sources are often processed incrementally rather than loaded entirely into memory.

A useful mental model is:

```text
Iterable
   |
   | iter()
   v
Iterator
   |
   | next()
   v
Value
   |
   | next()
   v
Value
   |
   | next()
   v
StopIteration
```

Understanding this protocol helps explain how Python executes `for` loops, why generators are memory-efficient, why iterators are usually single-use, and how to build custom streaming abstractions.

## Iterable vs Iterator

An **iterable** is an object that can return an iterator.

Examples include:

```python
list
tuple
dict
set
str
bytes
range
file objects
generators
```

An **iterator** is an object that implements the iterator protocol:

```python
__iter__()
__next__()
```

The simplest conceptual distinction is:

| Concept | Meaning | Typical Behavior |
|---|---|---|
| Iterable | Can be iterated over | Produces an iterator |
| Iterator | Produces values sequentially | Maintains iteration state |
| Generator | Iterator created using generator syntax | Produces values lazily |

A list is iterable:

```python
users = ["alice", "bob", "charlie"]

iterator = iter(users)
```

The resulting `iterator` is an iterator.

```python
next(iterator)
# "alice"

next(iterator)
# "bob"
```

## The Iterator Protocol

Python's iteration model is based on two methods.

```python
__iter__()
__next__()
```

An iterator's `__iter__()` method returns itself.

Its `__next__()` method returns the next value or raises `StopIteration` when exhausted.

Conceptually:

```python
iterator = iter(iterable)

while True:
    try:
        item = next(iterator)
    except StopIteration:
        break

    process(item)
```

This is approximately what a `for` loop does internally.

## How a `for` Loop Works

Consider:

```python
for user in users:
    process(user)
```

Python conceptually performs:

```python
iterator = iter(users)

while True:
    try:
        user = next(iterator)
    except StopIteration:
        break

    process(user)
```

This is why understanding `iter()` and `next()` explains a large portion of Python's iteration behavior.

The actual bytecode and interpreter implementation contain additional details, but this model is accurate for understanding application behavior.

## `iter()`

The built-in `iter()` obtains an iterator from an iterable.

```python
users = ["alice", "bob"]

iterator = iter(users)
```

You can inspect the result:

```python
print(type(iterator))
```

A list typically produces a list iterator.

```python
next(iterator)
# "alice"
```

`iter()` is useful when explicit control over iteration state is required.

Most application code can rely on `for` instead.

## `next()`

`next()` retrieves the next item from an iterator.

```python
iterator = iter(["a", "b"])

print(next(iterator))
print(next(iterator))
```

After the final value:

```python
next(iterator)
```

raises:

```text
StopIteration
```

A default can be supplied:

```python
value = next(iterator, None)
```

In this form, `None` is returned instead of raising `StopIteration` when the iterator is exhausted.

## StopIteration

`StopIteration` signals normal iterator exhaustion.

For example:

```python
iterator = iter([1, 2])

next(iterator)
# 1

next(iterator)
# 2

next(iterator)
# StopIteration
```

A `for` loop catches this internally and terminates normally.

Application code generally should not manually catch `StopIteration` when a `for` loop expresses the operation more clearly.

## Iterable Detection

An object is typically iterable if it implements `__iter__()` or supports Python's legacy sequence iteration mechanism through `__getitem__()` starting at index zero.

For normal application code, the important contract is:

```python
iter(value)
```

If this succeeds, the object is iterable.

Example:

```python
def consume(items):
    for item in items:
        process(item)
```

This function accepts any suitable iterable rather than requiring a specific concrete collection such as `list`.

## Iterator Detection

An iterator should support:

```python
iter(iterator) is iterator
```

For example:

```python
iterator = iter([1, 2, 3])

assert iter(iterator) is iterator
```

This property distinguishes an iterator from many reusable iterables.

## Reusable Iterables vs Single-Use Iterators

A list can usually be iterated multiple times:

```python
users = ["alice", "bob"]

list(users)
list(users)
```

An iterator is generally consumed as it is traversed:

```python
iterator = iter(users)

list(iterator)
# ["alice", "bob"]

list(iterator)
# []
```

This distinction is critical when passing iterators between functions.

Consider:

```python
def validate(items):
    for item in items:
        validate_item(item)


def persist(items):
    for item in items:
        save(item)
```

If the same iterator is passed to both:

```python
items = iter(load_items())

validate(items)
persist(items)
```

`persist()` may receive no values because `validate()` consumed the iterator.

If multiple passes are required, materialize the data or obtain independent iterators from a reusable iterable.

## Lazy Evaluation

Iterators commonly support lazy evaluation.

Instead of producing all values immediately:

```python
results = [transform(item) for item in items]
```

a generator can produce values as they are consumed:

```python
results = (transform(item) for item in items)
```

This can reduce memory usage.

The transformation happens during iteration rather than at generator creation time.

```text
Generator created
      |
      v
No values transformed yet
      |
      v
next()
      |
      v
Transform one item
      |
      v
Return value
```

Lazy processing is particularly useful for large or potentially unbounded streams.

## Memory Efficiency

Consider one million records.

An eager list:

```python
records = [transform(record) for record in source]
```

requires memory for the resulting collection.

A generator:

```python
records = (transform(record) for record in source)
```

holds the generator state and produces results incrementally.

This is valuable for:

- Large files
- Database exports
- S3 object processing
- ETL pipelines
- Kafka consumers
- Large API responses
- Batch processing

However, laziness does not eliminate memory usage entirely. Individual objects, buffers, caches, and downstream consumers can still retain data.

## Iterator State

An iterator maintains state describing where it currently is in its sequence.

For a list iterator:

```text
List:
["a", "b", "c"]

Iterator state:
    ^
    |
 current position
```

Each `next()` advances the state.

This state is why the same iterator cannot normally be restarted from the beginning.

A custom iterator may maintain more complex state:

```text
current page
current record
retry state
cursor
buffer
```

This makes iterators useful for streaming abstractions.

## Custom Iterator Classes

A class can implement the iterator protocol directly.

```python
class BatchIterator:
    def __init__(self, start: int, stop: int):
        self.current = start
        self.stop = stop

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if self.current >= self.stop:
            raise StopIteration

        value = self.current
        self.current += 1
        return value
```

Usage:

```python
for value in BatchIterator(0, 3):
    print(value)
```

Output:

```text
0
1
2
```

The class stores iteration state in instance attributes.

## Why Use a Custom Iterator?

Custom iterator classes are useful when iteration requires explicit state and behavior.

Examples include:

- Pagination
- Cursor traversal
- Tree traversal
- Stateful parsers
- Batch readers
- Streaming adapters
- Protocol-specific consumers

However, they are often more verbose than generator functions.

Use a custom class when the iterator has meaningful state or behavior that benefits from an explicit object.

## Generator Functions

Generator functions provide a simpler way to create iterators.

A function containing `yield` becomes a generator function:

```python
def count(start: int, stop: int):
    current = start

    while current < stop:
        yield current
        current += 1
```

Usage:

```python
for value in count(0, 3):
    print(value)
```

A generator function automatically implements the iterator protocol.

## `yield` Semantics

When execution reaches `yield`:

1. The current value is produced.
2. The generator pauses.
3. Its execution state is retained.
4. The next iteration resumes from that point.

Example:

```python
def values():
    print("before first")
    yield 1

    print("before second")
    yield 2
```

Creating the generator does not execute the body:

```python
generator = values()
```

Execution begins when the generator is advanced:

```python
next(generator)
```

This lazy execution model is central to streaming.

## Generator vs Custom Iterator

| Approach | Advantages | Limitations |
|---|---|---|
| Generator function | Concise, readable, automatic state management | Less suitable for complex object behavior |
| Custom iterator class | Explicit state and behavior | More boilerplate |
| List | Simple, reusable, indexable | Eager memory allocation |
| Generator expression | Concise lazy transformation | Usually less suitable for complex logic |

Prefer generator functions when iteration logic can naturally be expressed as sequential control flow.

## `iter()` With a Callable and Sentinel

Python also supports:

```python
iter(callable, sentinel)
```

This repeatedly calls the callable until the returned value equals the sentinel.

Example:

```python
from functools import partial

with open("events.log", "rb") as file:
    for block in iter(partial(file.read, 64 * 1024), b""):
        process_block(block)
```

This is useful for reading streams in chunks without loading the entire resource into memory.

The pattern is:

```text
call()
  |
  v
value == sentinel?
  |
  +-- yes --> stop
  |
  +-- no ---> process value
                |
                +--> call again
```

## File Iterators

File objects are iterable.

```python
with open("events.log", encoding="utf-8") as file:
    for line in file:
        process_line(line)
```

This is preferable to:

```python
with open("events.log", encoding="utf-8") as file:
    lines = file.readlines()

for line in lines:
    process_line(line)
```

for large files because iteration allows lines to be processed incrementally.

This pattern is especially useful in:

- Log processing
- ETL
- Import jobs
- Data migration
- Batch processing

## Database Cursors

Database drivers commonly expose cursor-like iteration.

Conceptually:

```python
with connection.cursor() as cursor:
    cursor.execute(query)

    for row in cursor:
        process_row(row)
```

The exact buffering behavior depends on the database driver and cursor configuration.

Important production considerations include:

- Whether rows are fetched eagerly or incrementally
- Server-side vs client-side cursors
- Batch size
- Transaction duration
- Connection lifetime
- Memory consumption

An iterator abstraction does not automatically guarantee constant memory or server-side streaming.

Always understand the underlying driver's behavior.

## Pagination Iterators

Iterators are useful for hiding pagination mechanics behind a simple interface.

For example:

```python
def iter_users(client, page_size: int = 100):
    page = 1

    while True:
        response = client.get_users(
            page=page,
            page_size=page_size,
        )

        users = response["users"]

        if not users:
            return

        yield from users

        if len(users) < page_size:
            return

        page += 1
```

The caller can simply write:

```python
for user in iter_users(client):
    process_user(user)
```

The pagination implementation remains hidden behind the iterable interface.

## API Streaming and Pagination

Consider a service consuming a paginated REST API:

```text
Application
    |
    v
GET /users?page=1
    |
    v
process page
    |
    v
GET /users?page=2
    |
    v
process page
    |
    v
GET /users?page=3
    |
    v
...
```

An iterator can encapsulate this state.

However, production implementations must also consider:

- Rate limits
- Retries
- Request timeouts
- Pagination token expiration
- Duplicate records
- Missing records
- API consistency
- Authentication refresh
- Cancellation

The iterator abstraction should not hide operationally important failure behavior.

## `yield from`

`yield from` delegates iteration to another iterable.

Instead of:

```python
def all_items(groups):
    for group in groups:
        for item in group:
            yield item
```

you can write:

```python
def all_items(groups):
    for group in groups:
        yield from group
```

This is useful for composing generators and flattening nested streams.

It can also delegate generator return values internally, although that advanced behavior is less common in ordinary backend code.

## Generator Expressions

Generator expressions provide compact lazy iteration.

```python
user_ids = (
    user.id
    for user in users
    if user.is_active
)
```

They work well with functions that consume iterables:

```python
total = sum(
    order.total
    for order in orders
)
```

This avoids constructing an intermediate list:

```python
total = sum(
    [order.total for order in orders]
)
```

The generator expression is generally preferable when the intermediate list is not needed elsewhere.

## Built-in Functions and Iterators

Many Python built-ins consume iterables.

Examples:

```python
sum(values)
```

```python
any(condition(item) for item in items)
```

```python
all(condition(item) for item in items)
```

```python
max(values)
```

```python
min(values)
```

```python
sorted(values)
```

Some consume lazily while others materialize data.

### Important Distinction

```python
sorted(iterator)
```

must materialize the values because sorting requires access to the complete dataset.

By contrast:

```python
any(predicate(item) for item in iterator)
```

can stop as soon as a truthy result is found.

## Short-Circuiting With Iterators

Iterator-consuming functions can avoid unnecessary work.

```python
has_admin = any(
    permission == "admin"
    for permission in permissions
)
```

Once `"admin"` is found, `any()` stops consuming the iterator.

Similarly:

```python
all(
    permission.is_valid
    for permission in permissions
)
```

stops at the first false result.

This is useful for performance when the condition can often be decided early.

## `map()` and `filter()`

In modern Python, `map()` and `filter()` return iterators.

```python
user_ids = map(
    lambda user: user.id,
    users,
)
```

```python
active_users = filter(
    lambda user: user.is_active,
    users,
)
```

They can be consumed lazily.

For straightforward transformations, comprehensions are often clearer:

```python
user_ids = [user.id for user in users]
```

For lazy processing:

```python
user_ids = (user.id for user in users)
```

The choice should prioritize readability and memory behavior.

## `zip()` and Iteration

`zip()` combines iterables lazily.

```python
for user, profile in zip(users, profiles):
    synchronize(user, profile)
```

With modern Python, `strict=True` can detect mismatched lengths:

```python
for user, profile in zip(
    users,
    profiles,
    strict=True,
):
    synchronize(user, profile)
```

This is valuable when equal-length inputs are an invariant.

Without `strict=True`, `zip()` stops when the shortest iterable is exhausted, which can silently discard unmatched values.

## `enumerate()`

`enumerate()` produces an iterator containing indexes and values.

```python
for index, item in enumerate(items):
    process(index, item)
```

It is preferable to manually maintaining a counter:

```python
index = 0

for item in items:
    process(index, item)
    index += 1
```

An optional starting value is supported:

```python
for index, item in enumerate(items, start=1):
    ...
```

## `reversed()` and Iteration

`reversed()` can provide reverse iteration for objects supporting the appropriate protocol.

```python
for item in reversed(items):
    process(item)
```

Not every iterable supports `reversed()`.

A general iterator may not know its length or how to move backward.

This is another reason to distinguish an iterable from an arbitrary iterator.

## `sorted()` vs Lazy Iteration

Sorting requires materialization.

```python
sorted(iterator)
```

consumes the iterator and returns a list.

For large datasets, sorting may therefore require substantial memory.

If the data must be sorted at scale, consider pushing the operation to an appropriate system:

- PostgreSQL `ORDER BY`
- Distributed processing
- External sorting
- Streaming algorithms for specialized cases

Do not assume that using an iterator automatically makes an entire pipeline memory-efficient.

## Iterator Consumption

Iterator consumption is often implicit.

For example:

```python
iterator = iter(items)

first = next(iterator)

remaining = list(iterator)
```

After calling `next()` once, the first element is no longer available from that iterator.

Similarly:

```python
iterator = iter(items)

if any(is_valid(item) for item in iterator):
    ...
```

may consume some or all of the iterator.

Do not reuse the iterator afterward unless its consumption behavior is explicitly understood.

## Iterator Pipelines

Iterators can be composed into processing pipelines.

```text
Input Stream
     |
     v
Filter
     |
     v
Transform
     |
     v
Validate
     |
     v
Persist
```

Example:

```python
records = read_records(source)

valid_records = (
    record
    for record in records
    if is_valid(record)
)

normalized_records = (
    normalize(record)
    for record in valid_records
)

for record in normalized_records:
    persist(record)
```

Each stage can operate incrementally.

This architecture is useful for ETL and large-data workloads.

## Backpressure

A lazy iterator does not automatically provide backpressure.

Suppose:

```text
Producer -> Iterator -> Consumer
```

If the producer can generate values faster than the consumer can process them, buffering can still grow depending on the architecture.

For synchronous generators, the producer typically advances only when the consumer requests another value, naturally coupling production and consumption.

This is useful because:

```text
consumer calls next()
        |
        v
producer generates one item
        |
        v
consumer processes it
```

For asynchronous queues, Kafka consumers, worker pools, or buffered pipelines, explicit flow-control mechanisms may be required.

## Iterators and Kafka

Kafka consumers are naturally stream-oriented.

A backend consumer may process messages incrementally:

```python
for message in consumer:
    process_message(message)
```

The application should avoid materializing an unbounded stream:

```python
messages = list(consumer)
```

Production Kafka consumers additionally need to manage:

- Consumer group coordination
- Offset commits
- Rebalancing
- Batch sizes
- Retry behavior
- Dead-letter handling
- Backpressure
- Graceful shutdown

The iterator interface simplifies consumption syntax but does not eliminate distributed-systems concerns.

## Iterators and Celery

Celery tasks frequently process batches.

Instead of creating one enormous task containing millions of records, applications can process bounded batches:

```text
Large Dataset
     |
     v
Batch 1 -> Task
Batch 2 -> Task
Batch 3 -> Task
...
```

Iterators can help generate batches:

```python
def batched(items, size: int):
    iterator = iter(items)

    while batch := list(islice(iterator, size)):
        yield batch
```

The resulting batches can be submitted to workers incrementally.

The exact worker architecture should account for retry semantics, idempotency, task visibility, and queue capacity.

## Iterator Thread Safety

Iterators are generally not automatically thread-safe.

Sharing one mutable iterator across multiple threads can create race conditions.

Avoid:

```python
iterator = iter(items)

# Multiple threads consume the same iterator.
```

unless synchronization and ownership semantics are explicitly designed.

Prefer assigning independent iterators or partitions to workers.

For async code, the same principle applies: an iterator should not be assumed to support concurrent consumption safely.

## Async Iterables and Async Iterators

Asynchronous iteration has a separate protocol.

An async iterable can provide an async iterator through:

```python
__aiter__()
```

An async iterator produces values through:

```python
__anext__()
```

Values are consumed with:

```python
async for item in source:
    await process(item)
```

Conceptually:

```text
Async Iterable
      |
    __aiter__()
      |
      v
Async Iterator
      |
  __anext__()
      |
      v
 await value
      |
      v
 repeat
```

This is important for asynchronous APIs, streaming HTTP responses, database drivers, and other I/O-bound workloads.

## Async Generator Functions

An async generator uses both `async def` and `yield`.

```python
async def stream_users(client):
    page = 1

    while True:
        users = await client.get_users(page=page)

        if not users:
            return

        for user in users:
            yield user

        page += 1
```

Consumption:

```python
async for user in stream_users(client):
    await process_user(user)
```

This combines lazy iteration with asynchronous I/O.

## Sync vs Async Iteration

| Feature | Synchronous | Asynchronous |
|---|---|---|
| Iterable protocol | `__iter__()` | `__aiter__()` |
| Iterator method | `__next__()` | `__anext__()` |
| Consumption | `for` | `async for` |
| Generator | `yield` | `async def` + `yield` |
| Typical use | CPU/local I/O | Async network/I/O |
| Completion signal | `StopIteration` | `StopAsyncIteration` |

Do not mix the two protocols accidentally.

## Iterators and Resource Management

An iterator may depend on an external resource:

```text
Iterator
   |
   +--> File
   +--> Database cursor
   +--> HTTP connection
   +--> Socket
```

Resource ownership must be explicit.

For example:

```python
with open("events.log", encoding="utf-8") as file:
    for line in file:
        process_line(line)
```

The `with` block owns the file lifetime.

Avoid designing an iterator whose underlying resource remains open indefinitely because the consumer forgot to exhaust it.

For database cursors and network streams, explicit context management is equally important.

## Failure Handling in Iterators

Failures can occur while values are being produced.

```python
def stream_users(client):
    page = 1

    while True:
        response = client.get_users(page=page)

        for user in response["users"]:
            yield user

        if not response["has_next"]:
            return

        page += 1
```

A network failure may happen on a later iteration rather than when the generator is created.

This means:

```python
stream = stream_users(client)
```

does not necessarily perform the network operation.

The failure may occur here:

```python
next(stream)
```

or later during a `for` loop.

Consumers should therefore understand that lazy APIs defer both work and failures.

## Retry Semantics

Retrying iterator operations requires care.

Suppose an API page is fetched, some records are yielded, and the connection fails.

Automatically retrying the page may produce duplicate records.

```text
Page 1
  |
  +--> records 1-50 yielded
  |
  +--> failure
  |
  +--> retry page 1
          |
          +--> records 1-50 again
```

Production streaming systems should define:

- Delivery semantics
- Cursor/checkpoint behavior
- Idempotency
- Deduplication
- Retry boundaries

Iterator abstractions should not obscure these distributed-systems properties.

## Performance Considerations

Iteration itself is usually efficient, but performance depends on the underlying operation.

Potential bottlenecks include:

- Expensive transformations
- Object allocation
- Database access
- Network requests
- Serialization
- Python-level loops over very large datasets
- Excessive function calls
- Poor batching

For example:

```python
results = [
    repository.get(item.id)
    for item in items
]
```

is not made efficient merely because it uses a comprehension.

The database access pattern dominates.

Prefer bulk retrieval:

```python
results = repository.get_by_ids(
    [item.id for item in items]
)
```

when the repository supports it.

## Memory Considerations

Iterator-based designs can reduce peak memory usage, but memory can still grow if downstream code materializes or buffers the values.

For example:

```python
stream = generate_records()

records = list(stream)
```

eliminates the memory benefit of lazy generation.

Similarly:

```python
sorted(stream)
```

must materialize the values to perform sorting.

A production pipeline should identify where materialization occurs.

## Security Considerations

Iterators processing untrusted input should still enforce:

- Maximum record sizes
- Maximum stream duration
- Resource limits
- Validation
- Timeouts
- Authentication
- Authorization

A lazy stream can otherwise become an unbounded resource consumer.

For example, an HTTP endpoint that streams arbitrary client-controlled data should not assume that lazy processing alone protects the service from resource exhaustion.

Use appropriate:

- Request limits
- Timeouts
- Rate limits
- Quotas
- Cancellation
- Bounded buffers

## Observability

Long-running iterator pipelines should expose useful operational metrics.

Depending on the workload:

- Records processed
- Records failed
- Processing latency
- Batch size
- Throughput
- Retry count
- Current offset/cursor
- Queue lag
- Stream duration

Avoid logging every item in high-throughput systems.

Prefer structured logs and aggregated metrics.

For example:

```python
logger.info(
    "batch_processed",
    extra={
        "batch_size": len(batch),
        "duration_ms": duration_ms,
    },
)
```

The exact logging API depends on the application's logging stack.

## Testing Iterators

Test both values and consumption behavior.

A generator:

```python
def active_users(users):
    for user in users:
        if user.is_active:
            yield user
```

can be tested with:

```python
def test_active_users():
    users = [
        User(id=1, is_active=True),
        User(id=2, is_active=False),
        User(id=3, is_active=True),
    ]

    assert list(active_users(users)) == [
        users[0],
        users[2],
    ]
```

Also test:

- Empty input
- Exhaustion
- Multiple consumers
- Exceptions during iteration
- Large inputs
- Resource cleanup
- Pagination boundaries
- Retry behavior where applicable

For asynchronous iterators, test cancellation and asynchronous failures as well.

## Common Mistakes

### Confusing Iterable and Iterator

Not every iterable is an iterator.

```python
items = [1, 2, 3]

next(items)
```

fails because the list itself is not an iterator.

Use:

```python
next(iter(items))
```

### Reusing an Exhausted Iterator

```python
iterator = iter(items)

list(iterator)
list(iterator)
```

The second traversal is empty.

Obtain a new iterator from the original reusable iterable when another pass is required.

### Assuming Generators Execute Immediately

This:

```python
stream = generate_records()
```

does not execute the generator body to completion.

Work begins as the generator is advanced.

### Materializing Everything

Avoid:

```python
records = list(stream)
```

for unbounded or very large streams unless materialization is intentional and capacity has been considered.

### Hiding I/O Behind Lazy APIs

A function that looks like a local iterator may actually perform network requests during iteration.

Document important external behavior.

### Ignoring Resource Lifetime

Do not allow files, sockets, or database cursors to remain open indefinitely because a consumer partially consumes an iterator.

### Assuming Thread Safety

Iterators with mutable state are not automatically safe for concurrent consumers.

### Using Iterators to Solve the Wrong Problem

Generators reduce memory pressure, but they do not automatically fix:

- Slow SQL
- N+1 queries
- Network latency
- CPU-heavy transformations
- Poor batching
- Unbounded concurrency

Optimize the entire data flow.

## Interview Traps

### What Is the Difference Between an Iterable and an Iterator?

An iterable can provide an iterator.

An iterator produces values and maintains iteration state.

```python
iter(iterable)
```

returns an iterator.

### What Methods Define the Iterator Protocol?

The key methods are:

```python
__iter__()
__next__()
```

For an iterator:

```python
iter(iterator) is iterator
```

### Why Is a Generator an Iterator?

A generator automatically implements the iterator protocol and maintains its suspended execution state between `yield` operations.

### Why Does `for` Work With Custom Objects?

Because Python obtains an iterator using `iter()` and repeatedly calls `next()` until `StopIteration`.

### Why Are Generators Memory Efficient?

They generally produce one value at a time rather than materializing the entire result collection.

This reduces peak memory usage when the consumer also processes values incrementally.

### Can an Iterator Be Reused?

Usually not.

Iterators are generally stateful and single-pass.

Reusable iterables such as lists can usually produce fresh iterators for each traversal.

### Does Lazy Evaluation Guarantee Constant Memory?

No.

The iterator itself may be small, but the pipeline can still materialize data, buffer values, retain references, or accumulate state.

### Does a Generator Execute When Created?

No.

A generator function's body begins executing when the generator is advanced.

### What Is the Difference Between `yield` and `return`?

`return` terminates the current function.

`yield` suspends a generator and produces a value while preserving its execution state for later resumption.

### Does `async for` Use the Same Protocol?

No.

Asynchronous iteration uses `__aiter__()` and `__anext__()`, with `StopAsyncIteration` signaling exhaustion.

## Production Checklist

When designing an iterator-based API, evaluate:

| Concern | Question |
|---|---|
| Data volume | Can the complete dataset fit safely in memory? |
| Reusability | Does the consumer need multiple passes? |
| Laziness | Should values be produced only when requested? |
| I/O | Does iteration trigger database or network operations? |
| Resource lifetime | Who owns and closes the underlying resource? |
| Errors | Can failures occur during iteration? |
| Retries | Can retrying produce duplicates? |
| Backpressure | Can the consumer control production rate? |
| Concurrency | Can multiple workers consume safely? |
| Cancellation | Can long-running processing stop cleanly? |
| Observability | Can progress and failures be measured? |
| Security | Are input size and processing limits enforced? |

## Best Practices

- Understand the distinction between iterables and iterators.
- Prefer `for` loops unless explicit iterator control is required.
- Use generators for naturally lazy, sequential processing.
- Use generator expressions when a lazy transformation is simple.
- Avoid materializing large or unbounded streams unnecessarily.
- Treat iterators as generally single-pass.
- Make resource ownership explicit when iteration depends on files, cursors, or network connections.
- Do not assume iterator-based code is automatically memory-efficient end to end.
- Avoid performing expensive per-item database or network operations when bulk operations are available.
- Use `zip(..., strict=True)` when equal-length inputs are an invariant.
- Use `any()` and `all()` with generator expressions when short-circuiting is useful.
- Use explicit loops when error handling, retries, logging, or complex control flow becomes important.
- Understand whether lazy iteration can trigger deferred I/O or exceptions.
- Bound concurrency and buffering in production pipelines.
- Consider idempotency and checkpointing when iterators consume distributed streams.
- Test exhaustion, partial consumption, failures, and resource cleanup.
- Use asynchronous iteration for genuinely asynchronous data sources rather than assuming `async` is required for every iterator.

## Key Takeaways

- An iterable can produce an iterator, while an iterator maintains state and produces values through `__next__()` until `StopIteration`.
- Python's `for` loops, comprehensions, generators, `zip()`, `enumerate()`, and many built-ins rely on the iterator protocol.
- Generators and lazy iterators can reduce peak memory usage and enable streaming, but they do not automatically solve I/O, buffering, database, or concurrency problems.
- Production iterator pipelines must account for resource ownership, failures, retries, backpressure, concurrency, observability, and idempotency.
- Senior-level iterator design focuses on the complete data flow: where values originate, when work occurs, how much state is retained, and where materialization or external I/O happens.