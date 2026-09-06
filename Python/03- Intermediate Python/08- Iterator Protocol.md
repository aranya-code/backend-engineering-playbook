# 08- Iterator Protocol

## Overview

The iterator protocol is the Python protocol that defines how objects produce values sequentially.

It is the mechanism behind:

```python
for item in collection:
    ...
```

and powers:

- Lists
- Tuples
- Sets
- Dictionaries
- Files
- Generators
- Generator expressions
- Database cursors
- Custom iterators
- Streaming pipelines
- Many standard-library APIs

The protocol is based primarily on two operations:

```python
iter(obj)
next(iterator)
```

An **iterable** can provide an iterator.

An **iterator** produces values one at a time and maintains its current position.

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

Understanding this protocol is essential for understanding generators, lazy evaluation, comprehensions, `itertools`, file iteration, streaming data, and custom collection APIs.

## Iterable vs Iterator

These concepts are related but not identical.

### Iterable

An iterable is an object that can return an iterator.

Typically:

```python
iter(obj)
```

produces an iterator for the object.

Examples:

```python
numbers = [1, 2, 3]

iterator = iter(numbers)
```

### Iterator

An iterator is an object that produces successive values through:

```python
next(iterator)
```

An iterator implements both:

```python
__iter__()
__next__()
```

The critical distinction is:

```text
Iterable
    |
    +--> can produce an iterator

Iterator
    |
    +--> produces the next value
```

A list is iterable but is not itself an iterator.

A generator object is both iterable and an iterator.

## The Core Protocol

The iterator protocol is expressed through two special methods:

```python
class Iterator:
    def __iter__(self):
        ...

    def __next__(self):
        ...
```

The contract is:

- `__iter__()` returns an iterator.
- `__next__()` returns the next value.
- When no values remain, `__next__()` raises `StopIteration`.

Example:

```python
class Counter:
    def __init__(self, limit: int):
        self.current = 0
        self.limit = limit

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if self.current >= self.limit:
            raise StopIteration

        value = self.current
        self.current += 1
        return value
```

Usage:

```python
counter = Counter(3)

print(next(counter))
print(next(counter))
print(next(counter))
```

Output:

```text
0
1
2
```

The next call raises `StopIteration`.

## Why `__iter__()` Returns `self`

For an iterator, this is normally:

```python
def __iter__(self):
    return self
```

because the iterator is already the object responsible for maintaining iteration state.

This allows:

```python
iterator = iter(counter)
```

to return the same iterator.

```text
Counter iterator
      |
      +--> __iter__()
              |
              v
          same object
```

This is different from reusable containers such as lists, where each call to `iter()` can create a fresh iterator.

## The `for` Loop

Python's `for` statement is built on the iterator protocol.

This:

```python
for item in items:
    process(item)
```

is conceptually equivalent to:

```python
iterator = iter(items)

while True:
    try:
        item = next(iterator)
    except StopIteration:
        break

    process(item)
```

The actual bytecode implementation is more optimized, but this model accurately explains the protocol.

The important sequence is:

```text
for
 |
 v
iter(iterable)
 |
 v
iterator
 |
 v
next()
 |
 v
value
 |
 v
body
 |
 +------> next()
```

When `StopIteration` occurs, the loop terminates normally.

## `iter()` and `__iter__()`

Calling:

```python
iter(obj)
```

invokes the object's iteration protocol.

For a normal iterable:

```python
iterator = iter(obj)
```

eventually resolves to:

```python
obj.__iter__()
```

Example:

```python
numbers = [10, 20, 30]

iterator = iter(numbers)

print(next(iterator))
print(next(iterator))
```

Output:

```text
10
20
```

The list itself remains unchanged.

The iterator contains the state needed to continue traversal.

## `next()` and `__next__()`

Calling:

```python
next(iterator)
```

invokes:

```python
iterator.__next__()
```

Example:

```python
numbers = iter([10, 20, 30])

print(next(numbers))
print(next(numbers))
print(next(numbers))
```

After the third value, the iterator is exhausted.

```python
next(numbers)
```

raises:

```text
StopIteration
```

`next()` also supports a default:

```python
value = next(numbers, None)
```

If the iterator is exhausted, `None` is returned instead of raising `StopIteration`.

