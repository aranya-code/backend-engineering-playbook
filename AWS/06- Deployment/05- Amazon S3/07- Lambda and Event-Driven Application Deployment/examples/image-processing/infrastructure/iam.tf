# ---------------------------------------------------------------------------
# Lambda Execution Role Trust Policy
#
# Allows the AWS Lambda service to assume this role when executing the
# image-processing function.
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    sid     = "AllowLambdaAssumeRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values = [
        "arn:${data.aws_partition.current.partition}:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${local.lambda_function_name}"
      ]
    }
  }
}

# ---------------------------------------------------------------------------
# Lambda Execution Role
#
# Dedicated to the image-processing function. Its permissions are defined
# separately in an inline policy and restricted to the resources required
# by this application.
# ---------------------------------------------------------------------------

resource "aws_iam_role" "lambda" {
  name               = "${local.lambda_function_name}-execution-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = merge(local.common_tags, {
    Name      = "${local.lambda_function_name}-execution-role"
    Purpose   = "lambda-execution"
    Component = "image-processing"
  })
}

# ---------------------------------------------------------------------------
# Lambda Execution Permissions
#
# Permissions are scoped to:
# - Write logs to the dedicated CloudWatch log group.
# - Read source images from the configured input prefix.
# - Write processed images to the configured output prefix.
# - Send failed asynchronous invocation records to the SQS destination.
#
# No broad managed policies such as AWSLambdaBasicExecutionRole or
# AmazonS3FullAccess are attached to this role.
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "lambda_execution" {
  statement {
    sid    = "WriteLambdaLogs"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = [
      "${aws_cloudwatch_log_group.lambda.arn}:*"
    ]
  }

  statement {
    sid    = "ReadInputImages"
    effect = "Allow"

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${aws_s3_bucket.input.arn}/${var.input_prefix}*"
    ]
  }

  statement {
    sid    = "WriteProcessedImages"
    effect = "Allow"

    actions = [
      "s3:PutObject"
    ]

    resources = [
      "${aws_s3_bucket.output.arn}/${var.output_prefix}*"
    ]
  }

  statement {
    sid    = "SendFailedInvocationRecords"
    effect = "Allow"

    actions = [
      "sqs:SendMessage"
    ]

    resources = [
      aws_sqs_queue.lambda_failure.arn
    ]
  }
}

# ---------------------------------------------------------------------------
# Lambda Execution Inline Policy
#
# Attaching the policy to the dedicated execution role keeps the function's
# AWS access explicit, auditable, and limited to required resources.
# ---------------------------------------------------------------------------

resource "aws_iam_role_policy" "lambda_execution" {
  name   = "${local.lambda_function_name}-execution-policy"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_execution.json
}