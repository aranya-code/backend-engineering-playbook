variable "source_bucket_id" {
  description = "Name of the existing source S3 bucket whose objects will be replicated."
  type        = string

  validation {
    condition     = length(trimspace(var.source_bucket_id)) > 0
    error_message = "source_bucket_id must not be empty."
  }
}

variable "source_bucket_arn" {
  description = "ARN of the source S3 bucket. Used in the replication role trust policy and source-bucket permissions."
  type        = string

  validation {
    condition     = can(regex("^arn:[^:]+:s3:::[^/]+$", var.source_bucket_arn))
    error_message = "source_bucket_arn must be a valid S3 bucket ARN without an object key."
  }
}

variable "source_account_id" {
  description = "12-digit AWS account ID that owns the source bucket. Restricts the S3 replication role trust policy."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.source_account_id))
    error_message = "source_account_id must contain exactly 12 digits."
  }
}

variable "destination_bucket_arn" {
  description = "ARN of the destination S3 bucket. The destination bucket must exist and have versioning enabled."
  type        = string

  validation {
    condition     = can(regex("^arn:[^:]+:s3:::[^/]+$", var.destination_bucket_arn))
    error_message = "destination_bucket_arn must be a valid S3 bucket ARN without an object key."
  }
}

variable "destination_account_id" {
  description = "Optional 12-digit AWS account ID that owns the destination bucket. Set this for cross-account replication."
  type        = string
  default     = null

  validation {
    condition = (
      var.destination_account_id == null ||
      can(regex("^[0-9]{12}$", var.destination_account_id))
    )
    error_message = "destination_account_id must contain exactly 12 digits when specified."
  }
}

variable "replication_role_name" {
  description = "Name of the IAM role assumed by Amazon S3 to perform replication."
  type        = string

  validation {
    condition = (
      length(var.replication_role_name) >= 1 &&
      length(var.replication_role_name) <= 64 &&
      can(regex("^[A-Za-z0-9_+=,.@-]+$", var.replication_role_name))
    )
    error_message = "replication_role_name must be 1-64 characters and contain only valid IAM role name characters."
  }
}

variable "replication_rule_id" {
  description = "Unique identifier for the S3 replication rule."
  type        = string
  default     = "replicate-source-objects"

  validation {
    condition = (
      length(var.replication_rule_id) >= 1 &&
      length(var.replication_rule_id) <= 255
    )
    error_message = "replication_rule_id must contain between 1 and 255 characters."
  }
}

variable "replication_rule_priority" {
  description = "Priority assigned to the replication rule. Required by S3 when rule filtering is configured."
  type        = number
  default     = 1

  validation {
    condition = (
      var.replication_rule_priority >= 0 &&
      floor(var.replication_rule_priority) == var.replication_rule_priority
    )
    error_message = "replication_rule_priority must be a non-negative integer."
  }
}

variable "replication_enabled" {
  description = "Whether the replication rule is enabled."
  type        = bool
  default     = true
}

variable "replication_filter_prefix" {
  description = "Optional object key prefix used to select objects for replication. An empty string selects all objects."
  type        = string
  default     = ""
}

variable "delete_marker_replication_enabled" {
  description = "Whether delete markers created by source-bucket delete operations are replicated. Delete marker replication is not supported with tag-based filters."
  type        = bool
  default     = false
}

variable "destination_storage_class" {
  description = "Storage class assigned to replicated objects in the destination bucket."
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
    error_message = "destination_storage_class must be a supported S3 replication destination storage class."
  }
}

variable "source_kms_key_arn" {
  description = "Optional ARN of the source AWS KMS key used to encrypt source objects. When configured, the replication rule selects SSE-KMS encrypted objects and the replication role requires kms:Decrypt permission."
  type        = string
  default     = null

  validation {
    condition = (
      var.source_kms_key_arn == null ||
      can(regex("^arn:[^:]+:kms:[^:]+:[0-9]{12}:key/.+$", var.source_kms_key_arn))
    )
    error_message = "source_kms_key_arn must be a valid AWS KMS key ARN when specified."
  }
}

variable "destination_kms_key_arn" {
  description = "Optional ARN of the destination AWS KMS key used to encrypt replicated objects. Required when replicating SSE-KMS encrypted source objects. The key policy must authorize the replication role."
  type        = string
  default     = null

  validation {
    condition = (
      var.destination_kms_key_arn == null ||
      can(regex("^arn:[^:]+:kms:[^:]+:[0-9]{12}:key/.+$", var.destination_kms_key_arn))
    )
    error_message = "destination_kms_key_arn must be a valid AWS KMS key ARN when specified."
  }
}

variable "metrics_enabled" {
  description = "Whether to enable S3 replication metrics for monitoring replication progress and failures."
  type        = bool
  default     = true
}

variable "replication_metrics_event_threshold_minutes" {
  description = "Replication metrics event threshold in minutes. S3 replication metrics use a 15-minute threshold."
  type        = number
  default     = 15

  validation {
    condition     = var.replication_metrics_event_threshold_minutes == 15
    error_message = "replication_metrics_event_threshold_minutes must be 15."
  }
}

variable "replication_time_control_enabled" {
  description = "Whether to enable S3 Replication Time Control (RTC), which provides a 15-minute replication time objective for eligible objects."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags applied to IAM resources created by this module."
  type        = map(string)
  default     = {}
}
