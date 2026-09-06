# 16- Coding Problems

## Overview

Python coding problems are useful for evaluating more than syntax. Strong interview performance requires recognizing the underlying pattern, selecting appropriate data structures, reasoning about complexity, handling edge cases, and communicating trade-offs.

For backend-oriented interviews, coding problems should also reinforce practical Python skills:

- dictionaries and sets;
- lists, tuples, and deques;
- stacks and queues;
- sorting and searching;
- recursion and iteration;
- generators;
- heaps;
- graphs and trees;
- sliding windows;
- two pointers;
- intervals;
- dynamic programming;
- concurrency-aware reasoning;
- input validation and error handling.

The goal is not to memorize solutions. The goal is to recognize recurring problem structures.

A useful problem-solving workflow is:

```text
Understand the problem
        │
        ▼
Clarify constraints
        │
        ▼
Identify pattern
        │
        ▼
Choose data structure
        │
        ▼
Design algorithm
        │
        ▼
State complexity
        │
        ▼
Implement
        │
        ▼
Test edge cases
        │
        ▼
Review trade-offs
```

---

## Interview Problem-Solving Framework

Before writing code, establish:

### Inputs

Determine:

- type;
- size;
- whether values are unique;
- whether data is sorted;
- whether input can be empty;
- whether input can contain invalid values.

### Outputs

Determine:

- exact return type;
- ordering requirements;
- whether duplicates matter;
- whether mutation is allowed.

### Constraints

Constraints often determine the algorithm.

For example:

```text
n <= 20
```

may permit exponential solutions.

```text
n <= 1,000,000
```

usually requires approximately O(n) or O(n log n) reasoning.

### Edge Cases

Always consider:

- empty input;
- one element;
- duplicate values;
- negative values;
- already sorted input;
- reverse-sorted input;
- very large input;
- missing values;
- invalid input where relevant.

---

## Complexity First

Before implementing, estimate:

```text
Time Complexity
Space Complexity
```

For example:

```python
def contains_duplicate(values: list[int]) -> bool:
    return len(values) != len(set(values))
```

Typical complexity:

```text
Time:  O(n)
Space: O(n)
```

The important interview skill is being able to explain why.

---

## Pattern Recognition

Many coding problems reduce to a small number of patterns.

| Pattern | Typical data structure | Common problem |
|---|---|---|
| Hash lookup | `dict`, `set` | Two Sum |
| Two pointers | List/string | Pair/triplet problems |
| Sliding window | `dict`, `set`, counters | Longest substring |
| Stack | `list` | Parentheses, monotonic stack |
| Queue | `deque` | BFS |
| Heap | `heapq` | Top K, scheduling |
| Binary search | Sorted sequence | Search/boundary |
| Intervals | Sorted list | Merge intervals |
| DFS | Recursion/stack | Trees/graphs |
| BFS | `deque` | Shortest unweighted path |
| Backtracking | Recursion | Permutations/combinations |
| Dynamic programming | Array/dict | Optimization/counting |
| Prefix sums | Array | Range queries |
| Union-Find | Parent/rank arrays | Connectivity |

Recognizing the pattern is often more valuable than memorizing a particular problem.

---

## Hash Maps and Sets

Hash-based lookup is one of the most important interview patterns.

Average-case dictionary/set operations are approximately O(1).

### Two Sum

Given a list of numbers and a target, return indices of two values whose sum equals the target.

```python
def two_sum(numbers: list[int], target: int) -> tuple[int, int] | None:
    seen: dict[int, int] = {}

    for index, value in enumerate(numbers):
        complement = target - value

        if complement in seen:
            return seen[complement], index

        seen[value] = index

    return None
```

Complexity:

```text
Time:  O(n)
Space: O(n)
```

The key insight is storing previously observed values rather than repeatedly searching the list.

---

## Frequency Counting

Use `Counter` when the problem is about frequencies.

```python
from collections import Counter


def first_unique_character(value: str) -> str | None:
    counts = Counter(value)

    for character in value:
        if counts[character] == 1:
            return character

    return None
```

Complexity:

```text
Time:  O(n)
Space: O(k)
```

where `k` is the number of distinct characters.

---

## Anagram Detection

A frequency map provides a direct solution:

```python
from collections import Counter


def are_anagrams(first: str, second: str) -> bool:
    return Counter(first) == Counter(second)
```

Sorting is another approach:

```python
def are_anagrams(first: str, second: str) -> bool:
    return sorted(first) == sorted(second)
```

The trade-off is:

| Approach | Time | Space | Advantage |
|---|---:|---:|---|
| `Counter` | O(n) | O(k) | Linear-time counting |
| Sorting | O(n log n) | O(n) | Simple and general |

