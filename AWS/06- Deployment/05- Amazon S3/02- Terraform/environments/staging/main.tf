terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Remote state is configured with backend.hcl.example during terraform init.
  backend "s3" {}
}

# -------------------------------------------------------------------
# Input Variables
# -------------------------------------------------------------------

variable "aws_region" {
  description = "AWS Region for the primary staging environment."
  type        = string
  default     = "ap-south-1"

  validation {
    condition     = length(trimspace(var.aws_region)) > 0
    error_message = "aws_region must not be empty."
  }
}

variable "replica_aws_region" {
  description = "AWS Region for the destination staging replication bucket."
  type        = string
  default     = "ap-southeast-1"

  validation {
    condition     = length(trimspace(var.replica_aws_region)) > 0
    error_message = "replica_aws_region must not be empty."
  }
}

variable "source_account_id" {
  description = "12-digit AWS account ID that owns the source bucket."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.source_account_id))
    error_message = "source_account_id must contain exactly 12 digits."
  }
}

variable "source_bucket_name" {
  description = "Globally unique name for the primary staging S3 bucket."
  type        = string

  validation {
    condition = (
      length(var.source_bucket_name) >= 3 &&
      length(var.source_bucket_name) <= 63 &&
      can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.source_bucket_name)) &&
      !can(regex("\\.\\.", var.source_bucket_name))
    )
    error_message = "source_bucket_name must be a valid S3 bucket name."
  }
}

variable "replica_bucket_name" {
  description = "Globally unique name for the destination staging S3 bucket."
  type        = string

  validation {
    condition = (
      length(var.replica_bucket_name) >= 3 &&
      length(var.replica_bucket_name) <= 63 &&
      can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.replica_bucket_name)) &&
      !can(regex("\\.\\.", var.replica_bucket_name))
    )
    error_message = "replica_bucket_name must be a valid S3 bucket name."
  }
}

variable "force_destroy" {
  description = "Whether Terraform may delete non-empty staging buckets. Keep false unless destructive cleanup is explicitly approved."
  type        = bool
  default     = false
}

variable "source_kms_key_arn" {
  description = "Optional customer-managed KMS key ARN for encrypting source bucket objects."
  type        = string
  default     = null
  nullable    = true
}

variable "destination_kms_key_arn" {
  description = "Optional customer-managed KMS key ARN for encrypting destination replicas."
  type        = string
  default     = null
  nullable    = true
}

variable "replication_role_name" {
  description = "IAM role name assumed by Amazon S3 for object replication."
  type        = string
  default     = "staging-s3-replication-role"

  validation {
    condition = (
      length(var.replication_role_name) >= 1 &&
      length(var.replication_role_name) <= 64 &&
      can(regex("^[A-Za-z0-9_+=,.@-]+$", var.replication_role_name))
    )
    error_message = "replication_role_name must contain 1-64 valid IAM role name characters."
  }
}

variable "replication_filter_prefix" {
  description = "Object key prefix selected for replication. An empty string selects all eligible objects."
  type        = string
  default     = ""
}

variable "replication_enabled" {
  description = "Whether the staging replication rule is enabled."
  type        = bool
  default     = true
}

variable "replication_metrics_enabled" {
  description = "Whether to enable S3 replication metrics."
  type        = bool
  default     = true
}

variable "replication_time_control_enabled" {
  description = "Whether to enable S3 Replication Time Control. This can incur additional charges."
  type        = bool
  default     = false
}

variable "destination_storage_class" {
  description = "Storage class used for destination replicas."
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
        "GLACIER_IR",
        "DEEP_ARCHIVE"
      ],
      var.destination_storage_class
    )
    error_message = "destination_storage_class must be a supported replication destination storage class."
  }
}

variable "tags" {
  description = "Common tags applied to staging S3 buckets and replication IAM resources."
  type        = map(string)
  default = {
    Environment = "staging"
    Project     = "amazon-s3-playbook"
    ManagedBy   = "terraform"
  }
}

# -------------------------------------------------------------------
# AWS Providers
# -------------------------------------------------------------------

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

