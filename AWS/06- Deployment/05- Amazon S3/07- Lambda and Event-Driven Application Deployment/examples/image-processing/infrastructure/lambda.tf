# ---------------------------------------------------------------------------
# Lambda CloudWatch Log Group
#
# The log group is created explicitly to control retention and ensure that
# the execution role can write only to this function's log streams.
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.lambda_function_name}"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Name      = "/aws/lambda/${local.lambda_function_name}"
    Purpose   = "lambda-application-logs"
    Component = "image-processing"
  })
}

# ---------------------------------------------------------------------------
# Lambda Function
#
# The deployment archive is built outside Terraform. It must contain:
# - handler.py
# - image_transformer.py
# - Dependencies from src/requirements.txt
#
# All files and dependencies must be located at the archive root.
# Pillow must be built for the configured Lambda runtime and architecture.
#
# The execution role and its permissions are defined in iam.tf.
# ---------------------------------------------------------------------------

resource "aws_lambda_function" "image_processor" {
  function_name = local.lambda_function_name
  description   = "Processes uploaded images and stores generated thumbnails."

  role          = aws_iam_role.lambda.arn
  runtime       = var.lambda_runtime
  handler       = "handler.lambda_handler"
  architectures = [var.lambda_architecture]

  filename         = var.lambda_package_path
  source_code_hash = filebase64sha256(var.lambda_package_path)

  timeout                        = var.lambda_timeout
  memory_size                    = var.lambda_memory_size
  reserved_concurrent_executions = -1
  publish                         = true

  ephemeral_storage {
    size = 512
  }

  environment {
    variables = {
      INPUT_BUCKET         = aws_s3_bucket.input.bucket
      OUTPUT_BUCKET        = aws_s3_bucket.output.bucket
      INPUT_PREFIX         = var.input_prefix
      OUTPUT_PREFIX        = var.output_prefix
      MAX_INPUT_SIZE_MB    = tostring(var.max_input_size_mb)
      THUMBNAIL_MAX_WIDTH  = tostring(var.thumbnail_max_width)
      THUMBNAIL_MAX_HEIGHT = tostring(var.thumbnail_max_height)
      MAX_IMAGE_PIXELS     = tostring(var.max_image_pixels)
      LOG_LEVEL            = "INFO"
    }
  }

  tags = merge(local.common_tags, {
    Name      = local.lambda_function_name
    Purpose   = "image-processing"
    Component = "s3-image-processing"
  })

  depends_on = [
    aws_iam_role_policy.lambda_execution,
    aws_cloudwatch_log_group.lambda
  ]

  lifecycle {
    precondition {
      condition     = fileexists(var.lambda_package_path)
      error_message = "Lambda deployment archive does not exist. Build the ZIP archive and set lambda_package_path before applying Terraform."
    }
  }
}

# ---------------------------------------------------------------------------
# Lambda Asynchronous Invocation Configuration
#
# S3 invokes Lambda asynchronously. Failed invocation records are delivered
# to the SQS failure destination after the configured retry attempts.
# ---------------------------------------------------------------------------

resource "aws_lambda_function_event_invoke_config" "image_processor" {
  function_name = aws_lambda_function.image_processor.function_name

  maximum_event_age_in_seconds = 3600
  maximum_retry_attempts       = var.lambda_max_retry_attempts

  destination_config {
    on_failure {
      destination = aws_sqs_queue.lambda_failure.arn
    }
  }

  depends_on = [
    aws_sqs_queue_policy.lambda_failure
  ]
}

# ---------------------------------------------------------------------------
# Permission for S3 to Invoke Lambda
#
# Invocation is restricted to the configured input bucket and current
# AWS account. The shared caller-identity data source is declared once
# elsewhere in the root module.
# ---------------------------------------------------------------------------

resource "aws_lambda_permission" "allow_s3_invocation" {
  statement_id  = "AllowInvocationFromInputBucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.image_processor.function_name
  principal     = "s3.amazonaws.com"

  source_arn     = aws_s3_bucket.input.arn
  source_account = data.aws_caller_identity.current.account_id
}