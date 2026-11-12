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
  description = "AWS Region in which the lifecycle-managed S3 bucket is created."
  type        = string
  default     = "ap-south-1"

  validation {
    condition     = can(regex("^[a-z]{2}(-gov)?-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "aws_region must be a valid AWS Region identifier."
  }
}

variable "bucket_name" {
  description = "Globally unique name for the lifecycle-managed S3 bucket."
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

variable "current_version_expiration_days" {
  description = "Number of days after object creation before current object versions are eligible for expiration. Null disables current-version expiration."
  type        = number
  default     = null
  nullable    = true

  validation {
    condition = (
      var.current_version_expiration_days == null ||
      (
        var.current_version_expiration_days >= 1 &&
        floor(var.current_version_expiration_days) == var.current_version_expiration_days
      )
    )
    error_message = "current_version_expiration_days must be null or a positive whole number."
  }
}

variable "noncurrent_version_expiration_days" {
  description = "Number of days after becoming noncurrent before object versions are eligible for expiration."
  type        = number
  default     = 90

  validation {
    condition = (
      var.noncurrent_version_expiration_days >= 1 &&
      floor(var.noncurrent_version_expiration_days) == var.noncurrent_version_expiration_days
    )
    error_message = "noncurrent_version_expiration_days must be a positive whole number."
  }
}

variable "abort_incomplete_multipart_upload_days" {
  description = "Number of days after initiation before incomplete multipart uploads are aborted."
  type        = number
  default     = 7

  validation {
    condition = (
      var.abort_incomplete_multipart_upload_days >= 1 &&
      floor(var.abort_incomplete_multipart_upload_days) == var.abort_incomplete_multipart_upload_days
    )
    error_message = "abort_incomplete_multipart_upload_days must be a positive whole number."
  }
}

variable "transition_to_standard_ia_days" {
  description = "Optional number of days after object creation before current objects transition to STANDARD_IA. Null disables this transition."
  type        = number
  default     = null
  nullable    = true

  validation {
    condition = (
      var.transition_to_standard_ia_days == null ||
      (
        var.transition_to_standard_ia_days >= 30 &&
        floor(var.transition_to_standard_ia_days) == var.transition_to_standard_ia_days
      )
    )
    error_message = "transition_to_standard_ia_days must be null or a whole number of at least 30 days."
  }
}

variable "transition_to_glacier_days" {
  description = "Optional number of days after object creation before current objects transition to GLACIER Flexible Retrieval. Null disables this transition."
  type        = number
  default     = null
  nullable    = true

  validation {
    condition = (
      var.transition_to_glacier_days == null ||
      (
        var.transition_to_glacier_days >= 0 &&
        floor(var.transition_to_glacier_days) == var.transition_to_glacier_days
      )
    )
    error_message = "transition_to_glacier_days must be null or a non-negative whole number."
  }
}

variable "lifecycle_filter_prefix" {
  description = "Optional object-key prefix to which the lifecycle rules apply. An empty string applies the rules to the entire bucket."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags applied to the bucket and supported resources."
  type        = map(string)
  default = {
    Environment = "example"
    Project     = "amazon-s3-playbook"
    ManagedBy   = "terraform"
    Purpose     = "lifecycle-managed-bucket"
  }
}

locals {
  lifecycle_transitions = concat(
    var.transition_to_standard_ia_days == null ? [] : [
      {
        days          = var.transition_to_standard_ia_days
        storage_class = "STANDARD_IA"
      }
    ],
    var.transition_to_glacier_days == null ? [] : [
      {
        days          = var.transition_to_glacier_days
        storage_class = "GLACIER"
      }
    ]
  )

  lifecycle_transitions_ordered = [
    for transition in local.lifecycle_transitions :
    transition
  ]

  lifecycle_transition_days_valid = (
    length(local.lifecycle_transitions_ordered) < 2 ||
    local.lifecycle_transitions_ordered[0].days < local.lifecycle_transitions_ordered[1].days
  )
}

resource "aws_s3_bucket" "lifecycle_managed" {
  bucket        = var.bucket_name
  force_destroy = var.force_destroy

  tags = var.tags
}

resource "aws_s3_bucket_ownership_controls" "lifecycle_managed" {
  bucket = aws_s3_bucket.lifecycle_managed.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "lifecycle_managed" {
  bucket = aws_s3_bucket.lifecycle_managed.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "lifecycle_managed" {
  bucket = aws_s3_bucket.lifecycle_managed.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lifecycle_managed" {
  bucket = aws_s3_bucket.lifecycle_managed.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn == null ? "AES256" : "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }

    bucket_key_enabled = var.kms_key_arn == null ? false : var.bucket_key_enabled
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "lifecycle_managed" {
  bucket = aws_s3_bucket.lifecycle_managed.id

  rule {
    id     = "manage-current-object-versions"
    status = "Enabled"

    filter {
      prefix = var.lifecycle_filter_prefix
    }

    dynamic "expiration" {
      for_each = var.current_version_expiration_days == null ? [] : [var.current_version_expiration_days]

      content {
        days = expiration.value
      }
    }

    dynamic "transition" {
      for_each = local.lifecycle_transitions_ordered

      content {
        days          = transition.value.days
        storage_class = transition.value.storage_class
      }
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = var.abort_incomplete_multipart_upload_days
    }
  }

  rule {
    id     = "manage-noncurrent-object-versions"
    status = "Enabled"

    filter {
      prefix = var.lifecycle_filter_prefix
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }

  lifecycle {
    precondition {
      condition     = local.lifecycle_transition_days_valid
      error_message = "When both storage transitions are configured, STANDARD_IA must occur before GLACIER."
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.lifecycle_managed
  ]
}

output "bucket_id" {
  description = "Name of the lifecycle-managed S3 bucket."
  value       = aws_s3_bucket.lifecycle_managed.id
}

output "bucket_arn" {
  description = "ARN of the lifecycle-managed S3 bucket."
  value       = aws_s3_bucket.lifecycle_managed.arn
}

output "bucket_region" {
  description = "AWS Region in which the bucket is deployed."
  value       = aws_s3_bucket.lifecycle_managed.region
}

output "bucket_versioning_status" {
  description = "Versioning status configured for the bucket."
  value       = aws_s3_bucket_versioning.lifecycle_managed.versioning_configuration[0].status
}

output "bucket_encryption_algorithm" {
  description = "Server-side encryption algorithm configured for the bucket."
  value       = aws_s3_bucket_server_side_encryption_configuration.lifecycle_managed.rule[0].apply_server_side_encryption_by_default[0].sse_algorithm
}

output "bucket_kms_key_arn" {
  description = "Customer-managed KMS key ARN, or null when SSE-S3 is used."
  value       = var.kms_key_arn
}

output "lifecycle_configuration_id" {
  description = "Identifier of the bucket lifecycle configuration."
  value       = aws_s3_bucket_lifecycle_configuration.lifecycle_managed.id
}

output "lifecycle_filter_prefix" {
  description = "Object-key prefix to which lifecycle rules apply."
  value       = var.lifecycle_filter_prefix
}

output "noncurrent_version_expiration_days" {
  description = "Configured noncurrent object version expiration period."
  value       = var.noncurrent_version_expiration_days
}

output "abort_incomplete_multipart_upload_days" {
  description = "Configured incomplete multipart upload cleanup period."
  value       = var.abort_incomplete_multipart_upload_days
}
