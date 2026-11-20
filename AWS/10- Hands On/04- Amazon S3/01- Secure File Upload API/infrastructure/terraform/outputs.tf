output "s3_bucket_name" {
  description = "Name of the S3 bucket used by the secure file upload API."
  value       = aws_s3_bucket.uploads.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket used by the secure file upload API."
  value       = aws_s3_bucket.uploads.arn
}

output "s3_bucket_region" {
  description = "AWS Region in which the S3 bucket is provisioned."
  value       = aws_s3_bucket.uploads.region
}

output "s3_upload_prefix" {
  description = "Object key prefix allocated to application uploads."
  value       = local.s3_upload_prefix
}

output "s3_bucket_domain_name" {
  description = "Regional DNS name of the S3 bucket."
  value       = aws_s3_bucket.uploads.bucket_regional_domain_name
}

output "s3_bucket_versioning_status" {
  description = "Versioning status configured for the S3 bucket."
  value       = aws_s3_bucket_versioning.uploads.versioning_configuration[0].status
}

output "s3_bucket_encryption_configuration" {
  description = "Default server-side encryption configuration for the S3 bucket."
  value       = aws_s3_bucket_server_side_encryption_configuration.uploads.rule[0].apply_server_side_encryption_by_default[0].sse_algorithm
}

output "kms_key_id" {
  description = "ID of the customer-managed KMS key used for S3 encryption."
  value       = aws_kms_key.s3_encryption.key_id
}

output "kms_key_arn" {
  description = "ARN of the customer-managed KMS key used for S3 encryption."
  value       = aws_kms_key.s3_encryption.arn
}

output "kms_key_alias" {
  description = "Alias of the customer-managed KMS key used for S3 encryption."
  value       = aws_kms_alias.s3_encryption.name
}

output "application_iam_role_name" {
  description = "IAM role name for the secure file upload API runtime."
  value       = aws_iam_role.s3_upload_api.name
}

output "application_iam_role_arn" {
  description = "IAM role ARN for the secure file upload API runtime."
  value       = aws_iam_role.s3_upload_api.arn
}

output "application_iam_policy_arn" {
  description = "ARN of the least-privilege S3 and KMS access policy."
  value       = aws_iam_policy.s3_upload_api_access.arn
}

output "aws_account_id" {
  description = "AWS account ID in which the infrastructure is provisioned."
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  description = "AWS Region used for the infrastructure deployment."
  value       = var.aws_region
}