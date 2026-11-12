output "bucket_id" {
  description = "Name of the created S3 bucket."
  value       = module.secure_bucket.bucket_id
}

output "bucket_arn" {
  description = "ARN of the created S3 bucket."
  value       = module.secure_bucket.bucket_arn
}

output "bucket_region" {
  description = "AWS Region in which the S3 bucket is deployed."
  value       = module.secure_bucket.bucket_region
}

output "bucket_domain_name" {
  description = "Regional DNS domain name of the S3 bucket."
  value       = module.secure_bucket.bucket_domain_name
}

output "bucket_hosted_zone_id" {
  description = "Route 53 hosted zone ID associated with the S3 bucket's Region-specific endpoint."
  value       = module.secure_bucket.bucket_hosted_zone_id
}

output "bucket_versioning_enabled" {
  description = "Whether versioning is enabled on the S3 bucket."
  value       = module.secure_bucket.bucket_versioning_enabled
}

output "bucket_kms_key_arn" {
  description = "Customer-managed KMS key ARN used for SSE-KMS, or null when SSE-S3 is used."
  value       = module.secure_bucket.bucket_kms_key_arn
}

output "bucket_encryption_algorithm" {
  description = "Server-side encryption algorithm configured for the S3 bucket."
  value       = module.secure_bucket.bucket_encryption_algorithm
}

output "lifecycle_configuration_id" {
  description = "Lifecycle configuration identifier, when lifecycle rules are managed by the s3-bucket module."
  value       = module.secure_bucket.lifecycle_configuration_id
}

output "server_access_logging_enabled" {
  description = "Whether server access logging is configured for the S3 bucket."
  value       = module.secure_bucket.server_access_logging_enabled
}

output "server_access_logging_target_bucket" {
  description = "Target bucket receiving server access logs, or null when logging is not configured."
  value       = module.secure_bucket.server_access_logging_target_bucket
}