provider "aws" {
  alias  = "replica"
  region = var.replica_aws_region

  default_tags {
    tags = var.tags
  }
}

# -------------------------------------------------------------------
# Locals
# -------------------------------------------------------------------

locals {
  environment = "staging"

  common_tags = merge(
    var.tags,
    {
      Environment = local.environment
      Project     = "amazon-s3-playbook"
      ManagedBy   = "terraform"
    }
  )
}

# -------------------------------------------------------------------
# Primary Source Bucket
# -------------------------------------------------------------------

module "source_bucket" {
  source = "../../modules/s3-bucket"

  bucket_name   = var.source_bucket_name
  force_destroy = var.force_destroy

  versioning_enabled = true

  kms_key_arn        = var.source_kms_key_arn
  bucket_key_enabled = true

  # Lifecycle configuration is intentionally managed separately
  # if a dedicated lifecycle module is introduced.
  lifecycle_rules = []

  tags = merge(
    local.common_tags,
    {
      Name = var.source_bucket_name
      Role = "replication-source"
    }
  )
}

# -------------------------------------------------------------------
# Destination Replication Bucket
# -------------------------------------------------------------------

module "replica_bucket" {
  source = "../../modules/s3-bucket"

  providers = {
    aws = aws.replica
  }

  bucket_name   = var.replica_bucket_name
  force_destroy = var.force_destroy

  versioning_enabled = true

  kms_key_arn        = var.destination_kms_key_arn
  bucket_key_enabled = true

  lifecycle_rules = []

  tags = merge(
    local.common_tags,
    {
      Name = var.replica_bucket_name
      Role = "replication-destination"
    }
  )
}

# -------------------------------------------------------------------
# S3 Cross-Region Replication
# -------------------------------------------------------------------

module "s3_replication" {
  source = "../../modules/s3-replication"

  source_bucket_id  = module.source_bucket.bucket_id
  source_bucket_arn = module.source_bucket.bucket_arn
  source_account_id = var.source_account_id

  destination_bucket_arn = module.replica_bucket.bucket_arn

  replication_role_name = var.replication_role_name

  replication_rule_id       = "staging-replication-rule"
  replication_rule_priority = 1
  replication_enabled       = var.replication_enabled

  replication_filter_prefix = var.replication_filter_prefix

  delete_marker_replication_enabled = false

  destination_storage_class = var.destination_storage_class

  source_kms_key_arn      = var.source_kms_key_arn
  destination_kms_key_arn = var.destination_kms_key_arn

  metrics_enabled                  = var.replication_metrics_enabled
  replication_time_control_enabled = var.replication_time_control_enabled

  tags = local.common_tags

  depends_on = [
    module.source_bucket,
    module.replica_bucket
  ]
}

# -------------------------------------------------------------------
# Outputs
# -------------------------------------------------------------------

output "environment" {
  description = "Deployment environment name."
  value       = local.environment
}

output "source_bucket_id" {
  description = "Name of the primary staging S3 bucket."
  value       = module.source_bucket.bucket_id
}

output "source_bucket_arn" {
  description = "ARN of the primary staging S3 bucket."
  value       = module.source_bucket.bucket_arn
}

output "source_bucket_region" {
  description = "AWS Region of the primary staging S3 bucket."
  value       = module.source_bucket.bucket_region
}

output "replica_bucket_id" {
  description = "Name of the destination staging S3 bucket."
  value       = module.replica_bucket.bucket_id
}

output "replica_bucket_arn" {
  description = "ARN of the destination staging S3 bucket."
  value       = module.replica_bucket.bucket_arn
}

output "replica_bucket_region" {
  description = "AWS Region of the destination staging S3 bucket."
  value       = module.replica_bucket.bucket_region
}

output "replication_role_arn" {
  description = "IAM role assumed by Amazon S3 to perform object replication."
  value       = module.s3_replication.replication_role_arn
}

output "replication_configuration_id" {
  description = "Identifier of the staging S3 replication configuration."
  value       = module.s3_replication.replication_configuration_id
}

output "replication_rule_status" {
  description = "Configured status of the staging replication rule."
  value       = module.s3_replication.replication_rule_status
}