This is useful for operations such as finding the first matching value.

## Iterable Lifecycle

A typical iteration lifecycle is:

```text
Object
  |
  v
iter(object)
  |
  v
Iterator
  |
  +--> next() --> item 1
  |
  +--> next() --> item 2
  |
  +--> next() --> item 3
  |
  +--> next() --> StopIteration
```

The iterable and iterator may be separate objects.

For a list:

```text
list
 |
 +--> iterator
       |
       +--> index/state
```

For a generator:

```text
generator function
       |
       v
generator object
       |
       +--> execution state
```

## Reusable Iterables vs Single-Use Iterators

A list is reusable:

```python
numbers = [1, 2, 3]

for number in numbers:
    print(number)

for number in numbers:
    print(number)
```

Both loops see all values.

An iterator is normally single-use:

```python
iterator = iter([1, 2, 3])

list(iterator)
list(iterator)
```

The second result is empty.

This distinction matters when designing APIs.

```text
Reusable iterable
     |
     +--> iter() --> iterator A
     |
     +--> iter() --> iterator B


Single-use iterator
     |
     +--> iter() --> itself
```

## Why Lists Are Iterable but Not Iterators

A list supports:

```python
iter(numbers)
```

but does not normally support:

```python
next(numbers)
```

because the list stores the collection, while a separate list iterator maintains traversal state.

This separation allows:

```python
iterator_a = iter(numbers)
iterator_b = iter(numbers)
```

to progress independently.

```text
List
 |
 +--> Iterator A --> 1 --> 2 --> 3
 |
 +--> Iterator B --> 1 --> 2 --> 3
```

This is one reason containers and iterators have different responsibilities.

## Iterator State

An iterator maintains enough state to know what value comes next.

For a sequence iterator, that may effectively be an index.

For a file iterator, it may depend on the file object's current position.

For a generator, it includes suspended execution state.

For a database cursor, it may involve driver and database-side state.

The protocol itself does not prescribe how state must be stored.

It only defines the behavior exposed through:

```python
__iter__()
__next__()
```

## Custom Iterator

A custom iterator is useful when iteration requires meaningful state or domain-specific logic.

Example:

```python
class PageIterator:
    def __init__(self, fetch_page, page_size: int):
        self.fetch_page = fetch_page
        self.page_size = page_size
        self.offset = 0
        self.buffer = []
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.buffer):
            self.buffer = self.fetch_page(
                offset=self.offset,
                limit=self.page_size,
            )
            self.offset += self.page_size
            self.index = 0

            if not self.buffer:
                raise StopIteration

        value = self.buffer[self.index]
        self.index += 1
        return value
```

This allows callers to consume a paginated backend API as a normal iterator.

However, production pagination requires careful handling of:

- Cursor consistency
- Authentication
- Rate limits
- Network failures
- Retries
- Duplicate pages
- Missing pages
- API changes
- Termination conditions

## Iterator Protocol with Pagination

A backend iterator can hide page boundaries:

```text
API
 |
 +--> Page 1
 |      |
 |      v
 |   Iterator buffer
 |
 +--> Page 2
 |      |
 |      v
 |   Iterator buffer
 |
 +--> Page 3
        |
        v
      done
```

The caller sees:

```python
for user in iter_users():
    process(user)
```

rather than:

```python
page = 1

while True:
    response = fetch_page(page)

    for user in response.items:
        process(user)

    if not response.has_next:
        break

    page += 1
```

This can simplify application code while keeping pagination implementation centralized.

## Iterator Protocol and Generators

Generators automatically implement the iterator protocol.

```python
def generate_users(users):
    for user in users:
        yield user
```

The resulting generator object supports:

```python
iter(generator)
next(generator)
```

and:

```python
iter(generator) is generator
```

is true.

This is why generators are often described as a convenient way to implement iterators without manually writing `__iter__()` and `__next__()`.

## Custom Iterator vs Generator

| Requirement | Generator | Custom Iterator Class |
|---|---|---|
| Simple sequential logic | Excellent | More verbose |
| Stateful iteration | Excellent | Excellent |
| Complex object state | Good | Excellent |
| Multiple iterator-related methods | Limited | Excellent |
| Readability | Usually better | Useful for complex state |
| Serialization | Generally unsuitable for live state | Possible if state is explicit |
| Resource management | Good with care | Explicit control possible |
| Custom iterator API | Limited | Excellent |

