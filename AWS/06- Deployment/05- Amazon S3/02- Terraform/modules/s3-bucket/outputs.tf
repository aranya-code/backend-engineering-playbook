output "bucket_id" {
  description = "Name of the S3 bucket."
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket."
  value       = aws_s3_bucket.this.arn
}

output "bucket_region" {
  description = "AWS Region in which the S3 bucket is located."
  value       = aws_s3_bucket.this.region
}

output "bucket_domain_name" {
  description = "Regional bucket domain name."
  value       = aws_s3_bucket.this.bucket_regional_domain_name
}

output "bucket_hosted_zone_id" {
  description = "Route 53 hosted zone ID associated with the bucket's Region."
  value       = aws_s3_bucket.this.hosted_zone_id
}

output "bucket_versioning_enabled" {
  description = "Whether bucket versioning is configured as enabled."
  value       = var.versioning_enabled
}

output "bucket_kms_key_arn" {
  description = "Customer-managed KMS key ARN, or null when SSE-S3 is used."
  value       = var.kms_key_arn
}

output "bucket_encryption_algorithm" {
  description = "Configured default server-side encryption algorithm."
  value       = var.kms_key_arn == null ? "AES256" : "aws:kms"
}

output "lifecycle_configuration_id" {
  description = "Lifecycle configuration resource ID, or null when no lifecycle rules are configured."
  value       = try(aws_s3_bucket_lifecycle_configuration.this[0].id, null)
}

output "server_access_logging_enabled" {
  description = "Whether server access logging is configured."
  value       = var.logging_target_bucket != null
}

output "server_access_logging_target_bucket" {
  description = "Target bucket for server access logs, or null when logging is disabled."
  value       = var.logging_target_bucket
}
