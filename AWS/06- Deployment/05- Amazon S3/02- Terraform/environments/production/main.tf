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

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------

variable "aws_region" {
  description = "AWS Region for the production source bucket."
  type        = string
  default     = "ap-south-1"

  validation {
    condition     = length(trimspace(var.aws_region)) > 0
    error_message = "aws_region must not be empty."
  }
}

variable "replica_aws_region" {
  description = "AWS Region for the production replica bucket."
  type        = string
  default     = "ap-southeast-1"

  validation {
    condition     = length(trimspace(var.replica_aws_region)) > 0
    error_message = "replica_aws_region must not be empty."
  }

  validation {
    condition     = var.replica_aws_region != var.aws_region
    error_message = "The replica Region must differ from the source Region for this cross-Region replication configuration."
  }
}

variable "source_account_id" {
  description = "12-digit AWS account ID that owns the production source bucket."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.source_account_id))
    error_message = "source_account_id must be a 12-digit AWS account ID."
  }
}

variable "source_bucket_name" {
  description = "Globally unique name for the production source bucket."
  type        = string

  validation {
    condition = (
      length(var.source_bucket_name) >= 3 &&
      length(var.source_bucket_name) <= 63 &&
      can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.source_bucket_name)) &&
      !can(regex("\\.\\.", var.source_bucket_name)) &&
      !can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+$", var.source_bucket_name))
    )
    error_message = "source_bucket_name must be a valid S3 bucket name between 3 and 63 characters."
  }
}

variable "replica_bucket_name" {
  description = "Globally unique name for the production replica bucket."
  type        = string

  validation {
    condition = (
      length(var.replica_bucket_name) >= 3 &&
      length(var.replica_bucket_name) <= 63 &&
      can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.replica_bucket_name)) &&
      !can(regex("\\.\\.", var.replica_bucket_name)) &&
      !can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+$", var.replica_bucket_name))
    )
    error_message = "replica_bucket_name must be a valid S3 bucket name between 3 and 63 characters."
  }

  validation {
    condition     = var.replica_bucket_name != var.source_bucket_name
    error_message = "The source and replica bucket names must be different."
  }
}

variable "force_destroy" {
  description = "Whether Terraform may delete non-empty buckets. Keep false for production."
  type        = bool
  default     = false
}

variable "source_kms_key_arn" {
  description = "Optional customer-managed KMS key ARN for source bucket encryption."
  type        = string
  default     = null
  nullable    = true
}

variable "destination_kms_key_arn" {
  description = "Optional customer-managed KMS key ARN for replica bucket encryption."
  type        = string
  default     = null
  nullable    = true
}

variable "replication_role_name" {
  description = "IAM role assumed by Amazon S3 for production replication."
  type        = string
  default     = "production-s3-replication-role"

  validation {
    condition     = length(var.replication_role_name) >= 1 && length(var.replication_role_name) <= 64
    error_message = "replication_role_name must contain between 1 and 64 characters."
  }
}

variable "replication_filter_prefix" {
  description = "Object key prefix selected by the replication rule. Empty selects all eligible objects."
  type        = string
  default     = ""
}

variable "replication_enabled" {
  description = "Whether the production replication rule is enabled."
  type        = bool
  default     = true
}

variable "replication_metrics_enabled" {
  description = "Whether replication metrics are enabled."
  type        = bool
  default     = true
}

variable "replication_time_control_enabled" {
  description = "Whether S3 Replication Time Control is enabled. Additional charges apply."
  type        = bool
  default     = false
}

variable "destination_storage_class" {
  description = "Storage class used for replicated objects."
  type        = string
  default     = "STANDARD"

  validation {
    condition = contains([
      "STANDARD",
      "STANDARD_IA",
      "ONEZONE_IA",
      "INTELLIGENT_TIERING",
      "GLACIER_IR",
      "GLACIER",
      "DEEP_ARCHIVE"
    ], var.destination_storage_class)
    error_message = "destination_storage_class must be a supported S3 replication destination storage class."
  }
}