Prefer a generator when the iteration logic is straightforward.

Prefer a custom iterator class when the iterator itself is a meaningful stateful abstraction.

## `iter()` with a Sentinel

Python provides a two-argument form:

```python
iter(callable, sentinel)
```

It repeatedly calls the callable until the returned value equals the sentinel.

Example:

```python
from functools import partial


with open("events.log", "rb") as file:
    for chunk in iter(partial(file.read, 8192), b""):
        process_chunk(chunk)
```

The behavior is approximately:

```python
while True:
    value = callable()
    if value == sentinel:
        break

    process(value)
```

This is useful for chunked I/O and other repeated callable operations.

## File Iteration

Files are iterable:

```python
with open("events.log", encoding="utf-8") as file:
    for line in file:
        process(line)
```

The file object implements the iteration protocol.

This allows incremental reading rather than:

```python
file.read()
```

which can load the entire file into memory.

The iterator protocol therefore forms an important foundation for streaming large files.

## Database Cursors

Database cursors commonly expose iterator-like behavior:

```python
cursor.execute(
    "SELECT id, email FROM users"
)

for row in cursor:
    process(row)
```

Whether this means the entire result is buffered or fetched incrementally depends on the database driver and cursor configuration.

The iterator protocol only defines how the application consumes rows.

It does not guarantee server-side streaming.

## API Clients

A custom API client can expose pagination through iteration:

```python
def iter_orders(client):
    cursor = None

    while True:
        response = client.list_orders(cursor=cursor)

        for order in response.items:
            yield order

        cursor = response.next_cursor

        if cursor is None:
            break
```

Usage:

```python
for order in iter_orders(client):
    process_order(order)
```

This provides a clean abstraction over remote pagination.

Production implementations should also define retry, timeout, rate-limit, and cancellation behavior.

## Iterator Protocol and `itertools`

The `itertools` module is built heavily around the iterator protocol.

Examples include:

```python
from itertools import chain, islice

values = chain(
    source_a,
    source_b,
)

first_100 = islice(values, 100)
```

These APIs generally operate lazily.

The architecture is:

```text
Source A ----+
             |
             v
           chain
             |
             v
          islice
             |
             v
          consumer
```

Understanding the iterator protocol makes `itertools` significantly easier to reason about.

## Iterator Composition

Iterators compose because the protocol establishes a common interface.

For example:

```python
def normalize(values):
    for value in values:
        yield value.strip().lower()


def valid(values):
    for value in values:
        if value:
            yield value
```

Then:

```python
pipeline = valid(
    normalize(lines)
)
```

Every stage consumes an iterator and produces an iterable stream.

```text
source
  |
  v
normalize
  |
  v
valid
  |
  v
consumer
```

This common protocol is what makes Python's lazy data-processing style possible.

## Iterator Protocol and Comprehensions

List comprehensions consume iterables:

```python
values = [
    transform(item)
    for item in source
]
```

Generator expressions also consume iterables:

```python
values = (
    transform(item)
    for item in source
)
```

The underlying iteration still follows the iterator protocol.

The difference is what happens to the produced values:

```text
List comprehension
iter(source)
    |
    v
consume all
    |
    v
list


Generator expression
iter(source)
    |
    v
produce on demand
    |
    v
consumer
```

## Iterator Protocol and `map` / `filter`

`map()` and `filter()` also produce lazy iterators.

```python
mapped = map(transform, values)
filtered = filter(predicate, values)
```

They can be consumed using:

```python
for value in filtered:
    ...
```

This is another example of Python building many APIs around the iterator abstraction.

## Iterator Invariants

A well-designed iterator should maintain predictable invariants:

- `iter(iterator) is iterator`.
- `next()` advances the iterator.
- Exhaustion eventually results in `StopIteration`.
- Once exhausted, normal iteration should remain exhausted.
- The iterator should not unexpectedly restart.
- Side effects should be documented.
- Resource ownership should be explicit.

For custom iterators, violating these expectations can produce difficult-to-debug application behavior.

## Exhaustion Semantics

