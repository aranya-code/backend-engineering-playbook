output "replication_role_arn" {
  description = "ARN of the IAM role assumed by Amazon S3 to perform object replication."
  value       = aws_iam_role.replication.arn
}

output "replication_role_name" {
  description = "Name of the IAM replication role."
  value       = aws_iam_role.replication.name
}

output "replication_role_id" {
  description = "Unique ID assigned to the IAM replication role."
  value       = aws_iam_role.replication.unique_id
}

output "replication_policy_id" {
  description = "ID of the inline IAM policy attached to the replication role."
  value       = aws_iam_role_policy.replication.id
}

output "replication_configuration_id" {
  description = "ID of the S3 replication configuration managed by this module."
  value       = aws_s3_bucket_replication_configuration.this.id
}

output "replication_rule_id" {
  description = "Identifier of the configured S3 replication rule."
  value       = var.replication_rule_id
}

output "replication_rule_status" {
  description = "Configured status of the S3 replication rule."
  value       = var.replication_enabled ? "Enabled" : "Disabled"
}

output "source_bucket_id" {
  description = "Name of the source S3 bucket configured for replication."
  value       = var.source_bucket_id
}

output "source_bucket_arn" {
  description = "ARN of the source S3 bucket configured for replication."
  value       = var.source_bucket_arn
}

output "destination_bucket_arn" {
  description = "ARN of the destination S3 bucket configured for replication."
  value       = var.destination_bucket_arn
}

output "destination_account_id" {
  description = "AWS account ID configured as the destination bucket owner, when supplied."
  value       = var.destination_account_id
}

output "destination_storage_class" {
  description = "Storage class configured for replicated objects."
  value       = var.destination_storage_class
}

output "replication_metrics_enabled" {
  description = "Whether S3 replication metrics are enabled."
  value       = var.metrics_enabled
}

output "replication_time_control_enabled" {
  description = "Whether S3 Replication Time Control is enabled."
  value       = var.replication_time_control_enabled
}

output "source_kms_key_arn" {
  description = "Source KMS key ARN configured for SSE-KMS encrypted object replication, if applicable."
  value       = var.source_kms_key_arn
}

output "destination_kms_key_arn" {
  description = "Destination KMS key ARN configured for replicated object encryption, if applicable."
  value       = var.destination_kms_key_arn
}