---

## Two Pointers

Two pointers are useful when processing ordered sequences.

### Valid Palindrome

```python
def is_palindrome(value: str) -> bool:
    left = 0
    right = len(value) - 1

    while left < right:
        while left < right and not value[left].isalnum():
            left += 1

        while left < right and not value[right].isalnum():
            right -= 1

        if value[left].lower() != value[right].lower():
            return False

        left += 1
        right -= 1

    return True
```

Complexity:

```text
Time:  O(n)
Space: O(1)
```

The key idea is processing the sequence from both ends without constructing unnecessary intermediate data.

---

## Two Sum on a Sorted Array

When the input is sorted, two pointers can replace a hash map.

```python
def two_sum_sorted(
    numbers: list[int],
    target: int,
) -> tuple[int, int] | None:
    left = 0
    right = len(numbers) - 1

    while left < right:
        total = numbers[left] + numbers[right]

        if total == target:
            return left, right

        if total < target:
            left += 1
        else:
            right -= 1

    return None
```

Complexity:

```text
Time:  O(n)
Space: O(1)
```

Always ask whether the input's ordering provides an opportunity to simplify the algorithm.

---

## Sliding Window

Sliding windows are useful when the problem asks about contiguous ranges.

### Longest Substring Without Repeating Characters

```python
def longest_unique_substring(value: str) -> int:
    last_seen: dict[str, int] = {}
    left = 0
    longest = 0

    for right, character in enumerate(value):
        previous = last_seen.get(character)

        if previous is not None and previous >= left:
            left = previous + 1

        last_seen[character] = right
        longest = max(longest, right - left + 1)

    return longest
```

Complexity:

```text
Time:  O(n)
Space: O(k)
```

The window represents the current valid range.

```text
left                 right
  │                     │
  ▼                     ▼
[a b c d e f g h i j k]
  └──── current window ─┘
```

---

## Fixed-Size Sliding Window

For a fixed window size:

```python
def maximum_window_sum(values: list[int], size: int) -> int:
    if size <= 0 or size > len(values):
        raise ValueError("invalid window size")

    current = sum(values[:size])
    maximum = current

    for index in range(size, len(values)):
        current += values[index]
        current -= values[index - size]
        maximum = max(maximum, current)

    return maximum
```

This avoids recomputing every window from scratch.

Complexity:

```text
Time:  O(n)
Space: O(1)
```

---

## Prefix Sums

Prefix sums are useful for repeated range-sum queries.

```python
def build_prefix_sums(values: list[int]) -> list[int]:
    prefix = [0]

    for value in values:
        prefix.append(prefix[-1] + value)

    return prefix


def range_sum(prefix: list[int], left: int, right: int) -> int:
    return prefix[right + 1] - prefix[left]
```

After O(n) preprocessing, each range query is O(1).

This pattern is useful when many queries operate on the same immutable dataset.

---

## Stack Problems

Python's `list` is usually the appropriate stack.

### Valid Parentheses

```python
def is_valid_parentheses(value: str) -> bool:
    matching = {
        ")": "(",
        "]": "[",
        "}": "{",
    }

    stack: list[str] = []

    for character in value:
        if character in matching:
            if not stack or stack.pop() != matching[character]:
                return False
        else:
            stack.append(character)

    return not stack
```

Complexity:

```text
Time:  O(n)
Space: O(n)
```

---

## Monotonic Stack

A monotonic stack maintains elements in increasing or decreasing order.

Common problems include:

- next greater element;
- daily temperatures;
- largest rectangle in histogram;
- stock span.

Example:

```python
def next_greater(values: list[int]) -> list[int]:
    result = [-1] * len(values)
    stack: list[int] = []

    for index, value in enumerate(values):
        while stack and values[stack[-1]] < value:
            previous = stack.pop()
            result[previous] = value

        stack.append(index)

    return result
```

The important insight is that each element is pushed and popped at most once.

Typical complexity:

```text
Time:  O(n)
Space: O(n)
```

---

## Queues

Use `collections.deque` for efficient FIFO operations.

Avoid:

```python
queue = []

queue.pop(0)
```

because removing from the front of a list is O(n).

Prefer:

```python
from collections import deque

queue = deque()

queue.append(item)
item = queue.popleft()
```

Both end operations are approximately O(1).

---

## Binary Search

Binary search requires an appropriate ordering property.

Basic implementation:

```python
def binary_search(values: list[int], target: int) -> int:
    left = 0
    right = len(values) - 1

    while left <= right:
        middle = left + (right - left) // 2

        if values[middle] == target:
            return middle

        if values[middle] < target:
            left = middle + 1
        else:
            right = middle - 1

    return -1
```

