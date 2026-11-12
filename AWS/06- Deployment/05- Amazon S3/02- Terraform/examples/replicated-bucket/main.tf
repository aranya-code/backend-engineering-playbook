terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

variable "source_aws_region" {
  description = "AWS Region for the source S3 bucket."
  type        = string
  default     = "ap-south-1"
}

variable "destination_aws_region" {
  description = "AWS Region for the destination replica bucket."
  type        = string
  default     = "ap-southeast-1"

  validation {
    condition     = var.destination_aws_region != var.source_aws_region
    error_message = "destination_aws_region must differ from source_aws_region for this cross-Region replication example."
  }
}

variable "source_bucket_name" {
  description = "Globally unique name for the source S3 bucket."
  type        = string

  validation {
    condition = (
      length(var.source_bucket_name) >= 3 &&
      length(var.source_bucket_name) <= 63 &&
      can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.source_bucket_name)) &&
      !can(regex("\\.\\.", var.source_bucket_name)) &&
      !can(regex("\\.-|\\-\\.", var.source_bucket_name)) &&
      !can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}$", var.source_bucket_name))
    )
    error_message = "source_bucket_name must be a valid S3 general-purpose bucket name with 3-63 lowercase letters, numbers, dots, or hyphens."
  }
}

variable "destination_bucket_name" {
  description = "Globally unique name for the destination replica S3 bucket."
  type        = string

  validation {
    condition = (
      length(var.destination_bucket_name) >= 3 &&
      length(var.destination_bucket_name) <= 63 &&
      can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.destination_bucket_name)) &&
      !can(regex("\\.\\.", var.destination_bucket_name)) &&
      !can(regex("\\.-|\\-\\.", var.destination_bucket_name)) &&
      !can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}$", var.destination_bucket_name))
    )
    error_message = "destination_bucket_name must be a valid S3 general-purpose bucket name with 3-63 lowercase letters, numbers, dots, or hyphens."
  }
}

variable "source_account_id" {
  description = "12-digit AWS account ID that owns the source bucket and replication role."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.source_account_id))
    error_message = "source_account_id must be a 12-digit AWS account ID."
  }
}

variable "force_destroy" {
  description = "Allow Terraform to delete non-empty buckets. Keep false for production and protected data."
  type        = bool
  default     = false
}

variable "source_kms_key_arn" {
  description = "Optional customer-managed KMS key ARN used to encrypt source objects. Null uses SSE-S3."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      var.source_kms_key_arn == null ||
      can(regex("^arn:[^:]+:kms:[^:]+:[0-9]{12}:key/.+$", var.source_kms_key_arn))
    )
    error_message = "source_kms_key_arn must be null or a valid customer-managed KMS key ARN."
  }
}

variable "destination_kms_key_arn" {
  description = "Optional customer-managed KMS key ARN used to encrypt replicated objects. Null uses SSE-S3."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      var.destination_kms_key_arn == null ||
      can(regex("^arn:[^:]+:kms:[^:]+:[0-9]{12}:key/.+$", var.destination_kms_key_arn))
    )
    error_message = "destination_kms_key_arn must be null or a valid customer-managed KMS key ARN."
  }
}

variable "bucket_key_enabled" {
  description = "Enable S3 Bucket Keys for buckets using SSE-KMS."
  type        = bool
  default     = true
}

variable "replication_role_name" {
  description = "Name of the IAM role assumed by the S3 replication service."
  type        = string
  default     = "s3-cross-region-replication-role"
}

variable "replication_rule_id" {
  description = "Unique identifier for the S3 replication rule."
  type        = string
  default     = "cross-region-replication-rule"
}

variable "replication_filter_prefix" {
  description = "Object-key prefix to replicate. An empty string applies the rule to all eligible objects."
  type        = string
  default     = ""
}

variable "replication_enabled" {
  description = "Enable or disable the replication rule."
  type        = bool
  default     = true
}

variable "delete_marker_replication_enabled" {
  description = "Replicate delete markers for objects matching the replication filter."
  type        = bool
  default     = false
}

variable "destination_storage_class" {
  description = "Storage class used for replicated objects."
  type        = string
  default     = "STANDARD"

  validation {
    condition = contains(
      [
        "STANDARD",
        "STANDARD_IA",
        "ONEZONE_IA",
        "INTELLIGENT_TIERING",
        "GLACIER",
        "DEEP_ARCHIVE",
        "GLACIER_IR"
      ],
      var.destination_storage_class
    )
    error_message = "destination_storage_class must be a supported S3 replication destination storage class."
  }
}

