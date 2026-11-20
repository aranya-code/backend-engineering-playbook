locals {
  processing_queue_name = (
    var.processing_queue_name != null
    ? var.processing_queue_name
    : "${local.name_prefix}-processing"
  )

  processing_dead_letter_queue_name = (
    var.processing_dead_letter_queue_name != null
    ? var.processing_dead_letter_queue_name
    : "${local.name_prefix}-processing-dlq"
  )
}

resource "aws_sqs_queue" "processing_dlq" {
  name = local.processing_dead_letter_queue_name

  message_retention_seconds = 1209600
  visibility_timeout_seconds = var.processing_queue_visibility_timeout_seconds

  sqs_managed_sse_enabled = true

  tags = merge(local.common_tags, {
    Name      = local.processing_dead_letter_queue_name
    Component = "document-processing"
    Purpose   = "DeadLetterQueue"
  })
}

resource "aws_sqs_queue" "processing" {
  name = local.processing_queue_name

  visibility_timeout_seconds = var.processing_queue_visibility_timeout_seconds
  message_retention_seconds  = var.processing_queue_message_retention_seconds

  receive_wait_time_seconds = 20

  delay_seconds = 0

  sqs_managed_sse_enabled = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.processing_dlq.arn
    maxReceiveCount     = var.processing_queue_max_receive_count
  })

  tags = merge(local.common_tags, {
    Name      = local.processing_queue_name
    Component = "document-processing"
    Purpose   = "ProcessingQueue"
  })

  lifecycle {
    precondition {
      condition = (
        var.processing_queue_visibility_timeout_seconds >=
        6 * var.processing_lambda_timeout_seconds
      )
      error_message = "The processing queue visibility timeout must be at least six times the processing Lambda timeout."
    }
  }
}

resource "aws_sqs_queue_redrive_allow_policy" "processing_dlq" {
  queue_url = aws_sqs_queue.processing_dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns = [
      aws_sqs_queue.processing.arn
    ]
  })
}

resource "aws_sqs_queue_policy" "processing" {
  queue_url = aws_sqs_queue.processing.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "AllowOnlyIngestionLambdaToSendMessages"
        Effect = "Allow"

        Principal = {
          AWS = aws_iam_role.ingestion_lambda.arn
        }

        Action = [
          "sqs:SendMessage"
        ]

        Resource = aws_sqs_queue.processing.arn
      }
    ]
  })
}

resource "aws_sqs_queue_policy" "processing_dlq" {
  queue_url = aws_sqs_queue.processing_dlq.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "DenyInsecureTransport"
        Effect = "Deny"

        Principal = {
          AWS = "*"
        }

        Action = "sqs:*"

        Resource = aws_sqs_queue.processing_dlq.arn

        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}