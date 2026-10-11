# 08- Project 07 - Scheduled Tasks with EventBridge Scheduler

## Overview

Amazon EventBridge Scheduler is a managed scheduling service that invokes supported AWS targets at specified times or according to recurring schedules. It supports one-time schedules, rate-based schedules, cron expressions, time zones, flexible delivery windows, retry policies, and dead-letter queues.

This project builds a scheduled order-maintenance workflow using EventBridge Scheduler and AWS Lambda. A schedule invokes a Python function that identifies and processes expired orders. The implementation demonstrates schedule configuration, IAM permissions, timezone handling, retry behavior, failure recovery, monitoring, deployment, and cleanup.

Scheduled workloads are common in backend systems for:

- Expiring abandoned orders and temporary records.
- Running periodic reconciliation jobs.
- Generating reports and billing summaries.
- Triggering data imports and ETL pipelines.
- Executing scheduled notifications.
- Starting maintenance or backup workflows.
- Coordinating recurring operational tasks.

EventBridge Scheduler is preferable to implementing a scheduler inside a continuously running Django or FastAPI process when the workload is naturally event-driven and does not require a permanently running worker.

## Architecture

```mermaid
flowchart TD
    S["EventBridge Scheduler"] -->|"Scheduled invocation"| R["Scheduler Execution Role"]
    R -->|"lambda:InvokeFunction"| L["Scheduled Maintenance Lambda"]
    L -->|"Query expired orders"| D[("DynamoDB Orders Table")]
    L -->|"Update order status"| D
    L --> C["CloudWatch Logs and Metrics"]
    S -. "Delivery failures after retries"| Q[("Scheduler DLQ")]
    O["CloudWatch Alarms / Operations"] --> C
    O --> Q
```

### Execution Flow

1. EventBridge Scheduler evaluates the configured schedule.
2. At the scheduled time, Scheduler assumes its execution role.
3. The role authorizes invocation of the configured Lambda target.
4. Lambda receives the configured input payload and executes the handler.
5. The handler identifies expired orders and conditionally updates their state.
6. Lambda emits logs and metrics for the execution.
7. If Scheduler cannot deliver the invocation, it retries according to the configured delivery policy.
8. If delivery ultimately fails, the event can be sent to a configured SQS dead-letter queue.

**Important distinction:** Scheduler's retry policy governs delivery of the scheduled invocation to its target. It does not automatically retry a Lambda execution that was successfully invoked but later failed during business processing. Lambda execution errors and business-level recovery need their own design.

## Prerequisites

| Requirement | Purpose |
|---|---|
| Python 3.12 | Lambda application runtime |
| AWS CLI | Resource inspection and verification |
| AWS SAM CLI | Infrastructure deployment |
| Docker | Local SAM execution |
| `pytest` | Unit testing |

Verify the environment:

```bash
python --version
aws --version
sam --version
aws sts get-caller-identity
aws configure list
```

Confirm the AWS account and Region before deployment.

This exercise creates an EventBridge Scheduler schedule, Lambda function, DynamoDB table, SQS dead-letter queue, IAM roles, and CloudWatch log group. AWS charges may apply for service usage. Review current regional pricing before deployment, especially if using frequent schedules or large workloads.

## Project Structure

```text
eventbridge-scheduler-lambda/
    src/
        __init__.py
        maintenance_handler.py
    tests/
        test_maintenance_handler.py
    template.yaml
    requirements.txt
    .gitignore
    README.md
```

| File | Responsibility |
|---|---|
| `src/maintenance_handler.py` | Identifies and updates expired orders |
| `tests/test_maintenance_handler.py` | Tests event validation and maintenance behavior |
| `template.yaml` | Defines the schedule, Lambda function, table, roles, and DLQ |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Excludes generated files and local secrets |
| `README.md` | Setup, deployment, verification, and cleanup instructions |

## Choose the Scheduling Mechanism