variable "replication_metrics_enabled" {
  description = "Enable replication metrics for the replication rule."
  type        = bool
  default     = true
}

variable "replication_time_control_enabled" {
  description = "Enable S3 Replication Time Control. Additional charges apply."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags applied to the buckets and supported resources."
  type        = map(string)
  default = {
    Environment = "example"
    Project     = "amazon-s3-playbook"
    ManagedBy   = "terraform"
    Purpose     = "cross-region-replication"
  }
}

provider "aws" {
  region = var.source_aws_region

  default_tags {
    tags = var.tags
  }
}

provider "aws" {
  alias  = "destination"
  region = var.destination_aws_region

  default_tags {
    tags = var.tags
  }
}

locals {
  replication_rule_status = var.replication_enabled ? "Enabled" : "Disabled"

  source_bucket_arn      = aws_s3_bucket.source.arn
  destination_bucket_arn = aws_s3_bucket.destination.arn

  source_kms_policy_statements = var.source_kms_key_arn == null ? [] : [
    {
      Sid    = "DecryptSourceObjects"
      Effect = "Allow"
      Action = [
        "kms:Decrypt"
      ]
      Resource = var.source_kms_key_arn
    }
  ]

  destination_kms_policy_statements = var.destination_kms_key_arn == null ? [] : [
    {
      Sid    = "EncryptDestinationObjects"
      Effect = "Allow"
      Action = [
        "kms:Encrypt",
        "kms:GenerateDataKey",
        "kms:ReEncrypt*"
      ]
      Resource = var.destination_kms_key_arn
    }
  ]

  replication_policy_statements = concat(
    [
      {
        Sid    = "ReadSourceBucketReplicationConfiguration"
        Effect = "Allow"
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Resource = local.source_bucket_arn
      },
      {
        Sid    = "ReadSourceObjectVersions"
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Resource = "${local.source_bucket_arn}/*"
      },
      {
        Sid    = "ReplicateObjectsToDestination"
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ]
        Resource = "${local.destination_bucket_arn}/*"
      }
    ],
    local.source_kms_policy_statements,
    local.destination_kms_policy_statements
  )
}

resource "aws_s3_bucket" "source" {
  bucket        = var.source_bucket_name
  force_destroy = var.force_destroy

  tags = merge(
    var.tags,
    {
      Name = var.source_bucket_name
      Role = "source"
    }
  )
}

resource "aws_s3_bucket" "destination" {
  provider      = aws.destination
  bucket        = var.destination_bucket_name
  force_destroy = var.force_destroy

  tags = merge(
    var.tags,
    {
      Name = var.destination_bucket_name
      Role = "replica"
    }
  )
}

resource "aws_s3_bucket_ownership_controls" "source" {
  bucket = aws_s3_bucket.source.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_ownership_controls" "destination" {
  provider = aws.destination
  bucket   = aws_s3_bucket.destination.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "source" {
  bucket = aws_s3_bucket.source.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "destination" {
  provider = aws.destination
  bucket   = aws_s3_bucket.destination.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "source" {
  bucket = aws_s3_bucket.source.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "destination" {
  provider = aws.destination
  bucket   = aws_s3_bucket.destination.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "source" {
  bucket = aws_s3_bucket.source.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.source_kms_key_arn == null ? "AES256" : "aws:kms"
      kms_master_key_id = var.source_kms_key_arn
    }

    bucket_key_enabled = var.source_kms_key_arn == null ? false : var.bucket_key_enabled
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "destination" {
  provider = aws.destination
  bucket   = aws_s3_bucket.destination.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.destination_kms_key_arn == null ? "AES256" : "aws:kms"
      kms_master_key_id = var.destination_kms_key_arn
    }

    bucket_key_enabled = var.destination_kms_key_arn == null ? false : var.bucket_key_enabled
  }
}

data "aws_iam_policy_document" "replication_assume_role" {
  statement {
    sid     = "AllowS3ReplicationService"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.source_account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [local.source_bucket_arn]
    }
  }
}

resource "aws_iam_role" "replication" {
  name               = var.replication_role_name
  assume_role_policy = data.aws_iam_policy_document.replication_assume_role.json

  tags = var.tags
}

resource "aws_iam_role_policy" "replication" {
  name = "${var.replication_role_name}-policy"
  role = aws_iam_role.replication.id

  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = local.replication_policy_statements
  })
}

