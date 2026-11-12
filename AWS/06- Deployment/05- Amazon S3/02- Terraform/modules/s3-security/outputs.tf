output "public_access_block_id" {
  description = "ID of the S3 bucket public access block configuration."
  value       = aws_s3_bucket_public_access_block.this.id
}

output "ownership_controls_id" {
  description = "ID of the S3 bucket ownership controls configuration."
  value       = aws_s3_bucket_ownership_controls.this.id
}

output "server_side_encryption_configuration_id" {
  description = "ID of the S3 bucket server-side encryption configuration."
  value       = aws_s3_bucket_server_side_encryption_configuration.this.id
}

output "bucket_policy_id" {
  description = "ID of the S3 bucket policy."
  value       = aws_s3_bucket_policy.this.id
}

output "bucket_policy_json" {
  description = "Rendered bucket policy JSON managed by this module."
  value       = data.aws_iam_policy_document.this.json
  sensitive   = true
}

output "cors_configuration_id" {
  description = "ID of the S3 bucket CORS configuration, or null when no CORS rules are configured."
  value       = try(aws_s3_bucket_cors_configuration.this[0].id, null)
}

output "request_payment_configuration_id" {
  description = "ID of the S3 Requester Pays configuration, or null when Requester Pays is disabled."
  value       = try(aws_s3_bucket_request_payment_configuration.this[0].id, null)
}

output "encryption_algorithm" {
  description = "Configured default server-side encryption algorithm."
  value       = var.kms_key_arn == null ? "AES256" : "aws:kms"
}

output "kms_key_arn" {
  description = "Customer-managed KMS key ARN configured for default bucket encryption, or null when SSE-S3 is used."
  value       = var.kms_key_arn
}

output "bucket_key_enabled" {
  description = "Whether S3 Bucket Keys are enabled for SSE-KMS encryption."
  value       = var.kms_key_arn != null ? var.bucket_key_enabled : false
}

output "public_access_block_enabled" {
  description = "Indicates that all four S3 Block Public Access settings are enabled by this module."
  value       = true
}

output "object_ownership" {
  description = "Object ownership mode configured by this module."
  value       = "BucketOwnerEnforced"
}

output "allowed_principal_arns" {
  description = "IAM principal ARNs granted the configured S3 actions by the bucket policy."
  value       = var.allowed_principal_arns
}

output "allowed_actions" {
  description = "S3 actions granted to the configured principals by the bucket policy."
  value       = var.allowed_actions
}

output "cors_enabled" {
  description = "Whether one or more CORS rules are configured."
  value       = length(var.cors_rules) > 0
}

output "request_payer_enabled" {
  description = "Whether Requester Pays is enabled for the bucket."
  value       = var.request_payer_enabled
}
