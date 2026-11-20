locals {
  ingestion_log_group_name  = "/aws/lambda/${local.name_prefix}-ingestion"
  processing_log_group_name = "/aws/lambda/${local.name_prefix}-processing"
}

resource "aws_cloudwatch_log_group" "ingestion" {
  name              = local.ingestion_log_group_name
  retention_in_days = var.lambda_log_retention_days

  tags = merge(local.common_tags, {
    Name      = local.ingestion_log_group_name
    Component = "document-ingestion"
    Purpose   = "LambdaLogs"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_cloudwatch_log_group" "processing" {
  name              = local.processing_log_group_name
  retention_in_days = var.lambda_log_retention_days

  tags = merge(local.common_tags, {
    Name      = local.processing_log_group_name
    Component = "document-processing"
    Purpose   = "LambdaLogs"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_cloudwatch_metric_alarm" "ingestion_lambda_errors" {
  alarm_name        = "${local.name_prefix}-ingestion-errors"
  alarm_description = "The document ingestion Lambda reported one or more execution errors."

  namespace   = "AWS/Lambda"
  metric_name = "Errors"
  statistic   = "Sum"

  dimensions = {
    FunctionName = aws_lambda_function.ingestion.function_name
  }

  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-ingestion-errors"
    Component = "document-ingestion"
  })
}

resource "aws_cloudwatch_metric_alarm" "processing_lambda_errors" {
  alarm_name        = "${local.name_prefix}-processing-errors"
  alarm_description = "The document processing Lambda reported one or more execution errors."

  namespace   = "AWS/Lambda"
  metric_name = "Errors"
  statistic   = "Sum"

  dimensions = {
    FunctionName = aws_lambda_function.processing.function_name
  }

  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-processing-errors"
    Component = "document-processing"
  })
}

resource "aws_cloudwatch_metric_alarm" "ingestion_lambda_throttles" {
  alarm_name        = "${local.name_prefix}-ingestion-throttles"
  alarm_description = "The document ingestion Lambda experienced invocation throttling."

  namespace   = "AWS/Lambda"
  metric_name = "Throttles"
  statistic   = "Sum"

  dimensions = {
    FunctionName = aws_lambda_function.ingestion.function_name
  }

  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-ingestion-throttles"
    Component = "document-ingestion"
  })
}

resource "aws_cloudwatch_metric_alarm" "processing_lambda_throttles" {
  alarm_name        = "${local.name_prefix}-processing-throttles"
  alarm_description = "The document processing Lambda experienced invocation throttling."

  namespace   = "AWS/Lambda"
  metric_name = "Throttles"
  statistic   = "Sum"

  dimensions = {
    FunctionName = aws_lambda_function.processing.function_name
  }

  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-processing-throttles"
    Component = "document-processing"
  })
}

resource "aws_cloudwatch_metric_alarm" "processing_queue_oldest_message" {
  alarm_name        = "${local.name_prefix}-processing-queue-message-age"
  alarm_description = "The oldest visible processing message has exceeded the configured age threshold."

  namespace   = "AWS/SQS"
  metric_name = "ApproximateAgeOfOldestMessage"
  statistic   = "Maximum"

  dimensions = {
    QueueName = aws_sqs_queue.processing.name
  }

  period              = 300
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = 900
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-processing-queue-message-age"
    Component = "document-processing"
  })
}

resource "aws_cloudwatch_metric_alarm" "processing_dlq_messages" {
  alarm_name        = "${local.name_prefix}-processing-dlq-messages"
  alarm_description = "One or more messages are visible in the document processing dead-letter queue."

  namespace   = "AWS/SQS"
  metric_name = "ApproximateNumberOfMessagesVisible"
  statistic   = "Maximum"

  dimensions = {
    QueueName = aws_sqs_queue.processing_dlq.name
  }

  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-processing-dlq-messages"
    Component = "document-processing"
  })
}