After an iterator is exhausted:

```python
iterator = iter([1])

next(iterator)
```

returns:

```text
1
```

Then:

```python
next(iterator)
```

raises `StopIteration`.

Subsequent calls should continue to indicate exhaustion.

```text
value
  |
  v
exhausted
  |
  +--> StopIteration
  |
  +--> StopIteration
  |
  +--> StopIteration
```

An iterator should not normally restart automatically after exhaustion.

## Stateful Iterators

Stateful iterators can be useful for controlled resource consumption.

Example:

```python
class BatchIterator:
    def __init__(self, source, batch_size: int):
        self.source = iter(source)
        self.batch_size = batch_size

    def __iter__(self):
        return self

    def __next__(self):
        batch = []

        try:
            for _ in range(self.batch_size):
                batch.append(next(self.source))
        except StopIteration:
            if not batch:
                raise

        return batch
```

This turns:

```text
item
item
item
item
...
```

into:

```text
batch
batch
batch
...
```

For production code, `itertools.batched()` is usually preferable when its semantics fit the requirement.

## Resource Ownership

An iterator can represent an active resource:

```text
Iterator
   |
   +--> File
   |
   +--> DB cursor
   |
   +--> HTTP connection
   |
   +--> Socket
```

This makes resource ownership important.

An iterator API should make clear:

- Who opens the resource.
- Who closes the resource.
- What happens on early termination.
- What happens when iteration raises.
- What happens when the consumer abandons the iterator.

A generator with a `finally` block can provide cleanup:

```python
def read_records(connection):
    cursor = connection.cursor()

    try:
        for row in cursor:
            yield row
    finally:
        cursor.close()
```

However, cleanup behavior should still be tested for normal completion and early termination.

## Iterator Protocol and Context Managers

The iterator protocol and context-manager protocol solve different problems.

| Protocol | Primary Responsibility |
|---|---|
| Iterator | Produce values sequentially |
| Context manager | Manage resource lifetime |
| Iterable | Provide an iterator |
| Generator | Convenient iterator implementation |

For example:

```python
with open("events.log", encoding="utf-8") as file:
    for line in file:
        process(line)
```

The file participates in both concepts:

- Context manager controls resource lifetime.
- Iterator provides lines sequentially.

Do not rely on iteration alone to define ownership of external resources.

## Iterator Protocol and Async Iteration

Python has a separate asynchronous iteration protocol.

The key methods are:

```python
__aiter__()
__anext__()
```

Consumption uses:

```python
async for item in source:
    await process(item)
```

Example:

```python
class AsyncCounter:
    def __init__(self, limit: int):
        self.current = 0
        self.limit = limit

    def __aiter__(self):
        return self

    async def __anext__(self) -> int:
        if self.current >= self.limit:
            raise StopAsyncIteration

        value = self.current
        self.current += 1
        return value
```

The asynchronous protocol is analogous to the synchronous protocol:

| Synchronous | Asynchronous |
|---|---|
| `__iter__()` | `__aiter__()` |
| `__next__()` | `__anext__()` |
| `next()` | `anext()` |
| `StopIteration` | `StopAsyncIteration` |
| `for` | `async for` |

## Async Iteration in Backend Systems

Async iterators are useful for:

- Async database clients
- Streaming HTTP responses
- WebSocket messages
- Async Kafka consumers
- Event streams
- Large asynchronous API pagination

Example:

```python
async def iter_events(client):
    cursor = None

    while True:
        response = await client.list_events(cursor=cursor)

        for event in response.items:
            yield event

        cursor = response.next_cursor

        if cursor is None:
            break
```

Consumption:

```python
async for event in iter_events(client):
    await process_event(event)
```

This keeps network I/O asynchronous while maintaining incremental processing.

## Iterator Protocol and Backpressure

The iterator protocol naturally supports pull-based consumption.

The consumer requests the next value:

```text
Consumer
   |
   | next()
   v
Iterator
   |
   | produce one item
   v
Consumer
```

This can provide local backpressure because the producer generally does not need to produce the next item until the consumer requests it.

However, this does not automatically provide:

- Distributed backpressure
- Durable buffering
- Message acknowledgment
- Replay
- Consumer groups
- Cross-process coordination

Those require dedicated systems such as:

- Kafka
- Message queues
- `queue.Queue`
- `asyncio.Queue`

## Iterator Protocol and Concurrency

Iterators generally have mutable traversal state.

Sharing one iterator across concurrent consumers can therefore be unsafe or semantically ambiguous.

Avoid assuming:

```text
Thread A --> next(iterator)
Thread B --> next(iterator)
```

provides useful work distribution.

For concurrent processing, separate iteration from work coordination:

```text
Iterator
   |
   v
Work queue
   |
   +--> Worker A
   +--> Worker B
   +--> Worker C
```

Use appropriate synchronization or queue abstractions when concurrency is required.

## Thread Safety

A custom iterator is not automatically thread-safe.

If its state is:

```python
self.position += 1
```

concurrent access may produce incorrect behavior depending on the surrounding operations and synchronization.

If shared concurrent iteration is required, use a lock:

```python
from threading import Lock


class ThreadSafeIterator:
    def __init__(self, source):
        self._iterator = iter(source)
        self._lock = Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self._lock:
            return next(self._iterator)
```

Even then, locking does not necessarily make the overall processing architecture correct or efficient.

Often a queue-based design is more appropriate.

## Iterator Protocol and Multiprocessing

Live iterators should generally remain inside the process that owns their resources.

Do not assume a database cursor, open file iterator, or network iterator can safely be transferred between processes.

Prefer:

```text
Parent
  |
  v
Serializable task
  |
  v
Worker process
  |
  v
Create iterator locally
  |
  v
Process values
```

For distributed workers, use explicit serializable state such as:

- IDs
- Offsets
- Cursor tokens
- Page numbers
- Checkpoints

rather than attempting to serialize active execution state.

## Performance Characteristics

Iterator-based processing can reduce memory usage because values are produced incrementally.

However, iterator processing still has per-item overhead.

For CPU-intensive workloads:

```python
for item in items:
    transform(item)
```

may be slower than optimized bulk/vectorized operations.

For I/O-heavy workloads, incremental iteration can improve:

- Memory usage
- Time to first result
- Pipeline behavior
- Streaming capability

Always measure using representative workloads.

## Complexity

An iterator does not automatically determine algorithmic complexity.

For example:

```python
for item in items:
    ...
```

is generally O(n) over n items.

But an iterator that performs a database query per item can create:

```text
O(n) application iterations
+
O(n) network/database operations
```

which may become an N+1 performance problem.

Iterator abstraction should therefore not hide expensive per-item side effects.

## Lazy I/O

Some iterators perform I/O only when advanced.

For example:

```python
events = client.iter_events()
```

may not make any network request until:

```python
next(events)
```

or:

```python
for event in events:
    ...
```

This can be desirable but should be documented.

A function that returns an iterator can therefore defer failures such as:

- Connection errors
- Authentication errors
- Timeout errors
- Query errors
- Parsing errors

until iteration begins.

## Error Timing

Consider:

```python
def iter_users():
    return client.iter_users()
```

If the underlying iterator performs network I/O lazily, this may succeed:

```python
iterator = iter_users()
```

and fail later:

```python
next(iterator)
```

This matters for exception handling.

Production code should distinguish:

```text
Iterator creation
       |
       v
Iteration begins
       |
       v
Remote operation
       |
       v
Potential failure
```

Tests should cover errors during both construction and iteration where applicable.

## Iterator API Design

A good iterator API should communicate:

- Whether iteration is lazy.
- Whether it performs I/O.
- Whether it is single-use.
- Whether results are ordered.
- Whether it owns resources.
- Whether iteration can fail midway.
- Whether retries occur.
- Whether values are eventually consistent.
- Whether cancellation is supported.

For example:

```python
def iter_users(
    *,
    page_size: int = 500,
) -> Iterator[User]:
    ...
```

The `iter_` naming convention communicates that the function returns an iterator.

For async APIs:

```python
async def iter_users(...) -> AsyncIterator[User]:
    ...
```

## Type Hints

Modern Python typing provides iterator-specific types.

```python
from collections.abc import Iterator


def iter_user_ids(users: list[User]) -> Iterator[int]:
    for user in users:
        yield user.id
```

For asynchronous iteration:

```python
from collections.abc import AsyncIterator


async def iter_events() -> AsyncIterator[Event]:
    ...
```

For a custom iterator:

```python
from collections.abc import Iterator


class UserIterator(Iterator[User]):
    def __next__(self) -> User:
        ...
```

Using the abstractions from `collections.abc` communicates the intended protocol clearly.

## Iterable Type Hints

If a function only needs to consume values, accept the broadest useful abstraction:

```python
from collections.abc import Iterable


def process_users(users: Iterable[User]) -> None:
    for user in users:
        process_user(user)
```

This accepts:

- Lists
- Tuples
- Sets
- Generators
- Generator expressions
- Custom iterables
- Iterators

Do not unnecessarily require:

```python
list[User]
```

if the function only needs iteration.

This improves composability and allows callers to use lazy sources.

## Iterator Type Hints

Use `Iterator[T]` when the API specifically expects or returns an iterator:

```python
from collections.abc import Iterator


def iter_active_users(
    users: Iterable[User],
) -> Iterator[User]:
    for user in users:
        if user.is_active:
            yield user
```

The distinction communicates lifecycle semantics.

## Iterable vs Iterator in API Design

| API Need | Type |
|---|---|
| Accept anything that can be iterated | `Iterable[T]` |
| Accept a stateful single-pass iterator | `Iterator[T]` |
| Return lazy synchronous values | `Iterator[T]` |
| Return reusable collection | `Sequence[T]` / concrete collection |
| Async iterable input | `AsyncIterable[T]` |
| Async single-pass iterator | `AsyncIterator[T]` |

Prefer the least restrictive interface that satisfies the operation.

## Custom Iterable Objects

Sometimes an object should be reusable and create a new iterator for every traversal.

Example:

```python
class UserCollection:
    def __init__(self, users: list[User]):
        self._users = users

    def __iter__(self):
        return iter(self._users)
```

Now:

```python
users = UserCollection(user_list)

first = iter(users)
second = iter(users)
```

creates independent iterators.

This is appropriate when the object represents a collection rather than a single traversal.

## Iterable with Separate Iterator

A useful architecture is:

```text
Collection
   |
   +--> __iter__()
           |
           v
       Iterator A
           |
           +--> state


Collection
   |
   +--> __iter__()
           |
           v
       Iterator B
           |
           +--> independent state
```

This makes the collection reusable while each traversal remains independent.

## Iterator vs Iterable Design Choice

Ask:

> Does this object represent the data, or does it represent the traversal?

If it represents the data:

```python
class UserCollection:
    def __iter__(self):
        return ...
```

make it an iterable.

If it represents an active traversal:

```python
class UserIterator:
    def __next__(self):
        ...
```

make it an iterator.

This distinction prevents many subtle API-design problems.

## Iterator Protocol and Caching

Do not assume that an iterator supports replay.

For example:

```python
events = client.iter_events()
```

may represent a live stream.

If replay is required, materialize or checkpoint the data explicitly:

```python
events = list(client.iter_events())
```

or use a durable source such as Kafka.

Caching an iterator object is usually not equivalent to caching the underlying data.

## Iterator Protocol and Distributed Systems

The iterator protocol is local to a Python process.

It does not provide:

- Durability
- Fault tolerance
- Replay
- Distributed coordination
- Consumer groups
- Exactly-once semantics
- Cross-process state

For example:

```text
Python Iterator
      |
      v
Local process
```

whereas:

```text
Kafka
  |
  +--> Consumer A
  +--> Consumer B
  +--> Consumer C
```

provides distributed streaming capabilities.

Use the iterator protocol as a local abstraction over distributed sources rather than treating it as a distributed streaming system itself.

## Monitoring Long-Running Iterators

For long-running iterator pipelines, monitor:

- Items processed
- Processing rate
- Error count
- Retry count
- Iterator duration
- Source latency
- Queue lag
- Database cursor duration
- Memory usage
- Last successful progress point

A process that is alive but has stopped advancing an iterator may be unhealthy.

Progress metrics are often more useful than process liveness alone.

## Reliability and Checkpointing

A long-running iterator may fail after partially processing a dataset.

For example:

```text
Items 1-10,000
       |
       v
success

Item 10,001
       |
       v
failure
```

