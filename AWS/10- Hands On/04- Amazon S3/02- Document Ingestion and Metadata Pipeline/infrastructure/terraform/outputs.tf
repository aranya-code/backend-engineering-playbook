output "aws_region" {
  description = "AWS Region where the document ingestion infrastructure is deployed."
  value       = data.aws_region.current.name
}

output "aws_account_id" {
  description = "AWS account ID hosting the document ingestion infrastructure."
  value       = data.aws_caller_identity.current.account_id
}

output "project_name" {
  description = "Logical project identifier used for resource naming."
  value       = local.project_name
}

output "environment" {
  description = "Deployment environment."
  value       = var.environment
}

output "name_prefix" {
  description = "Resolved resource naming prefix."
  value       = local.name_prefix
}

output "documents_bucket_name" {
  description = "Name of the private S3 bucket used for document uploads."
  value       = aws_s3_bucket.documents.bucket
}

output "documents_bucket_arn" {
  description = "ARN of the document storage bucket."
  value       = aws_s3_bucket.documents.arn
}

output "documents_bucket_regional_domain_name" {
  description = "Regional DNS domain name of the document storage bucket."
  value       = aws_s3_bucket.documents.bucket_regional_domain_name
}

output "documents_upload_prefix" {
  description = "S3 prefix used by the API for incoming document uploads."
  value       = var.documents_upload_prefix
}

output "metadata_table_name" {
  description = "Name of the DynamoDB table storing extracted document metadata."
  value       = aws_dynamodb_table.document_metadata.name
}

output "metadata_table_arn" {
  description = "ARN of the document metadata DynamoDB table."
  value       = aws_dynamodb_table.document_metadata.arn
}

output "processing_status_table_name" {
  description = "Name of the DynamoDB table storing document processing status."
  value       = aws_dynamodb_table.processing_status.name
}

output "processing_status_table_arn" {
  description = "ARN of the document processing-status DynamoDB table."
  value       = aws_dynamodb_table.processing_status.arn
}

output "processing_queue_url" {
  description = "URL of the SQS queue receiving document-processing events."
  value       = aws_sqs_queue.processing.url
}

output "processing_queue_arn" {
  description = "ARN of the SQS document-processing queue."
  value       = aws_sqs_queue.processing.arn
}

output "processing_dead_letter_queue_url" {
  description = "URL of the SQS dead-letter queue for failed document-processing messages."
  value       = aws_sqs_queue.processing_dlq.url
}

output "processing_dead_letter_queue_arn" {
  description = "ARN of the SQS dead-letter queue."
  value       = aws_sqs_queue.processing_dlq.arn
}

output "ingestion_lambda_function_name" {
  description = "Name of the Lambda function handling S3 document-ingestion events."
  value       = aws_lambda_function.ingestion.function_name
}

output "ingestion_lambda_function_arn" {
  description = "ARN of the S3 document-ingestion Lambda function."
  value       = aws_lambda_function.ingestion.arn
}

output "processing_lambda_function_name" {
  description = "Name of the Lambda function processing ingested documents."
  value       = aws_lambda_function.processing.function_name
}

output "processing_lambda_function_arn" {
  description = "ARN of the document-processing Lambda function."
  value       = aws_lambda_function.processing.arn
}

output "ingestion_lambda_log_group_name" {
  description = "CloudWatch Logs log group for the ingestion Lambda."
  value       = aws_cloudwatch_log_group.ingestion.name
}

output "processing_lambda_log_group_name" {
  description = "CloudWatch Logs log group for the document-processing Lambda."
  value       = aws_cloudwatch_log_group.processing.name
}

output "ingestion_lambda_execution_role_arn" {
  description = "IAM execution role ARN assigned to the ingestion Lambda."
  value       = aws_iam_role.ingestion_lambda.arn
}

output "processing_lambda_execution_role_arn" {
  description = "IAM execution role ARN assigned to the processing Lambda."
  value       = aws_iam_role.processing_lambda.arn
}

output "documents_bucket_notification_enabled" {
  description = "Whether S3 ObjectCreated notifications are enabled for the ingestion workflow."
  value       = var.enable_s3_event_notifications
}

output "documents_bucket_versioning_enabled" {
  description = "Whether document bucket versioning is enabled."
  value       = var.enable_s3_versioning
}

output "documents_bucket_encryption_key_arn" {
  description = "Customer-managed KMS key ARN when SSE-KMS is configured; null when S3-managed encryption is used."
  value       = var.s3_kms_key_arn
}

output "api_upload_configuration" {
  description = "Non-secret configuration values required by the document upload API."
  value = {
    AWS_REGION                = data.aws_region.current.name
    DOCUMENTS_BUCKET_NAME     = aws_s3_bucket.documents.bucket
    DOCUMENTS_UPLOAD_PREFIX   = var.documents_upload_prefix
  }
}

output "api_processing_status_configuration" {
  description = "Non-secret configuration values required by the processing-status API endpoint."
  value = {
    AWS_REGION                    = data.aws_region.current.name
    PROCESSING_STATUS_TABLE_NAME  = aws_dynamodb_table.processing_status.name
  }
}

output "ingestion_lambda_configuration" {
  description = "Non-secret environment configuration for the ingestion Lambda."
  value = {
    AWS_REGION           = data.aws_region.current.name
    METADATA_TABLE_NAME  = aws_dynamodb_table.document_metadata.name
    PROCESSING_QUEUE_URL = aws_sqs_queue.processing.url
  }
}

output "processing_lambda_configuration" {
  description = "Non-secret environment configuration for the processing Lambda."
  value = {
    AWS_REGION                   = data.aws_region.current.name
    DOCUMENTS_BUCKET_NAME        = aws_s3_bucket.documents.bucket
    METADATA_TABLE_NAME          = aws_dynamodb_table.document_metadata.name
    PROCESSING_STATUS_TABLE_NAME = aws_dynamodb_table.processing_status.name
  }
}