Complexity:

```text
Time:  O(log n)
Space: O(1)
```

---

## Binary Search on the Answer

A more advanced pattern uses binary search over a range of possible answers rather than directly searching an array.

The structure is:

```text
Possible answer
      │
      ▼
Feasibility check
      │
      ├── feasible
      └── infeasible
```

If feasibility is monotonic:

```text
False False False False True True True
                         ▲
                    first valid
```

binary search can find the boundary efficiently.

This pattern appears in:

- minimum capacity problems;
- scheduling;
- allocation;
- shipping workloads;
- rate/capacity problems.

---

## Sorting

Python's `sorted()` and `list.sort()` use Timsort.

```python
ordered = sorted(
    users,
    key=lambda user: user.created_at,
)
```

Typical complexity:

```text
Time:  O(n log n)
Space: O(n)
```

Timsort can exploit existing ordering in real-world data.

Use sorting when:

- ordering is required;
- sorting simplifies the algorithm;
- input size makes O(n log n) acceptable.

---

## Custom Sort Keys

Prefer `key=` over comparator-style logic.

```python
users.sort(
    key=lambda user: (
        user.is_active is False,
        user.created_at,
    )
)
```

The key function should express the ordering clearly.

Avoid repeatedly transforming values inside nested comparisons.

---

## Intervals

Interval problems usually become easier after sorting by start time.

### Merge Intervals

```python
def merge_intervals(
    intervals: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    if not intervals:
        return []

    intervals = sorted(intervals)
    merged = [intervals[0]]

    for start, end in intervals[1:]:
        previous_start, previous_end = merged[-1]

        if start <= previous_end:
            merged[-1] = (
                previous_start,
                max(previous_end, end),
            )
        else:
            merged.append((start, end))

    return merged
```

Complexity:

```text
Time:  O(n log n)
Space: O(n)
```

The sorting step dominates the complexity.

---

## Heaps

Use `heapq` when you repeatedly need the smallest or largest priority item.

Python's `heapq` implements a min-heap.

```python
import heapq


def smallest_k(values: list[int], k: int) -> list[int]:
    if k < 0:
        raise ValueError("k must be non-negative")

    return heapq.nsmallest(k, values)
```

For repeated dynamic operations:

```python
heap: list[int] = []

heapq.heappush(heap, value)
smallest = heapq.heappop(heap)
```

Typical operations:

```text
heappush → O(log n)
heappop  → O(log n)
peek     → O(1)
heapify  → O(n)
```

---

## Top K Elements

For large `n` and small `k`, a heap can avoid sorting everything.

```python
import heapq


def top_k(values: list[int], k: int) -> list[int]:
    if k <= 0:
        return []

    if k >= len(values):
        return sorted(values, reverse=True)

    heap: list[int] = []

    for value in values:
        if len(heap) < k:
            heapq.heappush(heap, value)
        elif value > heap[0]:
            heapq.heapreplace(heap, value)

    return sorted(heap, reverse=True)
```

Complexity:

```text
Time:  O(n log k)
Space: O(k)
```

This is preferable to O(n log n) sorting when `k` is much smaller than `n`.

---

## Trees

Tree problems commonly use:

- recursion;
- DFS;
- BFS;
- stacks;
- queues.

A recursive DFS:

```python
def max_depth(node: TreeNode | None) -> int:
    if node is None:
        return 0

    return 1 + max(
        max_depth(node.left),
        max_depth(node.right),
    )
```

Complexity:

```text
Time:  O(n)
Space: O(h)
```

where `h` is tree height due to recursion depth.

---

## Recursive vs Iterative DFS

Recursive:

```text
Node
 │
 ├── left
 │    └── ...
 │
 └── right
      └── ...
```

Iterative:

```python
def max_depth(node: TreeNode | None) -> int:
    if node is None:
        return 0

    stack = [(node, 1)]
    maximum = 0

    while stack:
        current, depth = stack.pop()
        maximum = max(maximum, depth)

        if current.left:
            stack.append((current.left, depth + 1))

        if current.right:
            stack.append((current.right, depth + 1))

    return maximum
```

For very deep structures, iterative traversal avoids Python recursion-depth limitations.

---

## Breadth-First Search

BFS processes nodes level by level.

```python
from collections import deque


def tree_levels(root: TreeNode | None) -> list[list[int]]:
    if root is None:
        return []

    result: list[list[int]] = []
    queue = deque([root])

    while queue:
        level: list[int] = []

        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.value)

            if node.left:
                queue.append(node.left)

            if node.right:
                queue.append(node.right)

        result.append(level)

    return result
```

