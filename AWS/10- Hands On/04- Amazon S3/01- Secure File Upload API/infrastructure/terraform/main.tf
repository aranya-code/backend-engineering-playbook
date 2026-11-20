locals {
  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  })

  s3_bucket_name = var.bucket_name != "" ? var.bucket_name : "${var.project_name}-${var.environment}-${var.aws_region}-${data.aws_caller_identity.current.account_id}"

  s3_upload_prefix = trimsuffix(var.s3_upload_prefix, "/") == "" ? "" : "${trimsuffix(var.s3_upload_prefix, "/")}/"

  s3_bucket_arn = aws_s3_bucket.uploads.arn

  s3_object_arn = "${aws_s3_bucket.uploads.arn}/*"

  kms_key_arn = aws_kms_key.s3_encryption.arn
}

data "aws_caller_identity" "current" {}

check "valid_environment" {
  assert {
    condition     = contains(["dev", "development", "staging", "prod", "production"], lower(var.environment))
    error_message = "environment must identify a supported deployment environment."
  }
}

check "valid_upload_prefix" {
  assert {
    condition     = !startswith(var.s3_upload_prefix, "/") && !strcontains(var.s3_upload_prefix, "..")
    error_message = "s3_upload_prefix must be a relative S3 prefix and must not contain '..'."
  }
}

check "kms_key_matches_bucket_region" {
  assert {
    condition     = aws_kms_key.s3_encryption.arn != ""
    error_message = "The S3 encryption KMS key must be available before the bucket configuration is applied."
  }
}