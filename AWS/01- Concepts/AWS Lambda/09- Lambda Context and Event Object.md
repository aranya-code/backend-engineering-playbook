# 09- Lambda Context and Event Object

# Lambda Context and Event Object

Every AWS Lambda invocation passes two parameters to the handler function:

```python
def handler(event, context):
    ...
```

Understanding these two objects is essential because they provide everything the Lambda function needs to process a request and interact with the execution environment.

A senior backend engineer should know:

- What information each object contains
- Which values change between invocations
- Which values remain constant
- How to use them for logging, tracing, timeout management, and observability

---

# Handler Signature

Python Lambda handlers have the following signature:

```python
def handler(event, context):
    pass
```

Where:

- `event` contains the incoming request or trigger data.
- `context` contains runtime metadata about the invocation.

---

# High-Level Flow

```text
AWS Service

↓

Lambda Runtime

↓

handler(event, context)

↓

Business Logic

↓

Return Response
```

---

# Event Object

The **event object** contains data sent by the event source.

Different event sources produce different event structures.

Examples include:

- API Gateway
- ALB
- S3
- EventBridge
- SNS
- SQS
- DynamoDB Streams
- Kinesis

The Lambda runtime does **not** modify the event.

---

# Example Event

Simple invocation:

```json
{
    "name":"Alice",
    "age":30
}
```

Handler:

```python
def handler(event, context):

    print(event["name"])
```

Output:

```
Alice
```

---

# Event is Read-Only Input

Think of the event as the request payload.

```text
Event Source

↓

JSON Event

↓

Lambda

↓

Read Data

↓

Return Response
```

Do not treat the event object as application state.

---

# API Gateway Event

Example:

```http
GET /users/100?page=1
```

Produces:

```json
{
    "httpMethod":"GET",
    "path":"/users/100",
    "headers":{},
    "queryStringParameters":{
        "page":"1"
    },
    "pathParameters":{
        "id":"100"
    }
}
```

---

# Reading Query Parameters

```python
page = event["queryStringParameters"]["page"]
```

---

# Reading Path Parameters

```python
user_id = event["pathParameters"]["id"]
```

---

# Reading Headers

```python
token = event["headers"]["Authorization"]
```

Useful for:

- JWT
- OAuth
- API Keys

---

# Reading Request Body

```python
import json

body = json.loads(event["body"])

print(body["email"])
```

---

# S3 Event Example

Uploading a file generates:

```json
{
    "Records":[
        {
            "s3":{
                "bucket":{
                    "name":"images"
                },
                "object":{
                    "key":"cat.jpg"
                }
            }
        }
    ]
}
```

Reading values:

```python
record = event["Records"][0]

bucket = record["s3"]["bucket"]["name"]

key = record["s3"]["object"]["key"]
```

---

# SQS Event Example

```json
{
    "Records":[
        {
            "body":"Hello"
        },
        {
            "body":"World"
        }
    ]
}
```

Process messages:

```python
for message in event["Records"]:

    print(message["body"])
```

---

# SNS Event Example

```json
{
    "Records":[
        {
            "Sns":{
                "Message":"Order Created"
            }
        }
    ]
}
```

---

# DynamoDB Streams Event

```json
{
    "Records":[
        {
            "eventName":"INSERT"
        }
    ]
}
```

Useful fields:

- INSERT
- MODIFY
- REMOVE

---

# Kinesis Event

```json
{
    "Records":[
        {
            "kinesis":{
                "data":"..."
            }
        }
    ]
}
```

---

# Event Size

Maximum event payload depends on the invocation source.

Examples:

| Source | Maximum Payload |
|----------|----------------|
| API Gateway | 10 MB |
| Function URL | 6 MB |
| Synchronous Invocation | 6 MB |
| Asynchronous Invocation | 1 MB |
| SQS | 256 KB per message |
| SNS | 256 KB |

Always verify current AWS limits before designing high-volume integrations.

---

# Context Object

The second parameter is the context object.

```python
def handler(event, context):

    print(context.function_name)
```

Unlike the event, the context object is created by the Lambda runtime.

---

# What Does Context Contain?

The context object contains runtime information such as:

- Function name
- Function version
- AWS Request ID
- Remaining execution time
- Memory allocation
- Log group
- Log stream
- Invoked ARN

---