EventBridge Scheduler and EventBridge scheduled rules serve related purposes, but Scheduler is the recommended choice for new scheduled workloads.

| Capability | EventBridge Scheduler | EventBridge scheduled rule |
|---|---|---|
| One-time schedules | Supported | Not the intended use case |
| Recurring rate schedules | Supported | Supported |
| Cron schedules | Supported | Supported |
| Timezone-aware cron | Supported | Uses UTC scheduling |
| Flexible delivery windows | Supported | Not available as a Scheduler-equivalent feature |
| Per-schedule retry policy | Supported | Different target retry configuration model |
| Schedule groups | Supported | Uses event buses and rules instead |
| Recommended for new scheduled workloads | Yes | Generally use Scheduler instead |

Use Scheduler when the primary requirement is to execute an action at a specified time. Use event rules for event-pattern routing, and consider other workflow services when scheduling is only one step in a larger orchestration process.

## Implement the Scheduled Handler

The example processes orders whose `expires_at` value is earlier than the current time. The table uses `status` and `expires_at` attributes to identify eligible orders.

For production-scale workloads, avoid scanning a large table on every schedule. The basic implementation below is intended for a small exercise; a production design should use a suitable index, partitioning strategy, and bounded processing batches.

Create `src/maintenance_handler.py`.

```python
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["ORDERS_TABLE"])


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    timestamp = datetime.fromisoformat(normalized)

    if timestamp.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")

    return timestamp.astimezone(timezone.utc)


def lambda_handler(event, context):
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    processed = 0
    expired = 0
    last_evaluated_key = None

    while True:
        scan_args = {
            "FilterExpression": (
                Attr("status").eq("PENDING")
                & Attr("expires_at").lt(now_iso)
            ),
            "ProjectionExpression": "order_id, #status, expires_at",
            "ExpressionAttributeNames": {
                "#status": "status",
            },
            "ConsistentRead": False,
        }

        if last_evaluated_key:
            scan_args["ExclusiveStartKey"] = last_evaluated_key

        response = table.scan(**scan_args)

        for item in response.get("Items", []):
            processed += 1
            order_id = item["order_id"]

            try:
                table.update_item(
                    Key={"order_id": order_id},
                    UpdateExpression="SET #status = :expired",
                    ConditionExpression=(
                        "#status = :pending AND expires_at < :now"
                    ),
                    ExpressionAttributeNames={
                        "#status": "status",
                    },
                    ExpressionAttributeValues={
                        ":pending": "PENDING",
                        ":expired": "EXPIRED",
                        ":now": now_iso,
                    },
                )
                expired += 1

            except ClientError as exc:
                error_code = exc.response["Error"]["Code"]

                if error_code == "ConditionalCheckFailedException":
                    logger.info(
                        "Order no longer eligible for expiration",
                        extra={"order_id": order_id},
                    )
                    continue

                raise

        last_evaluated_key = response.get("LastEvaluatedKey")

        if not last_evaluated_key:
            break

    logger.info(
        "Scheduled order maintenance completed",
        extra={
            "request_id": context.aws_request_id,
            "scheduled_time": event.get("scheduled_time"),
            "run_at": now_iso,
            "processed": processed,
            "expired": expired,
        },
    )

    return {
        "processed": processed,
        "expired": expired,
    }
```

### Implementation Notes

- The handler uses UTC timestamps to avoid ambiguity when comparing expiration times.
- The conditional update prevents an order that has already changed state from being expired by a stale scan result.
- A repeated invocation is safe for an order already marked `EXPIRED`, because the condition will no longer match.
- The code re-raises unexpected DynamoDB errors so the Lambda invocation fails visibly rather than silently reporting success.
- The handler uses a full table scan to keep the initial exercise straightforward. A production implementation should replace this with an index-based query and bounded batches.

The unused `Decimal`, `Key`, and `parse_timestamp` imports can be removed from the initial version. The streamlined import section is:

```python
import logging
import os
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
```

## Production Data-Access Design

A full-table scan becomes expensive as the table grows. DynamoDB applies filter expressions after reading items, so a filter does not eliminate the read capacity consumed by the scan.

For a production implementation, create a Global Secondary Index designed for expiration processing. For example:

- Partition key: `maintenance_bucket`
- Sort key: `expires_at`
- Eligible items: `status = PENDING`

The application assigns each pending order a deterministic maintenance bucket. The scheduled worker queries the relevant buckets for expired items and processes bounded pages.

If the table's primary key is `order_id`, the GSI can return the order key and required attributes. The conditional update remains necessary because the order can change between the query and the update.

A GSI is eventually consistent. The conditional update protects the business transition even if the query returns a stale candidate.

## Configure the Infrastructure

Create `template.yaml`.

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Description: Scheduled order maintenance using EventBridge Scheduler and Lambda

Globals:
  Function:
    Runtime: python3.12
    Timeout: 60
    MemorySize: 512
    Architectures:
      - x86_64
    LoggingConfig:
      LogFormat: JSON

Resources:
  OrdersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: order_id
          AttributeType: S
      KeySchema:
        - AttributeName: order_id
          KeyType: HASH
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true

  SchedulerDeadLetterQueue:
    Type: AWS::SQS::Queue
    Properties:
      MessageRetentionPeriod: 1209600

  MaintenanceFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: src.maintenance_handler.lambda_handler
      Description: Expires eligible pending orders
      Environment:
        Variables:
          ORDERS_TABLE: !Ref OrdersTable
      Policies:
        - AWSLambdaBasicExecutionRole
        - DynamoDBCrudPolicy:
            TableName: !Ref OrdersTable

  SchedulerExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service: scheduler.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: InvokeMaintenanceFunction
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - lambda:InvokeFunction
                Resource: !GetAtt MaintenanceFunction.Arn
              - Effect: Allow
                Action:
                  - sqs:SendMessage
                Resource: !GetAtt SchedulerDeadLetterQueue.Arn

  OrderMaintenanceSchedule:
    Type: AWS::Scheduler::Schedule
    Properties:
      Name: order-maintenance-every-five-minutes
      Description: Runs pending-order expiration every five minutes
      GroupName: default
      State: ENABLED
      ScheduleExpression: rate(5 minutes)
      FlexibleTimeWindow:
        Mode: OFF
      Target:
        Arn: !GetAtt MaintenanceFunction.Arn
        RoleArn: !GetAtt SchedulerExecutionRole.Arn
        Input: '{"job":"expire_pending_orders","schedule_version":"1"}'
        RetryPolicy:
          MaximumEventAgeInSeconds: 3600
          MaximumRetryAttempts: 3
        DeadLetterConfig:
          Arn: !GetAtt SchedulerDeadLetterQueue.Arn

Outputs:
  OrdersTableName:
    Description: DynamoDB table used by the maintenance job
    Value: !Ref OrdersTable

  MaintenanceFunctionName:
    Description: Scheduled maintenance Lambda function
    Value: !Ref MaintenanceFunction

  ScheduleName:
    Description: EventBridge Scheduler schedule
    Value: !Ref OrderMaintenanceSchedule

  SchedulerDeadLetterQueueUrl:
    Description: Queue receiving failed schedule deliveries
    Value: !Ref SchedulerDeadLetterQueue