variable "tags" {
  description = "Common tags applied to production resources."
  type        = map(string)

  default = {
    Environment = "production"
    Project     = "amazon-s3-playbook"
    ManagedBy   = "terraform"
    Criticality = "high"
  }
}

# ---------------------------------------------------------------------------
# AWS providers
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Shared configuration
# ---------------------------------------------------------------------------

locals {
  environment = "production"

  common_tags = merge(var.tags, {
    Environment = local.environment
    Project     = "amazon-s3-playbook"
    ManagedBy   = "terraform"
  })
}

# ---------------------------------------------------------------------------
# Source bucket
# ---------------------------------------------------------------------------

module "source_bucket" {
  source = "../../modules/s3-bucket"

  bucket_name  = var.source_bucket_name
  force_destroy = var.force_destroy

  versioning_enabled = true

  kms_key_arn       = var.source_kms_key_arn
  bucket_key_enabled = true

  # Lifecycle configuration is managed separately when the dedicated
  # s3-lifecycle module is introduced into this environment.
  lifecycle_rules = []

  tags = merge(local.common_tags, {
    Name = var.source_bucket_name
    Role = "production-source"
  })
}

# ---------------------------------------------------------------------------
# Replica bucket
# ---------------------------------------------------------------------------

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

  tags = merge(local.common_tags, {
    Name = var.replica_bucket_name
    Role = "production-replica"
  })
}

# ---------------------------------------------------------------------------
# Cross-Region replication
# ---------------------------------------------------------------------------

module "s3_replication" {
  source = "../../modules/s3-replication"

  source_bucket_id  = module.source_bucket.bucket_id
  source_bucket_arn = module.source_bucket.bucket_arn
  source_account_id = var.source_account_id

  destination_bucket_arn = module.replica_bucket.bucket_arn

  replication_role_name = var.replication_role_name

  replication_rule_id       = "production-replication-rule"
  replication_rule_priority = 1

  replication_enabled       = var.replication_enabled
  replication_filter_prefix = var.replication_filter_prefix

  delete_marker_replication_enabled = false

  destination_storage_class = var.destination_storage_class

  source_kms_key_arn      = var.source_kms_key_arn
  destination_kms_key_arn = var.destination_kms_key_arn

  metrics_enabled = var.replication_metrics_enabled

  replication_time_control_enabled = var.replication_time_control_enabled

  tags = merge(local.common_tags, {
    Name = "production-s3-replication"
    Role = "replication"
  })

  depends_on = [
    module.source_bucket,
    module.replica_bucket
  ]
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

output "environment" {
  description = "Deployment environment."
  value       = local.environment
}

output "source_bucket_id" {
  description = "Production source bucket name."
  value       = module.source_bucket.bucket_id
}

output "source_bucket_arn" {
  description = "Production source bucket ARN."
  value       = module.source_bucket.bucket_arn
}

output "source_bucket_region" {
  description = "AWS Region hosting the production source bucket."
  value       = module.source_bucket.bucket_region
}

output "replica_bucket_id" {
  description = "Production replica bucket name."
  value       = module.replica_bucket.bucket_id
}

output "replica_bucket_arn" {
  description = "Production replica bucket ARN."
  value       = module.replica_bucket.bucket_arn
}

output "replica_bucket_region" {
  description = "AWS Region hosting the production replica bucket."
  value       = module.replica_bucket.bucket_region
}

output "replication_role_arn" {
  description = "IAM role ARN assumed by Amazon S3 for replication."
  value       = module.s3_replication.replication_role_arn
}

output "replication_configuration_id" {
  description = "Replication configuration identifier."
  value       = module.s3_replication.replication_configuration_id
}

output "replication_rule_status" {
  description = "Status of the production replication rule."
  value       = module.s3_replication.replication_rule_status
}
