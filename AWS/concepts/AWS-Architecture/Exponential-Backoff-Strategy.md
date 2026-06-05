# Exponential Backoff Strategy

## Definition
Exponential Backoff is a retry mechanism where the wait time doubles after each failed request.

## Example

```text
Retry 1 -> 1 sec
Retry 2 -> 2 sec
Retry 3 -> 4 sec
Retry 4 -> 8 sec
Retry 5 -> 16 sec
```

## Why AWS Uses It
- Handles API throttling
- Prevents retry storms
- Reduces service overload

## Best Practice
Use Exponential Backoff + Jitter.

## Common AWS Errors
- ThrottlingException
- RequestLimitExceeded
- 429 Too Many Requests
