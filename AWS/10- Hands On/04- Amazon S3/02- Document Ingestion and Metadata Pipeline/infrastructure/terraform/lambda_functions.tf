locals {
  ingestion_lambda_function_name = "${local.name_prefix}-ingestion"
  processing_lambda_function_name = "${local.name_prefix}-processing"

  ingestion_lambda_source_dir = "${path.module}/../../../src/ingestion"
  processing_lambda_source_dir = "${path.module}/../../../src/processing"

  ingestion_lambda_archive_path = "${path.module}/.terraform/${local.ingestion_lambda_function_name}.zip"
  processing_lambda_archive_path = "${path.module}/.terraform/${local.processing_lambda_function_name}.zip"

  ingestion_lambda_environment = {
    AWS_REGION           = local.aws_region
    METADATA_TABLE_NAME  = aws_dynamodb_table.document_metadata.name
    PROCESSING_QUEUE_URL = aws_sqs_queue.processing.url
    LOG_LEVEL            = upper(var.api_log_level)
  }

  processing_lambda_environment = {
    AWS_REGION                   = local.aws_region
    DOCUMENTS_BUCKET_NAME        = aws_s3_bucket.documents.bucket
    METADATA_TABLE_NAME          = aws_dynamodb_table.document_metadata.name
    PROCESSING_STATUS_TABLE_NAME = aws_dynamodb_table.processing_status.name
    LOG_LEVEL                    = upper(var.api_log_level)
  }
}

data "archive_file" "ingestion" {
  type        = "zip"
  source_dir  = local.ingestion_lambda_source_dir
  output_path = local.ingestion_lambda_archive_path

  excludes = [
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "tests",
    "README.md"
  ]
}

data "archive_file" "processing" {
  type        = "zip"
  source_dir  = local.processing_lambda_source_dir
  output_path = local.processing_lambda_archive_path

  excludes = [
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "tests",
    "README.md"
  ]
}

resource "aws_lambda_function" "ingestion" {
  function_name = local.ingestion_lambda_function_name
  description   = "Processes S3 document-created events, extracts metadata, and publishes processing messages."

  role = aws_iam_role.ingestion_lambda.arn

  runtime       = var.lambda_runtime
  architectures = [var.lambda_architecture]

  handler = "handler.lambda_handler"

  filename         = data.archive_file.ingestion.output_path
  source_code_hash = data.archive_file.ingestion.output_base64sha256

  timeout     = var.ingestion_lambda_timeout_seconds
  memory_size = var.ingestion_lambda_memory_mb

  reserved_concurrent_executions = var.enable_deletion_protection ? 10 : -1

  environment {
    variables = local.ingestion_lambda_environment
  }

  tracing_config {
    mode = "Active"
  }

  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.ingestion.name
  }

  tags = merge(local.common_tags, {
    Name      = local.ingestion_lambda_function_name
    Component = "ingestion"
  })

  depends_on = [
    aws_iam_role_policy_attachment.ingestion_lambda_execution,
    aws_iam_role_policy.ingestion_lambda_access,
    aws_cloudwatch_log_group.ingestion
  ]

  lifecycle {
    precondition {
      condition     = fileexists("${local.ingestion_lambda_source_dir}/handler.py")
      error_message = "The ingestion Lambda source directory must contain handler.py."
    }
  }
}

resource "aws_lambda_function" "processing" {
  function_name = local.processing_lambda_function_name
  description   = "Processes document-ingestion messages from SQS and updates document processing state."

  role = aws_iam_role.processing_lambda.arn

  runtime       = var.lambda_runtime
  architectures = [var.lambda_architecture]

  handler = "handler.lambda_handler"

  filename         = data.archive_file.processing.output_path
  source_code_hash = data.archive_file.processing.output_base64sha256

  timeout     = var.processing_lambda_timeout_seconds
  memory_size = var.processing_lambda_memory_mb

  reserved_concurrent_executions = var.enable_deletion_protection ? 10 : -1

  environment {
    variables = local.processing_lambda_environment
  }

  tracing_config {
    mode = "Active"
  }

  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.processing.name
  }

  tags = merge(local.common_tags, {
    Name      = local.processing_lambda_function_name
    Component = "processing"
  })

  depends_on = [
    aws_iam_role_policy_attachment.processing_lambda_execution,
    aws_iam_role_policy.processing_lambda_access,
    aws_cloudwatch_log_group.processing
  ]

  lifecycle {
    precondition {
      condition     = fileexists("${local.processing_lambda_source_dir}/handler.py")
      error_message = "The processing Lambda source directory must contain handler.py."
    }
  }
}

resource "aws_lambda_permission" "allow_s3_ingestion" {
  count = var.enable_s3_event_notifications ? 1 : 0

  statement_id  = "AllowS3InvokeIngestionLambda"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.documents.arn

  source_account = local.aws_account_id
}

resource "aws_lambda_event_source_mapping" "processing_queue" {
  event_source_arn = aws_sqs_queue.processing.arn
  function_name    = aws_lambda_function.processing.arn

  enabled = true

  batch_size                         = 5
  maximum_batching_window_in_seconds = 5

  function_response_types = [
    "ReportBatchItemFailures"
  ]

  scaling_config {
    maximum_concurrency = 10
  }

  depends_on = [
    aws_iam_role_policy.processing_lambda_access,
    aws_iam_role_policy_attachment.processing_lambda_execution
  ]

  lifecycle {
    precondition {
      condition = (
        var.processing_queue_visibility_timeout_seconds >=
        6 * var.processing_lambda_timeout_seconds
      )
      error_message = "The processing SQS visibility timeout must be at least six times the processing Lambda timeout."
    }
  }
}