```

### Infrastructure Decisions

**Dedicated execution role:** EventBridge Scheduler assumes this role to invoke the Lambda target and send failed deliveries to the SQS DLQ. It is separate from the Lambda execution role, which grants the function access to DynamoDB and CloudWatch Logs.

**Explicit retry policy:** The schedule retries failed target delivery for up to three attempts while the event remains eligible for delivery within the configured event-age limit. These settings should reflect the business recovery objective.

**Flexible time window disabled:** Scheduler attempts delivery near the scheduled time instead of distributing it across a configured window. For large fleets of periodic jobs, a flexible window can reduce synchronized load on downstream systems.

**Five-minute schedule:** This is intentionally frequent for demonstration. Production jobs should run only as often as the business requirement demands.

**Table access:** The SAM policy shown is broader than the exact permissions needed for the handler because the function uses `Scan` and `UpdateItem`. In production, replace broad CRUD permissions with a narrowly scoped policy that grants only the required actions. If the implementation moves to an index-based query, grant `dynamodb:Query` and the required update permissions.

The schedule and function are deployed together. Scheduler uses the target role to invoke the function; a separate Lambda resource-based permission is not generally needed for this same-account role-based invocation pattern.

## Deploy the Application

Validate and build:

```bash
sam validate --lint
sam build
```

Deploy:

```bash
sam deploy --guided
```

Use a stack name such as:

```text
eventbridge-scheduler-lambda
```

Verify the target account and Region before approving resource creation.

Retrieve the stack outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name eventbridge-scheduler-lambda \
  --query "Stacks[0].Outputs" \
  --output table
```

Record the table name, function name, schedule name, and DLQ URL.

## Insert Test Orders

Set the table name from the stack output:

```bash
export TABLE_NAME="actual-orders-table-name"
```

Insert an expired pending order:

```bash
aws dynamodb put-item \
  --table-name "$TABLE_NAME" \
  --item '{
    "order_id": {"S": "order-expired-1001"},
    "status": {"S": "PENDING"},
    "expires_at": {"S": "2020-01-01T00:00:00+00:00"}
  }'
```

Insert an order that is not yet expired:

```bash
aws dynamodb put-item \
  --table-name "$TABLE_NAME" \
  --item '{
    "order_id": {"S": "order-active-1002"},
    "status": {"S": "PENDING"},
    "expires_at": {"S": "2099-01-01T00:00:00+00:00"}
  }'
```

The first order should become `EXPIRED` after a successful maintenance execution. The second should remain `PENDING`.

## Verify the Schedule

Inspect the schedule:

```bash
aws scheduler get-schedule \
  --name "order-maintenance-every-five-minutes" \
  --group-name default \
  --output json
```

Confirm:

- `State` is `ENABLED`.
- `ScheduleExpression` is `rate(5 minutes)`.
- The target ARN points to the intended Lambda function.
- The execution role ARN is correct.
- Retry and DLQ settings are configured.

Scheduler delivery is not an exact real-time guarantee. A schedule should be designed around a tolerance window rather than assuming that the function starts at the exact millisecond of the scheduled time.

## Verify the Lambda Execution

Set the deployed function name:

```bash
export FUNCTION_NAME="actual-maintenance-function-name"
```

Inspect logs:

```bash
aws logs tail \
  "/aws/lambda/$FUNCTION_NAME" \
  --since 15m \
  --follow
```

Look for the `Scheduled order maintenance completed` log entry and confirm that the expired order count matches expectations.

Inspect the order:

```bash
aws dynamodb get-item \
  --table-name "$TABLE_NAME" \
  --key '{
    "order_id": {"S": "order-expired-1001"}
  }' \
  --consistent-read
```

The returned status should be `EXPIRED`.

Inspect the active order in the same way and verify that it remains `PENDING`.

## Test the Handler Independently

A direct invocation is useful for testing the function without waiting for the schedule.

Create `event.json`:

```json
{
  "job": "expire_pending_orders",
  "schedule_version": "1"
}
```

Invoke the Lambda function:

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --cli-binary-format raw-in-base64-out \
  --payload file://event.json \
  response.json
