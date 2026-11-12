# ---------------------------------------------------------------------------
# Lambda Asynchronous Failure Destination Queue
#
# S3 invokes the image-processing Lambda function directly. Lambda processes
# these events asynchronously and sends an invocation record to this queue
# when processing fails after the configured retry policy.
#
# This is a Lambda destination queue, not an SQS event source queue.
# ---------------------------------------------------------------------------

resource "aws_sqs_queue" "lambda_failure" {
  name = local.failure_queue_name

  message_retention_seconds  = var.failure_queue_retention_seconds
  visibility_timeout_seconds = 300
  receive_wait_time_seconds  = 20

  sqs_managed_sse_enabled = true

  tags = merge(local.common_tags, {
    Name      = local.failure_queue_name
    Purpose   = "lambda-failure-destination"
    Component = "image-processing"
  })
}

# ---------------------------------------------------------------------------
# Failure Queue Transport Security
#
# Deny requests that do not use TLS. Lambda's asynchronous invocation
# destination delivery uses AWS service-to-service communication over
# secure transport.
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "lambda_failure_queue" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = [
      "sqs:*"
    ]

    resources = [
      aws_sqs_queue.lambda_failure.arn
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_sqs_queue_policy" "lambda_failure" {
  queue_url = aws_sqs_queue.lambda_failure.id
  policy    = data.aws_iam_policy_document.lambda_failure_queue.json
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

output "failure_queue_name" {
  description = "Name of the Lambda asynchronous invocation failure queue."
  value       = aws_sqs_queue.lambda_failure.name
}

output "failure_queue_url" {
  description = "URL of the Lambda asynchronous invocation failure queue."
  value       = aws_sqs_queue.lambda_failure.url
}

output "failure_queue_arn" {
  description = "ARN of the Lambda asynchronous invocation failure queue."
  value       = aws_sqs_queue.lambda_failure.arn
}