BFS is particularly useful for shortest paths in unweighted graphs.

---

## Graph Representation

An adjacency list is usually efficient for sparse graphs.

```python
graph: dict[str, list[str]] = {
    "api": ["users", "orders"],
    "users": ["database"],
    "orders": ["database", "queue"],
    "database": [],
    "queue": [],
}
```

An adjacency matrix consumes O(V²) memory and is appropriate only when the graph is sufficiently dense or constant-time edge lookup is important.

---

## Graph DFS

```python
def reachable(
    graph: dict[str, list[str]],
    start: str,
    target: str,
) -> bool:
    visited: set[str] = set()
    stack = [start]

    while stack:
        node = stack.pop()

        if node == target:
            return True

        if node in visited:
            continue

        visited.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                stack.append(neighbor)

    return False
```

Always track visited nodes when cycles are possible.

---

## Graph BFS

```python
from collections import deque


def shortest_hops(
    graph: dict[str, list[str]],
    start: str,
    target: str,
) -> int | None:
    queue = deque([(start, 0)])
    visited = {start}

    while queue:
        node, distance = queue.popleft()

        if node == target:
            return distance

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))

    return None
```

For an unweighted graph, BFS finds the shortest path in terms of edge count.

---

## Topological Sorting

Topological sorting applies to directed acyclic graphs.

Typical backend examples:

- job dependencies;
- migration dependencies;
- build dependencies;
- workflow execution.

Kahn's algorithm uses indegrees:

```python
from collections import deque


def topological_sort(
    graph: dict[str, list[str]],
) -> list[str]:
    indegree = {node: 0 for node in graph}

    for neighbors in graph.values():
        for neighbor in neighbors:
            indegree.setdefault(neighbor, 0)
            indegree[neighbor] += 1

    queue = deque(
        node for node, degree in indegree.items()
        if degree == 0
    )

    order: list[str] = []

    while queue:
        node = queue.popleft()
        order.append(node)

        for neighbor in graph.get(node, []):
            indegree[neighbor] -= 1

            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(indegree):
        raise ValueError("graph contains a cycle")

    return order
```

Complexity:

```text
Time:  O(V + E)
Space: O(V)
```

---

## Backtracking

Backtracking explores possible choices and reverses them when a path cannot produce a valid solution.

Common problems:

- permutations;
- combinations;
- subsets;
- N-Queens;
- constraint satisfaction.

Example:

```python
def permutations(values: list[int]) -> list[list[int]]:
    result: list[list[int]] = []
    path: list[int] = []
    used = [False] * len(values)

    def backtrack() -> None:
        if len(path) == len(values):
            result.append(path.copy())
            return

        for index, value in enumerate(values):
            if used[index]:
                continue

            used[index] = True
            path.append(value)

            backtrack()

            path.pop()
            used[index] = False

    backtrack()
    return result
```

Backtracking often has exponential complexity because it explores a large search space.

The key optimization is pruning impossible branches early.

---

## Dynamic Programming

Dynamic programming is appropriate when a problem has:

- overlapping subproblems;
- optimal substructure.

Two common forms are:

- top-down memoization;
- bottom-up tabulation.

### Memoization

```python
from functools import cache


@cache
def fibonacci(n: int) -> int:
    if n < 2:
        return n

    return fibonacci(n - 1) + fibonacci(n - 2)
```

This changes the naive recursive Fibonacci algorithm from exponential time to approximately O(n).

---

## Bottom-Up Dynamic Programming

```python
def fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")

    if n < 2:
        return n

    previous = 0
    current = 1

    for _ in range(2, n + 1):
        previous, current = current, previous + current

    return current
```

This version uses:

```text
Time:  O(n)
Space: O(1)
```

The important optimization is recognizing which historical states are actually required.

---

## 0/1 Knapsack Pattern

The classic knapsack problem asks for the best value under a capacity constraint.

The state is commonly:

```text
dp[capacity] = best value achievable
```

The interview focus is usually less about memorizing the implementation and more about identifying:

- state;
- transition;
- base case;
- iteration order.

Dynamic programming becomes much easier when the state has a precise definition.

---

## Greedy Algorithms

Greedy algorithms make the locally optimal choice at each step.

Examples include:

- interval scheduling;
- minimum spanning tree algorithms;
- Huffman coding;
- some coin-change variants.

Greedy solutions require proof or a known property showing that local choices lead to a globally optimal solution.

Do not assume:

> "Taking the largest available value first must be optimal."

That assumption is frequently false.

---

## Recursion

Recursion is useful for:

- tree traversal;
- divide-and-conquer;
- backtracking;
- recursive parsing.

Python has a recursion-depth limit, so recursion should not be used blindly for arbitrarily deep input.

For production code processing untrusted or deeply nested data, iterative approaches may be safer.

---

## String Problems

Common patterns include:

- frequency maps;
- two pointers;
- sliding windows;
- stacks;
- parsing.

Avoid unnecessary repeated concatenation:

```python
result = ""

for value in values:
    result += value
```

For many fragments, use:

```python
result = "".join(values)
```

This avoids repeatedly constructing larger intermediate strings.

---

## Parsing Problems

For structured input, separate parsing from business logic.

```python
def parse_record(line: str) -> tuple[str, int]:
    name, raw_count = line.split(",", maxsplit=1)
    return name.strip(), int(raw_count)
```

Production parsing should also define behavior for malformed input.

Do not silently accept corrupted data when correctness matters.

---

## Linked Lists

Linked-list problems test pointer/reference manipulation.

The fast/slow pointer pattern is useful for:

- cycle detection;
- finding the middle;
- detecting intersections.

### Cycle Detection

```python
def has_cycle(head: Node | None) -> bool:
    slow = head
    fast = head

    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next

        if slow is fast:
            return True

    return False
```

The use of `is` is intentional because cycle detection concerns object identity, not value equality.

---

## LRU Cache

An LRU cache combines:

- hash-based lookup;
- ordered eviction.

Python provides an implementation through `functools.lru_cache` for function-result caching:

```python
from functools import lru_cache


@lru_cache(maxsize=10_000)
def get_exchange_rate(currency: str) -> Decimal:
    return load_exchange_rate(currency)
```

Interview implementations often combine a dictionary with a doubly linked list.

The production lesson is more important than the implementation:

> Cache design requires explicit decisions about capacity, expiration, invalidation, consistency, and scope.

---

## Intervals and Scheduling

Scheduling problems often involve:

- sorting by start/end time;
- heaps;
- greedy selection.

A common transformation is:

```text
Unordered intervals
        │
        ▼
Sort by boundary
        │
        ▼
Process sequentially
        │
        ▼
Maintain active state
```

For meeting-room problems, a min-heap of active end times is often useful.

---

## Data Structure Selection

| Requirement | Preferred structure |
|---|---|
| Fast key lookup | `dict` |
| Unique membership | `set` |
| Ordered sequence | `list` |
| FIFO | `deque` |
| LIFO | `list` |
| Priority queue | `heapq` |
| Immutable sequence | `tuple` |
| Immutable set | `frozenset` |
| Frequency counting | `Counter` |
| Missing-key defaults | `defaultdict` |
| Graph adjacency | `dict` of lists/sets |

Choosing the correct structure often determines the complexity of the solution.

---

## Python-Specific Interview Topics

Coding interviews may test Python semantics alongside algorithms.

Be prepared for:

- mutable default arguments;
- shallow vs deep copy;
- `is` vs `==`;
- dictionary/set hashing;
- closures;
- generators;
- decorators;
- iterators;
- context managers;
- exception handling;
- comprehensions;
- `*args` and `**kwargs`;
- positional-only and keyword-only parameters;
- `async`/`await`;
- dataclasses;
- type hints.

Example mutable-default trap:

```python
def append_item(item, values=[]):
    values.append(item)
    return values
```

The default list is created once when the function is defined.

Prefer:

```python
def append_item(
    item: str,
    values: list[str] | None = None,
) -> list[str]:
    if values is None:
        values = []

    values.append(item)
    return values
```

---

## Backend-Oriented Coding Problems

Interview preparation should include problems that resemble real backend work.

Useful categories include:

### Rate Limiting

Implement a fixed-window or token-bucket limiter.

Relevant concepts:

- timestamps;
- counters;
- deques;
- Redis;
- atomic operations;
- distributed state.

### TTL Cache

Implement:

```text
key → value + expiration
```

Consider:

- lazy expiration;
- cleanup;
- maximum size;
- concurrency.

### Log Aggregation

Given events:

```text
timestamp
service
level
request_id
```

calculate:

- error rate;
- counts per service;
- top error types;
- latency percentiles.

### Request Deduplication

Determine whether an incoming request has already been processed.

Relevant concepts:

- hash keys;
- idempotency;
- expiration;
- persistence;
- distributed coordination.

### Task Scheduler

Given jobs and dependencies, determine execution order.

Relevant concepts:

- graphs;
- topological sorting;
- queues;
- concurrency;
- failure handling.

---

## Backend Coding Example: Rate Limiter

A simple in-process fixed-window limiter:

```python
from time import monotonic


class RateLimiter:
    def __init__(self, limit: int, window_seconds: float):
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window must be positive")

        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, tuple[int, float]] = {}

    def allow(self, key: str) -> bool:
        now = monotonic()
        count, window_start = self._requests.get(key, (0, now))

        if now - window_start >= self.window_seconds:
            count = 0
            window_start = now

        if count >= self.limit:
            self._requests[key] = count, window_start
            return False

        self._requests[key] = count + 1, window_start
        return True
```

This is useful as an interview exercise, but it is not sufficient for a distributed production deployment.

Production concerns include:

- multiple application instances;
- process-local state;
- atomic updates;
- memory growth;
- clock behavior;
- Redis availability;
- eviction;
- rate-limit semantics.

---

## Backend Coding Example: TTL Cache

A basic in-memory TTL cache:

```python
from time import monotonic
from typing import Generic, TypeVar


T = TypeVar("T")


class TTLCache(Generic[T]):
    def __init__(self, ttl_seconds: float):
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

        self.ttl_seconds = ttl_seconds
        self._items: dict[str, tuple[T, float]] = {}

    def get(self, key: str) -> T | None:
        item = self._items.get(key)

        if item is None:
            return None

        value, expires_at = item

        if monotonic() >= expires_at:
            del self._items[key]
            return None

        return value

    def set(self, key: str, value: T) -> None:
        self._items[key] = (
            value,
            monotonic() + self.ttl_seconds,
        )
```

Interview discussion should include why this implementation is incomplete:

- no maximum capacity;
- no background cleanup;
- no thread-safety;
- no distributed sharing;
- no persistence;
- `None` cannot distinguish a missing value from a cached `None`.

---

## Backend Coding Example: Log Aggregation

```python
from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogEvent:
    service: str
    level: str


def error_counts(events: list[LogEvent]) -> Counter[str]:
    return Counter(
        event.service
        for event in events
        if event.level == "ERROR"
    )
```

This demonstrates a common backend data-processing pattern:

```text
Events
  │
  ▼
Filter
  │
  ▼
Group
  │
  ▼
Aggregate
```

For very large datasets, stream events rather than materializing all events in memory.

---

## Testing Coding Solutions

Every algorithm should be tested against representative cases.

For:

```python
def two_sum(numbers, target):
    ...
```

test:

```text
Normal case
No solution
Duplicate values
Negative values
Zero
Empty input
Single element
```

Example:

```python
@pytest.mark.parametrize(
    ("numbers", "target", "expected"),
    [
        ([2, 7, 11, 15], 9, (0, 1)),
        ([3, 3], 6, (0, 1)),
        ([1, 2], 5, None),
        ([-3, 4, 1], 1, (0, 1)),
    ],
)
def test_two_sum(numbers, target, expected):
    assert two_sum(numbers, target) == expected
```

Tests should validate the contract, not merely demonstrate one successful example.

---

## Edge-Case Strategy

A useful checklist is:

```text
Empty
Single
Smallest valid
Largest valid
Duplicate
Negative
Zero
Already sorted
Reverse sorted
All identical
No solution
Multiple valid solutions
Malformed input
```

Not every problem supports every category, but systematically considering them reduces missed cases.

---

## Interview Communication

While coding, explain:

1. the brute-force approach;
2. its complexity;
3. why it may be insufficient;
4. the optimization;
5. the selected data structure;
6. the invariant;
7. complexity of the final solution;
8. important edge cases.

For example:

```text
Brute force:
For each value, scan the remaining values.
Time: O(n²)

Optimization:
Store previously seen values in a set.
Membership is average O(1).

Final:
Single pass.
Time: O(n)
Space: O(n)
```

This demonstrates engineering reasoning rather than memorization.

---

## Invariants

An invariant is a property that remains true throughout an algorithm.

For a sliding window:

```text
The current window always contains no duplicate characters.
```

For BFS:

```text
Nodes are processed in nondecreasing distance from the source.
```

For a two-pointer algorithm:

```text
All discarded regions have already been proven unable to contain
the required solution.
```

Stating the invariant makes correctness easier to reason about.

---

## Brute Force First

Brute force is often useful as the first correct solution.

Example:

```text
O(n²)
```

Then ask:

> What repeated work can be removed?

Possible transformations:

```text
Repeated lookup → hash map
Repeated range calculation → prefix sum
Repeated overlapping subproblem → dynamic programming
Repeated minimum selection → heap
Ordered search → binary search
Contiguous constraint → sliding window
```

This is a reliable path from correctness to optimization.

---

## Common Complexity Improvements