Restarting from the beginning may duplicate side effects.

For critical pipelines, maintain explicit progress state:

```text
Iterator
   |
   v
Process batch
   |
   v
Persist checkpoint
   |
   v
Continue
```

Checkpoint state might include:

- Last processed ID
- Database key
- Kafka offset
- API cursor
- Page token
- Timestamp watermark

The iterator protocol itself provides no checkpointing mechanism.

## Security Considerations

Iterator-based processing can handle untrusted streams safely only if resource consumption is bounded.

Consider:

- Maximum records
- Maximum record size
- Maximum processing time
- Request deadlines
- Rate limits
- Authorization
- Input validation
- Output filtering
- Memory bounds

A lazy iterator prevents immediate full materialization, but it does not prevent a malicious source from sending unlimited data over time.

## Testing Custom Iterators

A custom iterator should be tested against protocol expectations.

```python
def test_counter():
    iterator = Counter(3)

    assert iter(iterator) is iterator
    assert next(iterator) == 0
    assert next(iterator) == 1
    assert next(iterator) == 2

    with pytest.raises(StopIteration):
        next(iterator)
```

Also test:

- Empty input
- Single item
- Multiple items
- Exhaustion
- Repeated `next()` after exhaustion
- Exceptions
- Resource cleanup
- Early termination
- Invalid configuration
- Concurrent use if supported

## Testing Iterables

For reusable iterables, verify that separate iterations are independent:

```python
def test_collection_is_reusable():
    users = UserCollection(
        [
            User(id=1),
            User(id=2),
        ]
    )

    assert list(users) == [User(id=1), User(id=2)]
    assert list(users) == [User(id=1), User(id=2)]
```

The important property is that `__iter__()` produces a fresh traversal.

## Common Mistakes

### Implementing `__next__()` Without `__iter__()`

A class may support manual `next()` but fail to behave correctly in a `for` loop.

An iterator should normally implement both:

```python
__iter__()
__next__()
```

### Returning a New Iterator from an Iterator's `__iter__()`

For an iterator:

```python
def __iter__(self):
    return self
```

is the expected behavior.

Returning a new iterator changes its semantics.

### Returning `None` at Exhaustion

An iterator must signal exhaustion with:

```python
raise StopIteration
```

Returning `None` makes `None` indistinguishable from a legitimate value.

### Restarting Unexpectedly

An exhausted iterator should not silently restart.

### Confusing Iterable and Iterator

A reusable collection and a single-use traversal have different semantics.

### Assuming Iteration Means Streaming

The source may already be fully materialized.

### Hiding Network I/O

Returning an iterator can defer network failures until iteration.

Document lazy I/O behavior.

### Keeping Resources Open Indefinitely

A slow consumer can keep a cursor, file, or connection alive.

### Sharing Iterators Concurrently

Iterator state is mutable and usually not designed for concurrent access.

### Performing Expensive Work Per Item

Iteration can hide N+1 queries or repeated network requests.

## Production Pitfalls

| Pitfall | Impact | Mitigation |
|---|---|---|
| Full materialization before iteration | High memory usage | Preserve lazy source behavior |
| Iterator reused after exhaustion | Missing data | Create a fresh iterator |
| Iterator treated as reusable | Unexpected empty results | Document single-pass semantics |
| DB cursor held too long | Connection/resource exhaustion | Bound batches and lifetime |
| Network call per item | High latency / cost | Batch or bulk operations |
| No checkpointing | Duplicate processing after failure | Persist progress |
| Unbounded stream | Resource exhaustion | Limits, deadlines, backpressure |
| Shared iterator across threads | Race conditions | Synchronization or queues |
| Hidden lazy exceptions | Unexpected failure location | Document and test iteration-time errors |
| Iterator transferred between processes | Invalid resource state | Recreate iterator in worker |
| No progress metrics | Stalled pipeline unnoticed | Measure throughput and lag |
| Confusing local iteration with distributed streaming | Incorrect architecture | Use Kafka/queues for distributed semantics |

## Senior Engineering Heuristics

The iterator protocol is one of Python's most important abstraction boundaries.

A strong backend API should generally expose the appropriate level of abstraction:

```text
Need to consume anything iterable?
            |
            v
        Iterable[T]

Need a single-pass traversal?
            |
            v
        Iterator[T]

Need reusable indexed data?
            |
            v
       Sequence[T]

Need async streaming?
            |
            v
     AsyncIterator[T]

Need durable distributed streaming?
            |
            v
     Kafka / Queue / Broker
```

When designing custom iteration, explicitly reason about:

- Ownership
- Lifecycle
- Reusability
- Exhaustion
- Error timing
- Lazy I/O
- Memory usage
- Concurrency
- Checkpointing
- Backpressure
- Observability

The iterator protocol should simplify the caller's data flow without hiding operational behavior that materially affects reliability.

## Decision Guide

| Requirement | Recommended Abstraction |
|---|---|
| Reusable in-memory collection | Iterable / Sequence |
| One-pass lazy values | Iterator |
| Simple lazy logic | Generator |
| Complex lazy logic | Generator function |
| Stateful custom traversal | Iterator class |
| Simple transformation | Generator expression |
| Async streaming | Async iterator / async generator |
| Large file | File iterator |
| Large DB result | Driver-supported cursor + iterator |
| Paginated API | Iterator / generator wrapper |
| Concurrent processing | Queue / executor |
| Durable stream | Kafka / message broker |
| Distributed checkpointing | Explicit durable state |
| Resource lifetime | Context manager |
| Random access | Sequence / indexed structure |

## Interview Traps

### What Is the Iterator Protocol?

It is the Python protocol that defines sequential value production through `__iter__()` and `__next__()`.

### What Is an Iterable?

An object that can provide an iterator, normally through:

```python
iter(obj)
```

### What Is an Iterator?

An object that produces values through:

```python
next(iterator)
```

and raises `StopIteration` when exhausted.

### What Is the Difference Between Iterable and Iterator?

An iterable can produce an iterator.

An iterator represents the active traversal and maintains iteration state.

### Why Does an Iterator Return Itself from `__iter__()`?

Because the iterator already represents the traversal state.

```python
iter(iterator) is iterator
```

is the normal invariant.

### How Does a `for` Loop Work?

Conceptually:

```python
iterator = iter(iterable)

while True:
    try:
        value = next(iterator)
    except StopIteration:
        break

    process(value)
```

### Why Does `StopIteration` Exist?

It provides the protocol-level signal that an iterator has no more values.

### Are All Iterables Iterators?

No.

A list is iterable but not an iterator.

A generator object is both.

### Can an Iterator Be Reused?

Normally no. Iterators are typically single-pass.

### Can an Iterable Be Iterated Multiple Times?

Usually yes, if each call to `__iter__()` returns a fresh iterator.

### Why Are Generators Iterators?

Generator objects implement the iterator protocol automatically.

### Does the Iterator Protocol Guarantee Streaming?

No.

An iterator defines sequential access semantics. The underlying source may still be fully materialized.

### Does the Iterator Protocol Provide Concurrency?

No.

Concurrent processing requires separate concurrency primitives or execution models.

### What Is `iter(callable, sentinel)`?

It creates an iterator that repeatedly calls a callable until the returned value equals the sentinel.

### What Is the Async Iterator Protocol?

It uses:

```python
__aiter__()
__anext__()
```

and is consumed with:

```python
async for
```

### What Should You Use for a Reusable Custom Collection?

Usually an iterable object whose `__iter__()` creates a fresh iterator.

### What Should You Use for Complex Stateful Iteration?

A generator function is often sufficient, but a custom iterator class is appropriate when explicit iterator state and behavior form a meaningful abstraction.

## Key Takeaways

- Python's iterator protocol is based on `__iter__()` and `__next__()`, with `StopIteration` signaling exhaustion.
- An iterable provides an iterator, while an iterator represents a stateful, usually single-pass traversal; generators are convenient implementations of the iterator protocol.
- The protocol powers `for` loops, generators, generator expressions, `itertools`, file iteration, database cursors, and streaming API abstractions.
- Production iterator design must account for resource ownership, lazy I/O, exhaustion, error timing, memory usage, concurrency, checkpointing, and observability.
- The iterator protocol provides local sequential access semantics, not distributed durability, concurrency, replay, or fault tolerance; use queues, Kafka, databases, and other dedicated systems when those guarantees are required.