```

Inspect the response:

```bash
cat response.json
```

A successful synchronous invocation should return a function result containing `processed` and `expired` counts. A successful Lambda Invoke API response does not by itself guarantee business correctness; verify the updated table state and logs.

## Schedule Expressions

EventBridge Scheduler supports rate, cron, and one-time schedule expressions.

| Type | Example | Meaning |
|---|---|---|
| Rate | `rate(5 minutes)` | Runs every five minutes |
| Rate | `rate(1 day)` | Runs at a recurring daily interval |
| Cron | `cron(0 9 ? * MON-FRI *)` | Runs at 09:00 on weekdays, using the configured schedule timezone |
| One-time | `at(2027-01-01T09:00:00)` | Runs once at the specified local schedule time |

For cron schedules, configure the intended timezone explicitly when the requirement is tied to local business hours. UTC is generally the simplest choice for infrastructure maintenance and distributed systems.

One-time schedules can be configured to be deleted after completion. For large numbers of one-time schedules, define cleanup and retention behavior so completed schedules do not accumulate unnecessarily.

## Retry Semantics and Idempotency

There are two distinct failure scenarios.

### Scheduler Cannot Deliver the Invocation

Examples include a temporarily unavailable target, permission failures, or service throttling.

Scheduler retries according to the target retry policy. After delivery attempts are exhausted, the event can be sent to the configured Scheduler DLQ, provided the execution role has permission to send messages to the queue.

### Lambda Starts but Business Processing Fails

Examples include a DynamoDB throttling error, an unhandled exception, or a timeout after partially updating records.

Scheduler considers the target delivery successful once the Lambda invocation has been accepted. It does not automatically treat a later function execution error as a failed Scheduler delivery.

For this scenario, implement a separate recovery strategy:

- Use Lambda asynchronous failure destinations if the invocation mode and configuration support them.
- Emit application-level failures and alert on them.
- Make operations idempotent.
- Use a durable work queue for jobs requiring independent retries.
- Use Step Functions for workflows requiring explicit state, retries, and compensation.

The conditional update in this project makes the status transition repeatable. For external side effects, use a durable idempotency key or transactional outbox pattern rather than relying on an in-memory flag.

## Overlapping Executions and Concurrency

A scheduled Lambda can run longer than its interval. If the five-minute schedule invokes a function that takes eight minutes, executions can overlap.

Overlapping jobs can cause:

- Duplicate notifications.
- Repeated scans and increased cost.
- Conflicting updates.
- Downstream overload.
- Inconsistent reports.

Use the following controls where appropriate:

- Bound the job's execution time and work per invocation.
- Use conditional writes to make state transitions safe.
- Use a distributed lock or durable lease when only one execution may run at a time.
- Split large jobs into bounded batches.
- Use reserved concurrency to limit the function's parallel executions.
- Move substantial workloads to SQS or Step Functions when independent work tracking is needed.

A distributed lock requires expiration and recovery semantics. A permanent lock record can prevent future jobs from running after a crash.

## Monitoring and Operational Diagnosis

Monitor the schedule delivery path and the Lambda execution path separately.

Useful signals include:

- Scheduler invocation and delivery failures.
- Scheduler DLQ message count.
- Lambda `Errors`, `Duration`, `Throttles`, and `ConcurrentExecutions`.
- Number of orders processed and expired.
- Job duration and last successful completion time.
- DynamoDB throttling and request latency.

A job can have successful Lambda invocations while still failing its business objective. For critical reconciliation or expiration jobs, emit an explicit completion metric and alert when the expected completion window passes without a successful run.

For operational recovery, retain enough information to identify the schedule, invocation, processing window, and failed business records. A DLQ message indicates failed delivery; it does not necessarily contain a complete record of every downstream operation attempted by the function.

## Security Considerations

- Restrict the Scheduler execution role to the required Lambda target.
- Grant `sqs:SendMessage` only to the configured DLQ.
- Restrict the Lambda execution role to the required DynamoDB actions.
- Avoid embedding secrets in the schedule input payload.
- Use Secrets Manager or Parameter Store for credentials if the job needs them.
- Enable suitable CloudWatch log retention and access controls.
- Review IAM trust policies and permissions before deploying.
- Keep deployment credentials separate from runtime credentials.

Scheduler input should contain job parameters, not authentication material or unnecessary personal data.

## Common Failure Modes

| Symptom | Possible cause | Corrective action |
|---|---|---|
| Schedule never invokes the target | Disabled schedule or invalid target role | Inspect `get-schedule` and role trust policy |
| Scheduler reports delivery failures | Missing `lambda:InvokeFunction` permission or incorrect target ARN | Correct the execution role and target |
| Lambda runs but no records change | Filter conditions do not match, or table name is incorrect | Inspect environment variables and table data |
| Function times out | Full-table scan or unbounded processing | Use an index, pagination, and bounded batches |
| Orders are processed more than once | Overlapping executions or retry after partial completion | Use conditional updates and durable idempotency |
| DLQ contains messages | Target invocation could not be delivered after retries | Inspect the message, role permissions, target configuration, and delivery errors |
| Job succeeds but business objective is missed | Handler returns success without validating expected work | Emit completion metrics and validate business invariants |
| Job runs at an unexpected local time | Incorrect timezone or misunderstanding of cron fields | Inspect schedule timezone and expression |

## Cost and Resource Management

The main cost drivers are:

- Lambda invocations and execution duration.
- DynamoDB reads and writes.
- EventBridge Scheduler schedule usage.
- SQS requests and retained DLQ messages.
- CloudWatch Logs ingestion and retention.
- Point-in-time recovery and DynamoDB storage.

Frequent full-table scans can become the dominant cost as the table grows. Use index-based queries, process bounded pages, and measure the number of items examined per successful update.

Before deployment, estimate the schedule frequency, average function duration, number of eligible records, and expected retry volume. Review current regional pricing and service quotas.

## Cleanup

Delete the stack:

```bash
aws cloudformation delete-stack \
  --stack-name eventbridge-scheduler-lambda