| From | To | Typical technique |
|---|---|---|
| O(n²) | O(n) | Hash map/set |
| O(n²) | O(n log n) | Sorting + scan |
| O(n²) | O(n) | Two pointers |
| O(n²) | O(n) | Sliding window |
| O(n) per query | O(1) | Prefix sums |
| O(n log n) | O(n log k) | Heap |
| Exponential recursion | O(n) / O(n²) | Memoization |
| Repeated graph traversal | O(V + E) | DFS/BFS |

The correct transformation depends on constraints and problem structure.

---

## Common Mistakes

### Starting to Code Immediately

Without clarifying constraints, the selected algorithm may be fundamentally wrong.

### Ignoring Input Constraints

An O(n²) algorithm may be acceptable for 100 elements and unusable for 1,000,000.

### Choosing the Wrong Collection

Using a list for repeated membership checks can turn an O(n) algorithm into O(n²).

### Forgetting Duplicate Values

Many hash-map and two-pointer solutions fail because duplicate handling was not considered.

### Using `pop(0)`

This is O(n). Use `deque.popleft()` for queue behavior.

### Sorting Unnecessarily

Sorting can increase O(n) solutions to O(n log n) when ordering is not required.

### Overusing Recursion

Deep input can exceed Python's recursion limit.

### Ignoring Memory

An O(n) time solution using several large auxiliary structures may become memory-bound.

### Overfitting to the Example

An algorithm that works for the provided sample may fail on empty input, duplicates, negative values, or large data.

---

## Production Considerations

Interview algorithms often operate on clean in-memory data. Production systems have additional constraints.

A real service must consider:

- malformed input;
- untrusted input sizes;
- memory limits;
- timeouts;
- concurrency;
- cancellation;
- database access;
- network latency;
- partial failures;
- observability.

For example, an O(n) algorithm is not necessarily safe if `n` comes directly from an unbounded API request.

Set limits:

```python
MAX_ITEMS = 10_000

if len(items) > MAX_ITEMS:
    raise ValueError("too many items")
```

Algorithmic complexity and operational limits must be considered together.

---

## Security Considerations

Algorithm selection can affect security.

Potential issues include:

- unbounded input causing excessive CPU;
- unbounded collections causing memory exhaustion;
- pathological parsing;
- expensive regular expressions;
- algorithmic complexity attacks;
- hash-table abuse in some environments.

For public APIs:

```text
Untrusted input
      │
      ▼
Validate size and shape
      │
      ▼
Bound computation
      │
      ▼
Execute algorithm
```

Never assume that interview-style inputs will remain small or well-formed in production.

---

## Coding Problem Categories

A practical interview preparation matrix:

| Category | Core patterns |
|---|---|
| Arrays | Hashing, two pointers, sliding window |
| Strings | Hashing, parsing, windows |
| Linked lists | Pointers, fast/slow |
| Stacks | Parsing, monotonic stack |
| Queues | BFS, scheduling |
| Hash tables | Lookup, counting, deduplication |
| Sorting | Custom keys, intervals |
| Binary search | Boundaries, answer search |
| Heaps | Top K, scheduling |
| Trees | DFS, BFS, recursion |
| Graphs | DFS, BFS, topological sort |
| Backtracking | Search and pruning |
| Dynamic programming | State and transitions |
| Greedy | Local optimal decisions |
| Intervals | Sorting and merging |
| Prefix sums | Range queries |
| Design problems | Caches, rate limiters, schedulers |

---

## Recommended Practice Progression

A useful progression is:

```text
Python fundamentals
       │
       ▼
Arrays + Strings
       │
       ▼
Hash Maps + Sets
       │
       ▼
Two Pointers + Sliding Window
       │
       ▼
Stacks + Queues
       │
       ▼
Binary Search + Sorting
       │
       ▼
Heaps + Intervals
       │
       ▼
Trees + Graphs
       │
       ▼
Backtracking
       │
       ▼
Dynamic Programming
       │
       ▼
Backend-oriented coding
       │
       ▼
Timed interview practice
```

The progression matters because later patterns depend on fluency with earlier data structures.

---

## Problem-Solving Checklist

Before submitting a solution:

### Correctness

- [ ] Does it handle empty input?
- [ ] Does it handle the smallest valid input?
- [ ] Are duplicates handled?
- [ ] Are negative values handled where relevant?
- [ ] Are boundary conditions correct?
- [ ] Is the return contract correct?

### Complexity

- [ ] What is the time complexity?
- [ ] What is the space complexity?
- [ ] Which operation dominates?
- [ ] Can the algorithm be improved?
- [ ] Does the solution fit the input constraints?

### Python

