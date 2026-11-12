terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

variable "aws_region" {
  description = "AWS Region in which the versioned S3 bucket is created."
  type        = string
  default     = "ap-south-1"
}

variable "bucket_name" {
  description = "Globally unique name for the versioned S3 bucket."
  type        = string

  validation {
    condition = (
      length(var.bucket_name) >= 3 &&
      length(var.bucket_name) <= 63 &&
      can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.bucket_name)) &&
      !can(regex("\\.\\.", var.bucket_name)) &&
      !can(regex("\\.-|\\-\\.", var.bucket_name)) &&
      !can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}$", var.bucket_name))
    )
    error_message = "bucket_name must be a valid S3 general-purpose bucket name with 3-63 lowercase letters, numbers, dots, or hyphens."
  }
}

variable "force_destroy" {
  description = "Allow Terraform to delete a non-empty bucket. Keep false for production and protected data."
  type        = bool
  default     = false
}

variable "kms_key_arn" {
  description = "Optional customer-managed KMS key ARN. Null uses SSE-S3 encryption."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      var.kms_key_arn == null ||
      can(regex("^arn:[^:]+:kms:[^:]+:[0-9]{12}:key/.+$", var.kms_key_arn))
    )
    error_message = "kms_key_arn must be null or a valid customer-managed KMS key ARN."
  }
}

variable "bucket_key_enabled" {
  description = "Enable S3 Bucket Keys when SSE-KMS is configured."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags applied to the bucket and supported resources."
  type        = map(string)
  default = {
    Environment = "example"
    Project     = "amazon-s3-playbook"
    ManagedBy   = "terraform"
    Purpose     = "versioned-bucket-example"
  }
}

resource "aws_s3_bucket" "versioned" {
  bucket        = var.bucket_name
  force_destroy = var.force_destroy

  tags = var.tags
}

resource "aws_s3_bucket_ownership_controls" "versioned" {
  bucket = aws_s3_bucket.versioned.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "versioned" {
  bucket = aws_s3_bucket.versioned.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "versioned" {
  bucket = aws_s3_bucket.versioned.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "versioned" {
  bucket = aws_s3_bucket.versioned.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn == null ? "AES256" : "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }

    bucket_key_enabled = var.kms_key_arn == null ? false : var.bucket_key_enabled
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "versioned" {
  bucket = aws_s3_bucket.versioned.id

  rule {
    id     = "manage-noncurrent-object-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 90
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.versioned
  ]
}

output "bucket_id" {
  description = "Name of the versioned S3 bucket."
  value       = aws_s3_bucket.versioned.id
}

output "bucket_arn" {
  description = "ARN of the versioned S3 bucket."
  value       = aws_s3_bucket.versioned.arn
}

output "bucket_region" {
  description = "AWS Region in which the bucket is deployed."
  value       = aws_s3_bucket.versioned.region
}

output "bucket_versioning_status" {
  description = "Versioning status configured for the bucket."
  value       = aws_s3_bucket_versioning.versioned.versioning_configuration[0].status
}

output "bucket_encryption_algorithm" {
  description = "Server-side encryption algorithm configured for the bucket."
  value       = aws_s3_bucket_server_side_encryption_configuration.versioned.rule[0].apply_server_side_encryption_by_default[0].sse_algorithm
}

output "bucket_kms_key_arn" {
  description = "Customer-managed KMS key ARN, or null when SSE-S3 is used."
  value       = var.kms_key_arn
}

output "lifecycle_configuration_id" {
  description = "Identifier of the bucket lifecycle configuration."
  value       = aws_s3_bucket_lifecycle_configuration.versioned.id
}
