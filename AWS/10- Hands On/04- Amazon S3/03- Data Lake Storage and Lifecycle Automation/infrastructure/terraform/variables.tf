variable "aws_region" {
  description = "AWS Region in which the data lake infrastructure will be deployed."
  type        = string
  default     = "ap-south-1"

  validation {
    condition     = can(regex("^[a-z]{2}(-gov)?-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "The AWS Region must be a valid Region identifier, such as ap-south-1."
  }
}

variable "environment" {
  description = "Deployment environment used for resource naming and tagging."
  type        = string
  default     = "dev"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,19}$", var.environment))
    error_message = "Environment must start with a lowercase letter and contain only lowercase letters, digits, or hyphens (2-20 characters)."
  }
}

variable "bucket_name_prefix" {
  description = "Globally unique prefix used to construct the data lake S3 bucket names."
  type        = string
  default     = "data-lake"

  validation {
    condition = (
      length(var.bucket_name_prefix) >= 3 &&
      length(var.bucket_name_prefix) <= 37 &&
      can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.bucket_name_prefix))
    )
    error_message = "Bucket name prefix must contain 3-37 lowercase letters, digits, or hyphens and must start and end with an alphanumeric character."
  }
}

variable "bucket_name_suffix" {
  description = "Globally unique suffix for S3 bucket names, such as an account identifier or deployment identifier."
  type        = string

  validation {
    condition = (
      length(var.bucket_name_suffix) >= 3 &&
      length(var.bucket_name_suffix) <= 20 &&
      can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.bucket_name_suffix))
    )
    error_message = "Bucket name suffix must contain 3-20 lowercase letters, digits, or hyphens and must start and end with an alphanumeric character."
  }
}

variable "force_destroy_buckets" {
  description = "Allow Terraform to delete non-empty project buckets. Keep false for production environments."
  type        = bool
  default     = false
}

variable "enable_bucket_versioning" {
  description = "Enable S3 bucket versioning for data recovery and lifecycle management."
  type        = bool
  default     = true
}

variable "enable_bucket_key" {
  description = "Enable S3 Bucket Keys for SSE-KMS objects to reduce KMS request costs."
  type        = bool
  default     = true
}

variable "kms_key_deletion_window_in_days" {
  description = "Waiting period before a customer-managed KMS key is permanently deleted."
  type        = number
  default     = 30

  validation {
    condition = (
      var.kms_key_deletion_window_in_days >= 7 &&
      var.kms_key_deletion_window_in_days <= 30
    )
    error_message = "KMS key deletion window must be between 7 and 30 days."
  }
}

variable "kms_key_rotation_enabled" {
  description = "Enable automatic annual rotation for the customer-managed KMS key."
  type        = bool
  default     = true
}

variable "raw_data_prefix" {
  description = "S3 prefix used for ingested raw event datasets."
  type        = string
  default     = "raw/events"
}

variable "processed_data_prefix" {
  description = "S3 prefix reserved for processed datasets."
  type        = string
  default     = "processed/events"
}

variable "analytics_data_prefix" {
  description = "S3 prefix used for Athena query outputs and analytics artifacts."
  type        = string
  default     = "analytics"

  validation {
    condition     = length(trim(var.analytics_data_prefix, "/")) > 0
    error_message = "Analytics prefix must not be empty."
  }
}

variable "glue_database_name" {
  description = "AWS Glue database name used to catalog event datasets."
  type        = string
  default     = "data_lake_events"

  validation {
    condition     = can(regex("^[a-z0-9_]{1,255}$", var.glue_database_name))
    error_message = "Glue database name must contain 1-255 lowercase letters, digits, or underscores."
  }
}

variable "glue_table_name" {
  description = "AWS Glue table name used for event analytics."
  type        = string
  default     = "events"

  validation {
    condition     = can(regex("^[a-z0-9_]{1,255}$", var.glue_table_name))
    error_message = "Glue table name must contain 1-255 lowercase letters, digits, or underscores."
  }
}

variable "athena_workgroup_name" {
  description = "Athena workgroup used for data lake queries."
  type        = string
  default     = "data-lake-analytics"
}

variable "athena_bytes_scanned_cutoff_per_query" {
  description = "Maximum bytes scanned by an Athena query before it is cancelled."
  type        = number
  default     = 10737418240

  validation {
    condition     = var.athena_bytes_scanned_cutoff_per_query > 0
    error_message = "Athena bytes-scanned cutoff must be greater than zero."
  }
}

variable "athena_engine_version" {
  description = "Athena engine version selected for the analytics workgroup."
  type        = string
  default     = "Athena engine version 3"
}

variable "lifecycle_transition_to_ia_days" {
  description = "Minimum object age in days before transitioning eligible raw data to Standard-IA."
  type        = number
  default     = 30

  validation {
    condition     = var.lifecycle_transition_to_ia_days >= 30
    error_message = "Standard-IA lifecycle transition must be configured for at least 30 days after object creation."
  }
}

variable "lifecycle_transition_to_glacier_days" {
  description = "Minimum object age in days before transitioning eligible raw data to Glacier Flexible Retrieval."
  type        = number
  default     = 90

  validation {
    condition = (
      var.lifecycle_transition_to_glacier_days >
      var.lifecycle_transition_to_ia_days
    )
    error_message = "Glacier transition must occur after the Standard-IA transition."
  }
}

variable "lifecycle_expiration_days" {
  description = "Object age in days before eligible current raw-data objects expire. Set to zero to disable expiration."
  type        = number
  default     = 365

  validation {
    condition     = var.lifecycle_expiration_days >= 0
    error_message = "Lifecycle expiration days cannot be negative."
  }
}

variable "noncurrent_version_expiration_days" {
  description = "Number of days before noncurrent object versions are permanently expired."
  type        = number
  default     = 90

  validation {
    condition     = var.noncurrent_version_expiration_days >= 0
    error_message = "Noncurrent version expiration days cannot be negative."
  }
}

variable "abort_incomplete_multipart_upload_days" {
  description = "Number of days after initiation before incomplete multipart uploads are aborted."
  type        = number
  default     = 7

  validation {
    condition     = var.abort_incomplete_multipart_upload_days >= 1
    error_message = "Incomplete multipart upload cleanup must be configured for at least one day."
  }
}

variable "enable_glue_catalog" {
  description = "Create the AWS Glue database and table for the event data lake."
  type        = bool
  default     = true
}

variable "enable_athena_workgroup" {
  description = "Create an Athena workgroup for querying the data lake."
  type        = bool
  default     = true
}

variable "enable_lifecycle_configuration" {
  description = "Apply S3 lifecycle rules to manage object transitions and retention."
  type        = bool
  default     = true
}

variable "enable_s3_bucket_keys" {
  description = "Use S3 Bucket Keys when SSE-KMS encryption is configured."
  type        = bool
  default     = true
}

variable "additional_tags" {
  description = "Additional tags applied to project infrastructure resources."
  type        = map(string)
  default     = {}
}