- [ ] Is the chosen collection appropriate?
- [ ] Is `deque` used for FIFO?
- [ ] Is `set`/`dict` used for repeated membership/lookup?
- [ ] Are unnecessary copies avoided?
- [ ] Is recursion depth safe?
- [ ] Are built-ins used appropriately?

### Production

- [ ] Can input size be bounded?
- [ ] Can malformed input be rejected?
- [ ] Can the operation exhaust memory?
- [ ] Can it consume excessive CPU?
- [ ] Is behavior deterministic?
- [ ] Would concurrency affect correctness?

---

## Interview Traps

### Why Is a Dictionary Lookup O(1)?

It is average-case O(1) because Python dictionaries use hash-table-based lookup. Worst-case behavior can differ, and the implementation details should not be described as an unconditional guarantee.

### Why Use a Set Instead of a List?

For repeated membership checks, a set typically provides average O(1) membership versus O(n) for a list.

### Why Use `deque` Instead of a List for BFS?

`deque.popleft()` is O(1), while `list.pop(0)` is O(n).

### When Is Sorting Better Than Hashing?

Sorting may be preferable when:

- the input is already sorted;
- ordering is needed anyway;
- memory usage matters;
- the problem naturally becomes a linear scan after sorting.

### Is O(n) Always Better Than O(n log n)?

Not necessarily.

Constant factors, memory behavior, implementation quality, input size, and operational constraints all matter.

### Why Is `is` Used in Linked-List Cycle Detection?

Because the algorithm needs to determine whether two references point to the exact same object, not whether two objects have equal values.

---

## Senior-Level Coding Discussion

### How Would You Adapt an Algorithm for a 10 Million Element Dataset?

First determine whether the data can fit in memory.

Possible approaches:

- streaming;
- chunking;
- external sorting;
- database-side aggregation;
- partitioning;
- generators;
- distributed processing where justified.

Do not blindly convert a list into another list if memory is already constrained.

### How Would You Turn an In-Memory Algorithm Into a Distributed Service?

Identify state and ownership:

```text
Client
  │
  ▼
API
  │
  ├── Stateless computation
  │
  ├── Redis / shared state
  │
  ├── PostgreSQL / durable state
  │
  └── Kafka / asynchronous processing
```

Then consider:

- partitioning;
- consistency;
- idempotency;
- retries;
- ordering;
- failure recovery;
- serialization;
- network overhead.

### When Would You Move Computation to PostgreSQL?

Move filtering, aggregation, joining, and other relational operations to PostgreSQL when the database can perform them efficiently and doing so reduces data transfer and Python-side processing.

The decision should be based on query plans, database capacity, data locality, and workload characteristics.

### When Would You Use Redis Instead of Python Memory?

Use Redis when state needs to be:

- shared across application workers;
- externally accessible;
- short-lived;
- coordinated across instances.

A Python dictionary is appropriate for process-local state but is not a distributed cache.

### When Would You Use Kafka Instead of a Python Queue?

Use Kafka when you need durable, scalable event streaming with independent consumers and replay/retention semantics.

An in-process Python queue is suitable for local coordination but disappears when the process terminates.

---

## Final Interview Strategy

For coding interviews, optimize for a repeatable process:

```text
Read
  │
  ▼
Clarify
  │
  ▼
Constraints
  │
  ▼
Pattern
  │
  ▼
Data Structure
  │
  ▼
Brute Force
  │
  ▼
Optimization
  │
  ▼
Invariant
  │
  ▼
Implementation
  │
  ▼
Tests
  │
  ▼
Complexity
  │
  ▼
Trade-offs
```

A strong solution is not merely code that passes examples. It should be correct, appropriately complex, explainable, testable, and suitable for the stated constraints.

## Key Takeaways

- **Recognize patterns rather than memorizing solutions:** hash maps, two pointers, sliding windows, stacks, queues, heaps, binary search, graphs, backtracking, and dynamic programming cover a large portion of interview problems.
- **Let constraints drive the algorithm:** input size, ordering, uniqueness, memory limits, and required output determine whether O(n), O(n log n), or more expensive approaches are acceptable.
- **Choose Python data structures deliberately:** use `dict`/`set` for lookup, `deque` for FIFO, `list` for stacks/sequences, and `heapq` for priority-based workloads.
- **Explain correctness and complexity:** state the invariant, identify the dominant operation, provide time/space complexity, and test meaningful edge cases rather than only the sample input.
- **Bridge interview algorithms to production engineering:** untrusted input, memory limits, concurrency, database access, distributed state, retries, observability, and failure handling determine whether an algorithm is safe beyond an isolated coding exercise.