# Common Context Properties

| Property | Description |
|----------|-------------|
| function_name | Lambda function name |
| function_version | Published version |
| invoked_function_arn | ARN used for invocation |
| memory_limit_in_mb | Configured memory |
| aws_request_id | Unique request identifier |
| log_group_name | CloudWatch log group |
| log_stream_name | CloudWatch log stream |

---

# Function Name

```python
print(context.function_name)
```

Output:

```
order-service
```

---

# Function Version

```python
print(context.function_version)
```

Example:

```
12
```

or

```
$LATEST
```

---

# Memory Limit

```python
print(context.memory_limit_in_mb)
```

Output:

```
1024
```

Useful for diagnostics.

---

# AWS Request ID

Every invocation receives a unique ID.

```python
print(context.aws_request_id)
```

Example:

```
6cf58ef1-1dd4...
```

This ID is extremely useful for:

- Logging
- Tracing
- Support investigations

---

# Remaining Execution Time

One of the most useful context methods.

```python
remaining = context.get_remaining_time_in_millis()
```

Output:

```
8750
```

(milliseconds)

---

# Why Remaining Time Matters

Imagine:

Timeout:

```
30 Seconds
```

Processing:

```
29 Seconds
```

Before calling another service:

```python
if context.get_remaining_time_in_millis() < 2000:

    return
```

Avoids abrupt termination.

---

# Logging Request IDs

Good production logging:

```python
print({

    "request_id":context.aws_request_id,

    "user":"100"

})
```

Makes debugging significantly easier.

---

# Context Lifetime

The context object exists only for a single invocation.

```text
Invocation 1

↓

Context A

------------------

Invocation 2

↓

Context B
```

Never cache the context object globally.

---

# Event vs Context

| Event | Context |
|--------|----------|
| Input from trigger | Runtime metadata |
| Different for each trigger | Same structure for all triggers |
| Business data | Execution data |
| User supplied | AWS supplied |

---

# Production Example

```python
import json

def handler(event, context):

    print(

        f"Request={context.aws_request_id}"

    )

    return {

        "statusCode":200,

        "body":json.dumps({

            "id":event["pathParameters"]["id"]

        })
    }
```

---

# Common Mistakes

## Assuming Every Event Looks the Same

Incorrect:

```python
event["body"]
```

This exists for API Gateway but not for S3 events.

Always inspect the event format for the specific trigger.

---

## Ignoring Request IDs

Without logging:

```
Production Error
```

No way to correlate logs.

Always log:

```
aws_request_id
```

---

## Ignoring Remaining Time

Large operations should check:

```python
context.get_remaining_time_in_millis()
```

to avoid being terminated unexpectedly.

---

# Best Practices

✅ Understand the event format for every trigger.

✅ Validate all incoming event data.

✅ Log the AWS Request ID.

✅ Use `get_remaining_time_in_millis()` before expensive operations.

✅ Keep the event immutable.

✅ Never cache the context object.

---

# Senior Backend Engineering Perspective

The **event object** defines the business request, while the **context object** provides operational metadata about the execution environment.

Senior engineers use the context object to improve observability, implement graceful timeout handling, and correlate distributed logs. They design handlers that are independent of any specific trigger by abstracting event parsing into reusable components and validating incoming payloads before processing.

In production, understanding these two objects is fundamental to building robust, debuggable, and maintainable serverless applications.

---

# Interview Questions

### Beginner

- What are the two parameters passed to a Lambda handler?
- What does the event object contain?
- What is the purpose of the context object?

### Intermediate

- How do you access path parameters?
- How do you retrieve the remaining execution time?
- What is `aws_request_id` used for?

### Senior

- How would you design a trigger-agnostic Lambda handler?
- Why should you log the AWS Request ID?
- How would you prevent a Lambda from timing out while calling downstream services?
- How would you normalize events from API Gateway, SQS, and EventBridge into a common business model?

---

# Key Takeaways

- Every Lambda handler receives an `event` object and a `context` object.
- The `event` contains business data from the trigger, while the `context` contains runtime metadata supplied by AWS.
- Event formats vary depending on the triggering service and should be parsed accordingly.
- The `context` object provides valuable information such as the function name, memory allocation, request ID, and remaining execution time.
- Proper use of both objects improves application reliability, observability, and maintainability.