```

Wait for deletion:

```bash
aws cloudformation wait stack-delete-complete \
  --stack-name eventbridge-scheduler-lambda
```

Verify removal:

```bash
aws cloudformation describe-stacks \
  --stack-name eventbridge-scheduler-lambda
```

Check the DLQ for messages that need investigation or replay before deleting the stack. If the table contains data that must be retained, export or preserve it before removing the resources.

## Extension Exercises

| Exercise | Objective |
|---|---|
| Add a GSI for expiration queries | Replace full-table scans with targeted queries |
| Add a distributed lease | Prevent overlapping maintenance runs |
| Add a scheduled reconciliation job | Compare application state with an external system |
| Add a Scheduler DLQ replay tool | Recover failed target deliveries safely |
| Add a separate SQS work queue | Process large expiration workloads asynchronously |
| Add CloudWatch alarms | Detect failed delivery and missed completion windows |
| Add Step Functions | Coordinate multi-step scheduled workflows |
| Add a local-business-time schedule | Handle timezone and daylight-saving requirements |
| Add idempotent notifications | Avoid sending duplicate expiration notifications |
| Add CI/CD deployment | Automate testing, deployment, and smoke verification |

For each extension, document the IAM changes, schedule expression, failure semantics, verification steps, and cleanup procedure.

## Key Takeaways

- EventBridge Scheduler is the preferred service for new scheduled workloads requiring one-time or recurring execution, timezone support, and configurable delivery retries.
- Scheduler retries failed target delivery, but a Lambda function that starts and later fails requires its own execution-error recovery strategy.
- Scheduled jobs must tolerate duplicate and overlapping executions through conditional updates, idempotency, and, where necessary, distributed coordination.
- Full-table scans are acceptable for small exercises but should be replaced with index-based queries and bounded processing for production workloads.
- Production scheduling requires least-privilege IAM roles, explicit failure handling, completion monitoring, cost controls, and a tested recovery procedure.