resource "aws_s3_bucket_replication_configuration" "this" {
  bucket = aws_s3_bucket.source.id
  role   = aws_iam_role.replication.arn

  rule {
    id       = var.replication_rule_id
    priority = 1
    status   = local.replication_rule_status

    filter {
      prefix = var.replication_filter_prefix
    }

    delete_marker_replication {
      status = var.delete_marker_replication_enabled ? "Enabled" : "Disabled"
    }

    destination {
      bucket        = local.destination_bucket_arn
      storage_class = var.destination_storage_class

      dynamic "encryption_configuration" {
        for_each = var.destination_kms_key_arn == null ? [] : [var.destination_kms_key_arn]

        content {
          replica_kms_key_id = encryption_configuration.value
        }
      }

      dynamic "metrics" {
        for_each = var.replication_metrics_enabled ? [true] : []

        content {
          status = "Enabled"

          event_threshold {
            minutes = 15
          }
        }
      }

      dynamic "replication_time" {
        for_each = var.replication_time_control_enabled ? [true] : []

        content {
          status = "Enabled"

          time {
            minutes = 15
          }
        }
      }
    }

    dynamic "source_selection_criteria" {
      for_each = var.source_kms_key_arn == null ? [] : [true]

      content {
        sse_kms_encrypted_objects {
          status = "Enabled"
        }
      }
    }
  }

  lifecycle {
    precondition {
      condition = (
        var.source_kms_key_arn == null ||
        var.destination_kms_key_arn != null
      )
      error_message = "When source objects use SSE-KMS, configure destination_kms_key_arn so replicated objects can be encrypted with a destination key."
    }

    precondition {
      condition = (
        !var.replication_time_control_enabled ||
        var.replication_metrics_enabled
      )
      error_message = "Replication Time Control requires replication metrics to be enabled."
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.source,
    aws_s3_bucket_versioning.destination,
    aws_s3_bucket_server_side_encryption_configuration.source,
    aws_s3_bucket_server_side_encryption_configuration.destination,
    aws_iam_role_policy.replication
  ]
}

output "source_bucket_id" {
  description = "Name of the source S3 bucket."
  value       = aws_s3_bucket.source.id
}

output "source_bucket_arn" {
  description = "ARN of the source S3 bucket."
  value       = aws_s3_bucket.source.arn
}

output "source_bucket_region" {
  description = "AWS Region of the source S3 bucket."
  value       = aws_s3_bucket.source.region
}

output "destination_bucket_id" {
  description = "Name of the destination replica S3 bucket."
  value       = aws_s3_bucket.destination.id
}

output "destination_bucket_arn" {
  description = "ARN of the destination replica S3 bucket."
  value       = aws_s3_bucket.destination.arn
}

output "destination_bucket_region" {
  description = "AWS Region of the destination replica S3 bucket."
  value       = aws_s3_bucket.destination.region
}

output "replication_role_arn" {
  description = "ARN of the IAM role assumed by the S3 replication service."
  value       = aws_iam_role.replication.arn
}

output "replication_role_name" {
  description = "Name of the IAM replication role."
  value       = aws_iam_role.replication.name
}

output "replication_configuration_id" {
  description = "Identifier of the source bucket replication configuration."
  value       = aws_s3_bucket_replication_configuration.this.id
}

output "replication_rule_id" {
  description = "Identifier of the configured replication rule."
  value       = var.replication_rule_id
}

output "replication_rule_status" {
  description = "Configured replication rule status."
  value       = local.replication_rule_status
}

output "replication_metrics_enabled" {
  description = "Whether replication metrics are enabled."
  value       = var.replication_metrics_enabled
}

output "replication_time_control_enabled" {
  description = "Whether S3 Replication Time Control is enabled."
  value       = var.replication_time_control_enabled
}

output "source_kms_key_arn" {
  description = "KMS key ARN configured for source bucket encryption."
  value       = var.source_kms_key_arn
}

output "destination_kms_key_arn" {
  description = "KMS key ARN configured for destination bucket encryption."
  value       = var.destination_kms_key_arn
}
